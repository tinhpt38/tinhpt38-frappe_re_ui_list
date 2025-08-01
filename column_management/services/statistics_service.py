# -*- coding: utf-8 -*-
# Copyright (c) 2024, ERPNext Column Management Team and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import json
import hashlib
from frappe import _

class StatisticsService:
	def __init__(self):
		self.cache = frappe.cache()
		self.cache_prefix = "column_management_stats"
		self.cache_ttl = 1800  # 30 minutes
	
	def calculate_statistics(self, doctype, data=None, config=None):
		"""Calculate statistics for a DocType with optional data and config"""
		try:
			# If no config provided, get from database
			if not config:
				config = self._get_statistics_config(doctype)
			
			if not config:
				return {}
			
			# If data is provided, calculate from data
			if data:
				return self._calculate_from_data(data, config)
			
			# Otherwise, calculate from database
			return self._calculate_from_database(doctype, config)
			
		except Exception as e:
			frappe.log_error(f"Error calculating statistics: {str(e)}")
			return {}
	
	def get_cached_statistics(self, doctype, filters_hash=None):
		"""Get statistics from cache"""
		cache_key = self._get_cache_key(doctype, filters_hash)
		
		cached_stats = self.cache.get(cache_key)
		if cached_stats:
			return json.loads(cached_stats)
		
		return None
	
	def _get_cache_key(self, doctype, filters_hash=None):
		"""Generate cache key for statistics"""
		if filters_hash:
			return f"{self.cache_prefix}:stats:{doctype}:{filters_hash}"
		else:
			return f"{self.cache_prefix}:stats:{doctype}:all"
	
	def _get_statistics_config(self, doctype):
		"""Get statistics configuration for a DocType"""
		try:
			configs = frappe.get_all("Statistics Config",
				filters={
					"doctype_name": doctype,
					"is_active": 1
				},
				fields=["name", "statistic_name", "field_name", "calculation_type", "format_string", "condition"],
				order_by="statistic_name asc"
			)
			
			return configs
			
		except Exception as e:
			frappe.log_error(f"Error getting statistics config: {str(e)}")
			return []
	
	def _calculate_from_data(self, data, config):
		"""Calculate statistics from provided data"""
		results = {}
		
		for stat_config in config:
			try:
				stat_name = stat_config["statistic_name"]
				field_name = stat_config["field_name"]
				calc_type = stat_config["calculation_type"]
				format_string = stat_config.get("format_string", "Data")
				
				# Extract field values from data
				values = []
				for row in data:
					if field_name in row and row[field_name] is not None:
						values.append(row[field_name])
				
				# Calculate based on type
				if calc_type == "Count":
					value = len(data)
				elif calc_type == "Sum":
					value = sum(float(v) for v in values if self._is_numeric(v))
				elif calc_type == "Average":
					numeric_values = [float(v) for v in values if self._is_numeric(v)]
					value = sum(numeric_values) / len(numeric_values) if numeric_values else 0
				elif calc_type == "Min":
					numeric_values = [float(v) for v in values if self._is_numeric(v)]
					value = min(numeric_values) if numeric_values else 0
				elif calc_type == "Max":
					numeric_values = [float(v) for v in values if self._is_numeric(v)]
					value = max(numeric_values) if numeric_values else 0
				else:
					value = 0
				
				# Format the value
				formatted_value = self._format_value(value, format_string)
				
				results[stat_name] = {
					"value": value,
					"formatted_value": formatted_value,
					"field_name": field_name,
					"calculation_type": calc_type
				}
				
			except Exception as e:
				frappe.log_error(f"Error calculating statistic {stat_config.get('statistic_name')}: {str(e)}")
				continue
		
		return results
	
	def _calculate_from_database(self, doctype, config, additional_conditions=None):
		"""Calculate statistics from database"""
		results = {}
		
		for stat_config in config:
			try:
				# Get the Statistics Config document for SQL building
				stat_doc = frappe.get_doc("Statistics Config", stat_config["name"])
				
				# Calculate the statistic
				value = stat_doc.calculate_statistic(additional_conditions)
				formatted_value = stat_doc.format_value(value)
				
				results[stat_config["statistic_name"]] = {
					"value": value,
					"formatted_value": formatted_value,
					"field_name": stat_config["field_name"],
					"calculation_type": stat_config["calculation_type"]
				}
				
			except Exception as e:
				frappe.log_error(f"Error calculating statistic {stat_config.get('statistic_name')}: {str(e)}")
				continue
		
		return results
	
	def calculate_filtered_statistics(self, doctype, filters):
		"""Calculate statistics with filters applied"""
		try:
			# Generate filters hash for caching
			filters_hash = self._generate_filters_hash(filters)
			
			# Try to get from cache first
			cached_stats = self.get_cached_statistics(doctype, filters_hash)
			if cached_stats:
				return cached_stats
			
			# Convert filters to SQL conditions
			sql_conditions = self._convert_filters_to_sql(filters)
			
			# Get statistics config
			config = self._get_statistics_config(doctype)
			
			# Calculate statistics with additional conditions
			results = self._calculate_from_database(doctype, config, sql_conditions)
			
			# Cache the results
			cache_key = self._get_cache_key(doctype, filters_hash)
			self.cache.set(cache_key, json.dumps(results), expire=self.cache_ttl)
			
			return results
			
		except Exception as e:
			frappe.log_error(f"Error calculating filtered statistics: {str(e)}")
			return {}
	
	def _convert_filters_to_sql(self, filters):
		"""Convert filter conditions to SQL WHERE clauses"""
		if not filters:
			return []
		
		sql_conditions = []
		
		for filter_item in filters:
			try:
				fieldname = filter_item.get("fieldname")
				operator = filter_item.get("operator")
				value = filter_item.get("value")
				
				if not fieldname or not operator:
					continue
				
				# Escape field name
				escaped_field = f"`{fieldname}`"
				
				# Build condition based on operator
				if operator == "=":
					condition = f"{escaped_field} = {frappe.db.escape(value)}"
				elif operator == "!=":
					condition = f"{escaped_field} != {frappe.db.escape(value)}"
				elif operator == ">":
					condition = f"{escaped_field} > {frappe.db.escape(value)}"
				elif operator == "<":
					condition = f"{escaped_field} < {frappe.db.escape(value)}"
				elif operator == ">=":
					condition = f"{escaped_field} >= {frappe.db.escape(value)}"
				elif operator == "<=":
					condition = f"{escaped_field} <= {frappe.db.escape(value)}"
				elif operator == "like":
					condition = f"{escaped_field} LIKE {frappe.db.escape(f'%{value}%')}"
				elif operator == "not like":
					condition = f"{escaped_field} NOT LIKE {frappe.db.escape(f'%{value}%')}"
				elif operator == "in":
					if isinstance(value, list):
						escaped_values = [frappe.db.escape(v) for v in value]
						condition = f"{escaped_field} IN ({','.join(escaped_values)})"
					else:
						condition = f"{escaped_field} = {frappe.db.escape(value)}"
				elif operator == "not in":
					if isinstance(value, list):
						escaped_values = [frappe.db.escape(v) for v in value]
						condition = f"{escaped_field} NOT IN ({','.join(escaped_values)})"
					else:
						condition = f"{escaped_field} != {frappe.db.escape(value)}"
				elif operator == "between":
					if isinstance(value, list) and len(value) == 2:
						condition = f"{escaped_field} BETWEEN {frappe.db.escape(value[0])} AND {frappe.db.escape(value[1])}"
					else:
						continue
				else:
					continue
				
				sql_conditions.append(condition)
				
			except Exception as e:
				frappe.log_error(f"Error converting filter to SQL: {str(e)}")
				continue
		
		return sql_conditions
	
	def _generate_filters_hash(self, filters):
		"""Generate hash for filters to use as cache key"""
		if not filters:
			return "no_filters"
		
		# Sort filters for consistent hashing
		sorted_filters = sorted(filters, key=lambda x: x.get("fieldname", ""))
		filters_str = json.dumps(sorted_filters, sort_keys=True)
		
		return hashlib.md5(filters_str.encode()).hexdigest()
	
	def _is_numeric(self, value):
		"""Check if a value is numeric"""
		try:
			float(value)
			return True
		except (ValueError, TypeError):
			return False
	
	def _format_value(self, value, format_string):
		"""Format value according to format string"""
		if value is None:
			return "0"
		
		try:
			if format_string == "Int":
				return str(int(value))
			elif format_string == "Float":
				return f"{float(value):.2f}"
			elif format_string == "Currency":
				return frappe.utils.fmt_money(value)
			elif format_string == "Percent":
				return f"{float(value):.2f}%"
			elif format_string == "Date":
				return frappe.utils.formatdate(value)
			elif format_string == "Datetime":
				return frappe.utils.format_datetime(value)
			else:
				return str(value)
		
		except:
			return str(value)
	
	def invalidate_statistics_cache(self, doctype):
		"""Invalidate all cached statistics for a DocType"""
		try:
			# Clear all cache keys for this doctype
			# Note: This is a simplified approach - in production you might want to use cache tags
			cache_pattern = f"{self.cache_prefix}:stats:{doctype}:*"
			
			# Since frappe.cache doesn't support pattern deletion, we'll clear specific known keys
			# Clear the "all" statistics
			all_cache_key = f"{self.cache_prefix}:stats:{doctype}:all"
			self.cache.delete(all_cache_key)
			
			# For filtered statistics, we would need to track the filter hashes
			# This is a limitation of the current caching approach
			
		except Exception as e:
			frappe.log_error(f"Error invalidating statistics cache: {str(e)}")
	
	def get_statistics_summary(self, doctype):
		"""Get a summary of available statistics for a DocType"""
		try:
			configs = self._get_statistics_config(doctype)
			
			summary = {
				"doctype": doctype,
				"total_statistics": len(configs),
				"statistics": []
			}
			
			for config in configs:
				stat_info = {
					"name": config["statistic_name"],
					"field": config["field_name"],
					"type": config["calculation_type"],
					"format": config.get("format_string", "Data")
				}
				summary["statistics"].append(stat_info)
			
			return summary
			
		except Exception as e:
			frappe.log_error(f"Error getting statistics summary: {str(e)}")
			return {"doctype": doctype, "total_statistics": 0, "statistics": []}
	
	def calculate_drill_down_statistics(self, doctype, statistic_name, drill_down_field, filters=None):
		"""Calculate drill-down statistics grouped by a specific field"""
		try:
			# Get the statistics configuration
			stat_config = frappe.get_value("Statistics Config", {
				"doctype_name": doctype,
				"statistic_name": statistic_name,
				"is_active": 1
			}, ["name", "field_name", "calculation_type", "format_string", "condition"], as_dict=True)
			
			if not stat_config:
				return {}
			
			# Build SQL query for drill-down
			table_name = f"tab{doctype}"
			field_name = stat_config["field_name"]
			calc_type = stat_config["calculation_type"]
			
			# Build SELECT clause
			if calc_type == "Count":
				select_clause = f"COUNT(*) as value"
			else:
				sql_function = {
					"Sum": "SUM",
					"Average": "AVG",
					"Min": "MIN",
					"Max": "MAX"
				}.get(calc_type, "COUNT")
				select_clause = f"{sql_function}(`{field_name}`) as value"
			
			# Build WHERE clause
			where_conditions = ["docstatus != 2"]
			
			if stat_config.get("condition"):
				where_conditions.append(stat_config["condition"])
			
			if filters:
				sql_conditions = self._convert_filters_to_sql(filters)
				where_conditions.extend(sql_conditions)
			
			where_clause = " AND ".join(where_conditions)
			
			# Build complete query
			query = f"""
				SELECT 
					`{drill_down_field}` as group_by_field,
					{select_clause}
				FROM `{table_name}` 
				WHERE {where_clause}
				GROUP BY `{drill_down_field}`
				ORDER BY value DESC
				LIMIT 20
			"""
			
			# Execute query
			results = frappe.db.sql(query, as_dict=True)
			
			# Format results
			drill_down_data = {}
			for row in results:
				group_value = row["group_by_field"] or "Not Set"
				value = row["value"] or 0
				formatted_value = self._format_value(value, stat_config.get("format_string", "Data"))
				
				drill_down_data[group_value] = {
					"value": value,
					"formatted_value": formatted_value
				}
			
			return drill_down_data
			
		except Exception as e:
			frappe.log_error(f"Error calculating drill-down statistics: {str(e)}")
			return {}
	
	def get_real_time_statistics(self, doctype, filters=None, refresh_cache=False):
		"""Get real-time statistics with optional cache refresh"""
		try:
			if refresh_cache:
				# Clear cache first
				if filters:
					filters_hash = self._generate_filters_hash(filters)
					cache_key = self._get_cache_key(doctype, filters_hash)
					self.cache.delete(cache_key)
				else:
					self.invalidate_statistics_cache(doctype)
			
			# Calculate statistics
			if filters:
				return self.calculate_filtered_statistics(doctype, filters)
			else:
				# Try cache first
				cached_stats = self.get_cached_statistics(doctype)
				if cached_stats:
					return cached_stats
				
				# Calculate and cache
				config = self._get_statistics_config(doctype)
				results = self._calculate_from_database(doctype, config)
				
				cache_key = self._get_cache_key(doctype)
				self.cache.set(cache_key, json.dumps(results), expire=self.cache_ttl)
				
				return results
			
		except Exception as e:
			frappe.log_error(f"Error getting real-time statistics: {str(e)}")
			return {}