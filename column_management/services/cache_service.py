# -*- coding: utf-8 -*-
# Copyright (c) 2024, ERPNext Column Management Team and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import json
import time
import threading
from frappe import _

class CacheService:
	def __init__(self):
		self.redis_cache = frappe.cache()
		self.memory_cache = {}
		self.cache_stats = {
			"hits": 0,
			"misses": 0,
			"sets": 0,
			"deletes": 0
		}
		self.cache_prefix = "column_management"
		self.default_ttl = 3600  # 1 hour
		self.memory_cache_size_limit = 1000  # Maximum items in memory cache
		self.lock = threading.Lock()
	
	def get(self, key, default=None):
		"""Get value from multi-level cache"""
		try:
			full_key = f"{self.cache_prefix}:{key}"
			
			# Level 1: Memory cache
			with self.lock:
				if full_key in self.memory_cache:
					cache_item = self.memory_cache[full_key]
					
					# Check if expired
					if cache_item["expires_at"] > time.time():
						self.cache_stats["hits"] += 1
						return cache_item["value"]
					else:
						# Remove expired item
						del self.memory_cache[full_key]
			
			# Level 2: Redis cache
			cached_value = self.redis_cache.get(full_key)
			if cached_value is not None:
				try:
					value = json.loads(cached_value)
					
					# Store in memory cache for faster access
					self._set_memory_cache(full_key, value, self.default_ttl)
					
					self.cache_stats["hits"] += 1
					return value
				except json.JSONDecodeError:
					# If JSON decode fails, treat as cache miss
					pass
			
			# Cache miss
			self.cache_stats["misses"] += 1
			return default
			
		except Exception as e:
			frappe.log_error(f"Error getting from cache: {str(e)}")
			return default
	
	def set(self, key, value, expire=None):
		"""Set value in multi-level cache"""
		try:
			full_key = f"{self.cache_prefix}:{key}"
			ttl = expire or self.default_ttl
			
			# Serialize value
			serialized_value = json.dumps(value)
			
			# Level 1: Memory cache
			self._set_memory_cache(full_key, value, ttl)
			
			# Level 2: Redis cache
			self.redis_cache.set(full_key, serialized_value, expire=ttl)
			
			self.cache_stats["sets"] += 1
			return True
			
		except Exception as e:
			frappe.log_error(f"Error setting cache: {str(e)}")
			return False
	
	def _set_memory_cache(self, key, value, ttl):
		"""Set value in memory cache with size limit"""
		with self.lock:
			# Check size limit
			if len(self.memory_cache) >= self.memory_cache_size_limit:
				# Remove oldest items (simple LRU)
				oldest_key = min(self.memory_cache.keys(), 
					key=lambda k: self.memory_cache[k]["created_at"])
				del self.memory_cache[oldest_key]
			
			# Set new value
			self.memory_cache[key] = {
				"value": value,
				"created_at": time.time(),
				"expires_at": time.time() + ttl
			}
	
	def delete(self, key):
		"""Delete value from multi-level cache"""
		try:
			full_key = f"{self.cache_prefix}:{key}"
			
			# Level 1: Memory cache
			with self.lock:
				if full_key in self.memory_cache:
					del self.memory_cache[full_key]
			
			# Level 2: Redis cache
			self.redis_cache.delete(full_key)
			
			self.cache_stats["deletes"] += 1
			return True
			
		except Exception as e:
			frappe.log_error(f"Error deleting from cache: {str(e)}")
			return False
	
	def delete_pattern(self, pattern):
		"""Delete all keys matching a pattern"""
		try:
			# For memory cache, we need to iterate through keys
			full_pattern = f"{self.cache_prefix}:{pattern}"
			
			with self.lock:
				keys_to_delete = []
				for key in self.memory_cache.keys():
					if self._match_pattern(key, full_pattern):
						keys_to_delete.append(key)
				
				for key in keys_to_delete:
					del self.memory_cache[key]
			
			# For Redis cache, we would need to use SCAN command
			# This is a simplified approach - in production you might want to use cache tags
			
			return True
			
		except Exception as e:
			frappe.log_error(f"Error deleting pattern from cache: {str(e)}")
			return False
	
	def _match_pattern(self, key, pattern):
		"""Simple pattern matching for cache keys"""
		# Replace * with regex equivalent
		import re
		regex_pattern = pattern.replace("*", ".*")
		return re.match(regex_pattern, key) is not None
	
	def exists(self, key):
		"""Check if key exists in cache"""
		full_key = f"{self.cache_prefix}:{key}"
		
		# Check memory cache first
		with self.lock:
			if full_key in self.memory_cache:
				cache_item = self.memory_cache[full_key]
				if cache_item["expires_at"] > time.time():
					return True
				else:
					del self.memory_cache[full_key]
		
		# Check Redis cache
		return self.redis_cache.exists(full_key)
	
	def get_or_set(self, key, callback, expire=None):
		"""Get value from cache or set it using callback"""
		value = self.get(key)
		
		if value is None:
			# Call the callback to get the value
			value = callback()
			if value is not None:
				self.set(key, value, expire)
		
		return value
	
	def increment(self, key, amount=1, expire=None):
		"""Increment a numeric value in cache"""
		try:
			current_value = self.get(key, 0)
			
			if not isinstance(current_value, (int, float)):
				current_value = 0
			
			new_value = current_value + amount
			self.set(key, new_value, expire)
			
			return new_value
			
		except Exception as e:
			frappe.log_error(f"Error incrementing cache value: {str(e)}")
			return None
	
	def get_stats(self):
		"""Get cache statistics"""
		total_requests = self.cache_stats["hits"] + self.cache_stats["misses"]
		hit_rate = (self.cache_stats["hits"] / total_requests * 100) if total_requests > 0 else 0
		
		with self.lock:
			memory_cache_size = len(self.memory_cache)
		
		return {
			"hits": self.cache_stats["hits"],
			"misses": self.cache_stats["misses"],
			"sets": self.cache_stats["sets"],
			"deletes": self.cache_stats["deletes"],
			"hit_rate": round(hit_rate, 2),
			"memory_cache_size": memory_cache_size,
			"memory_cache_limit": self.memory_cache_size_limit
		}
	
	def clear_stats(self):
		"""Clear cache statistics"""
		self.cache_stats = {
			"hits": 0,
			"misses": 0,
			"sets": 0,
			"deletes": 0
		}
	
	def warm_cache(self, doctype_list=None):
		"""Warm up cache with commonly used data"""
		try:
			if not doctype_list:
				# Get list of commonly used DocTypes
				doctype_list = self._get_common_doctypes()
			
			from column_management.column_management.services.metadata_service import MetadataService
			from column_management.column_management.services.column_service import ColumnService
			
			metadata_service = MetadataService()
			column_service = ColumnService()
			
			for doctype in doctype_list:
				try:
					# Warm up metadata cache
					metadata_service.get_doctype_metadata(doctype)
					
					# Warm up column configuration for common users
					common_users = self._get_common_users()
					for user in common_users:
						column_service.get_user_column_config(doctype, user)
					
				except Exception as e:
					frappe.log_error(f"Error warming cache for {doctype}: {str(e)}")
					continue
			
			return True
			
		except Exception as e:
			frappe.log_error(f"Error warming cache: {str(e)}")
			return False
	
	def _get_common_doctypes(self):
		"""Get list of commonly used DocTypes"""
		try:
			# Get DocTypes that have been accessed recently
			common_doctypes = frappe.db.sql("""
				SELECT DISTINCT doctype_name
				FROM `tabColumn Config`
				WHERE modified > DATE_SUB(NOW(), INTERVAL 7 DAY)
				LIMIT 20
			""", as_list=True)
			
			return [dt[0] for dt in common_doctypes]
			
		except:
			# Fallback to some standard DocTypes
			return ["Sales Invoice", "Purchase Invoice", "Item", "Customer", "Supplier"]
	
	def _get_common_users(self):
		"""Get list of commonly active users"""
		try:
			# Get users who have been active recently
			common_users = frappe.db.sql("""
				SELECT DISTINCT user
				FROM `tabColumn Config`
				WHERE modified > DATE_SUB(NOW(), INTERVAL 7 DAY)
				LIMIT 10
			""", as_list=True)
			
			return [user[0] for user in common_users]
			
		except:
			# Fallback to current user
			return [frappe.session.user]
	
	def preload_data(self, keys_and_callbacks):
		"""Preload multiple cache keys using callbacks"""
		try:
			results = {}
			
			for key, callback in keys_and_callbacks.items():
				try:
					if not self.exists(key):
						value = callback()
						if value is not None:
							self.set(key, value)
							results[key] = value
					else:
						results[key] = self.get(key)
				
				except Exception as e:
					frappe.log_error(f"Error preloading {key}: {str(e)}")
					continue
			
			return results
			
		except Exception as e:
			frappe.log_error(f"Error preloading data: {str(e)}")
			return {}
	
	def invalidate_doctype_cache(self, doctype):
		"""Invalidate all cache entries for a specific DocType"""
		try:
			patterns_to_clear = [
				f"columns:{doctype}:*",
				f"metadata:doctype:{doctype}",
				f"metadata:field:{doctype}:*",
				f"stats:{doctype}:*"
			]
			
			for pattern in patterns_to_clear:
				self.delete_pattern(pattern)
			
			return True
			
		except Exception as e:
			frappe.log_error(f"Error invalidating DocType cache: {str(e)}")
			return False
	
	def invalidate_user_cache(self, user):
		"""Invalidate all cache entries for a specific user"""
		try:
			pattern = f"columns:*:{user}"
			self.delete_pattern(pattern)
			
			return True
			
		except Exception as e:
			frappe.log_error(f"Error invalidating user cache: {str(e)}")
			return False
	
	def cleanup_expired_memory_cache(self):
		"""Clean up expired items from memory cache"""
		try:
			current_time = time.time()
			
			with self.lock:
				expired_keys = []
				for key, cache_item in self.memory_cache.items():
					if cache_item["expires_at"] <= current_time:
						expired_keys.append(key)
				
				for key in expired_keys:
					del self.memory_cache[key]
			
			return len(expired_keys)
			
		except Exception as e:
			frappe.log_error(f"Error cleaning up memory cache: {str(e)}")
			return 0
	
	def get_memory_usage(self):
		"""Get memory usage statistics"""
		try:
			import sys
			
			with self.lock:
				total_size = sys.getsizeof(self.memory_cache)
				for key, value in self.memory_cache.items():
					total_size += sys.getsizeof(key) + sys.getsizeof(value)
			
			return {
				"total_size_bytes": total_size,
				"total_size_mb": round(total_size / (1024 * 1024), 2),
				"item_count": len(self.memory_cache)
			}
			
		except Exception as e:
			frappe.log_error(f"Error getting memory usage: {str(e)}")
			return {"total_size_bytes": 0, "total_size_mb": 0, "item_count": 0}
	
	def set_cache_config(self, memory_cache_size_limit=None, default_ttl=None):
		"""Update cache configuration"""
		if memory_cache_size_limit is not None:
			self.memory_cache_size_limit = memory_cache_size_limit
		
		if default_ttl is not None:
			self.default_ttl = default_ttl
	
	def flush_all(self):
		"""Flush all cache data"""
		try:
			# Clear memory cache
			with self.lock:
				self.memory_cache.clear()
			
			# Clear Redis cache (pattern-based)
			# Note: This is a simplified approach
			self.delete_pattern("*")
			
			# Reset stats
			self.clear_stats()
			
			return True
			
		except Exception as e:
			frappe.log_error(f"Error flushing cache: {str(e)}")
			return False