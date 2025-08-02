# -*- coding: utf-8 -*-
# Copyright (c) 2024, ERPNext Column Management Team and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import json
import time
from frappe import _

class CacheService:
    """Service for handling caching operations"""
    
    def __init__(self):
        self.default_expire = 300  # 5 minutes default
        self.cache_prefix = "column_mgmt"
    
    def get(self, key):
        """
        Get value from cache
        
        Args:
            key: Cache key
        
        Returns:
            Cached value or None if not found/expired
        """
        try:
            cache_key = self._build_cache_key(key)
            cached_data = frappe.cache().get_value(cache_key)
            
            if cached_data:
                # Check if expired
                if isinstance(cached_data, dict) and 'expires_at' in cached_data:
                    if time.time() > cached_data['expires_at']:
                        self.delete(key)
                        return None
                    return cached_data.get('data')
                else:
                    return cached_data
            
            return None
            
        except Exception as e:
            frappe.log_error(f"Error getting cache value: {str(e)}")
            return None
    
    def set(self, key, value, expire=None):
        """
        Set value in cache
        
        Args:
            key: Cache key
            value: Value to cache
            expire: Expiration time in seconds
        """
        try:
            cache_key = self._build_cache_key(key)
            expire_time = expire or self.default_expire
            
            cached_data = {
                'data': value,
                'expires_at': time.time() + expire_time,
                'created_at': time.time()
            }
            
            frappe.cache().set_value(cache_key, cached_data)
            
        except Exception as e:
            frappe.log_error(f"Error setting cache value: {str(e)}")
    
    def delete(self, key):
        """
        Delete value from cache
        
        Args:
            key: Cache key
        """
        try:
            cache_key = self._build_cache_key(key)
            frappe.cache().delete_value(cache_key)
            
        except Exception as e:
            frappe.log_error(f"Error deleting cache value: {str(e)}")
    
    def delete_pattern(self, pattern):
        """
        Delete all keys matching pattern
        
        Args:
            pattern: Pattern to match (supports wildcards)
        """
        try:
            # Get all cache keys
            cache_keys = frappe.cache().get_keys(self._build_cache_key("*"))
            
            # Filter keys matching pattern
            import fnmatch
            pattern_key = self._build_cache_key(pattern)
            matching_keys = [key for key in cache_keys if fnmatch.fnmatch(key, pattern_key)]
            
            # Delete matching keys
            for key in matching_keys:
                frappe.cache().delete_value(key)
                
        except Exception as e:
            frappe.log_error(f"Error deleting cache pattern: {str(e)}")
    
    def exists(self, key):
        """
        Check if key exists in cache
        
        Args:
            key: Cache key
        
        Returns:
            bool: True if key exists and not expired
        """
        return self.get(key) is not None
    
    def get_or_set(self, key, callback, expire=None):
        """
        Get value from cache or set it using callback
        
        Args:
            key: Cache key
            callback: Function to call if cache miss
            expire: Expiration time in seconds
        
        Returns:
            Cached or computed value
        """
        try:
            # Try to get from cache
            cached_value = self.get(key)
            if cached_value is not None:
                return cached_value
            
            # Cache miss, compute value
            computed_value = callback()
            
            # Store in cache
            self.set(key, computed_value, expire)
            
            return computed_value
            
        except Exception as e:
            frappe.log_error(f"Error in get_or_set: {str(e)}")
            # Fallback to callback
            try:
                return callback()
            except:
                return None
    
    def clear_all(self):
        """Clear all cache entries for this service"""
        try:
            self.delete_pattern("*")
        except Exception as e:
            frappe.log_error(f"Error clearing all cache: {str(e)}")
    
    def get_stats(self):
        """
        Get cache statistics
        
        Returns:
            dict: Cache statistics
        """
        try:
            cache_keys = frappe.cache().get_keys(self._build_cache_key("*"))
            
            total_keys = len(cache_keys)
            expired_keys = 0
            total_size = 0
            
            current_time = time.time()
            
            for key in cache_keys:
                try:
                    cached_data = frappe.cache().get_value(key)
                    if cached_data:
                        if isinstance(cached_data, dict) and 'expires_at' in cached_data:
                            if current_time > cached_data['expires_at']:
                                expired_keys += 1
                        
                        # Estimate size
                        total_size += len(json.dumps(cached_data, default=str))
                except:
                    continue
            
            return {
                "total_keys": total_keys,
                "expired_keys": expired_keys,
                "active_keys": total_keys - expired_keys,
                "estimated_size_bytes": total_size,
                "estimated_size_mb": round(total_size / (1024 * 1024), 2)
            }
            
        except Exception as e:
            frappe.log_error(f"Error getting cache stats: {str(e)}")
            return {
                "total_keys": 0,
                "expired_keys": 0,
                "active_keys": 0,
                "estimated_size_bytes": 0,
                "estimated_size_mb": 0
            }
    
    def cleanup_expired(self):
        """Remove expired cache entries"""
        try:
            cache_keys = frappe.cache().get_keys(self._build_cache_key("*"))
            current_time = time.time()
            cleaned_count = 0
            
            for key in cache_keys:
                try:
                    cached_data = frappe.cache().get_value(key)
                    if cached_data and isinstance(cached_data, dict) and 'expires_at' in cached_data:
                        if current_time > cached_data['expires_at']:
                            frappe.cache().delete_value(key)
                            cleaned_count += 1
                except:
                    continue
            
            return {
                "success": True,
                "cleaned_count": cleaned_count,
                "message": _("Cleaned {0} expired cache entries").format(cleaned_count)
            }
            
        except Exception as e:
            frappe.log_error(f"Error cleaning expired cache: {str(e)}")
            return {
                "success": False,
                "cleaned_count": 0,
                "message": str(e)
            }
    
    def _build_cache_key(self, key):
        """Build full cache key with prefix"""
        return f"{self.cache_prefix}:{key}"

# Global cache service instance
_cache_service = None

def get_cache_service():
    """Get global cache service instance"""
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service