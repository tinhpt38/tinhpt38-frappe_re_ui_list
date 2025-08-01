# -*- coding: utf-8 -*-
# Copyright (c) 2024, ERPNext Column Management Team and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import re
from frappe.model.document import Document
from frappe import _

class StatisticsConfig(Document):
	def validate(self):
		"""Validate statistics configuration data"""
		self.validate_doctype_exists()
		self.validate_field_exists()
		self.validate_calculation_type()
		self.validate_condition()
		self.validate_unique_config()
		self.set_timestamps()
	
	def validate_doctype_exists(self):
		"""Validate that the DocType exists"""
		if not frappe.db.exists("DocType", self.doctype_name):
			frappe.throw(_("DocType {0} does not exist").format(self.doctype_name))
	
	def validate_field_exists(self):
		"""Validate that the field exists in the DocType"""
		if self.doctype_name and self.field_name:
			# Get DocType meta
			meta = frappe.get_meta(self.doctype_name)
			
			# Check if field exists
			if not meta.get_field(self.field_name):
				frappe.throw(_("Field {0} does not exist in DocType {1}").format(
					self.field_name, self.doctype_name))
	
	def validate_calculation_type(self):
		"""Validate calculation type against field type"""
		if self.doctype_name and self.field_name and self.calculation_type:
			meta = frappe.get_meta(self.doctype_name)
			field = meta.get_field(self.field_name)
			
			if field:
				numeric_types = ['Int', 'Float', 'Currency', 'Percent']
				
				# Count can be used on any field
				if self.calculation_type == 'Count':
					return
				
				# Sum, Average, Min, Max require numeric fields
				if self.calculation_type in ['Sum', 'Average', 'Min', 'Max']:
					if field.fieldtype not in numeric_types:
						frappe.throw(_("Calculation type {0} can only be used with numeric fields").format(
							self.calculation_type))
	
	def validate_condition(self):
		"""Validate SQL condition for security"""
		if self.condition:
			# Basic SQL injection prevention
			dangerous_keywords = [
				'DROP', 'DELETE', 'UPDATE', 'INSERT', 'CREATE', 'ALTER', 
				'TRUNCATE', 'EXEC', 'EXECUTE', 'UNION', 'SCRIPT'
			]
			
			condition_upper = self.condition.upper()
			for keyword in dangerous_keywords:
				if keyword in condition_upper:
					frappe.throw(_("Dangerous SQL keyword '{0}' not allowed in condition").format(keyword))
			
			# Validate basic SQL syntax
			if not re.match(r'^[a-zA-Z0-9_\s\.\=\!\<\>\(\)\'\"\,\-\+\*\/\%\&\|\^]+$', self.condition):
				frappe.throw(_("Invalid characters in condition. Only alphanumeric, operators, and basic SQL syntax allowed"))
	
	def validate_unique_config(self):
		"""Ensure unique configuration per doctype and statistic name"""
		existing = frappe.db.get_value("Statistics Config", {
			"doctype_name": self.doctype_name,
			"statistic_name": self.statistic_name,
			"name": ["!=", self.name]
		})
		
		if existing:
			frappe.throw(_("Statistics configuration already exists for {0} - {1}").format(
				self.doctype_name, self.statistic_name))
	
	def set_timestamps(self):
		"""Set created_at and modified_at timestamps"""
		now = frappe.utils.now()
		
		if self.is_new():
			self.created_at = now
		
		self.modified_at = now
	
	def after_insert(self):
		"""Actions after inserting the document"""
		self.clear_cache()
	
	def on_update(self):
		"""Actions after updating the document"""
		self.clear_cache()
	
	def on_trash(self):
		"""Actions before deleting the document"""
		self.clear_cache()
	
	def clear_cache(self):
		"""Clear related caches"""
		try:
			from column_management.column_management.services.statistics_service import StatisticsService
			service = StatisticsService()
			service.invalidate_statistics_cache(self.doctype_name)
		except ImportError:
			pass
	
	def get_sql_function(self):
		"""Get SQL function for calculation type"""
		functions = {
			'Count': 'COUNT',
			'Sum': 'SUM',
			'Average': 'AVG',
			'Min': 'MIN',
			'Max': 'MAX'
		}
		return functions.get(self.calculation_type, 'COUNT')
	
	def build_sql_query(self, additional_conditions=None):
		"""Build SQL query for statistics calculation"""
		sql_function = self.get_sql_function()
		table_name = f"tab{self.doctype_name}"
		
		# Build SELECT clause
		if self.calculation_type == 'Count':
			select_clause = f"{sql_function}(*)"
		else:
			select_clause = f"{sql_function}(`{self.field_name}`)"
		
		# Build WHERE clause
		where_conditions = ["docstatus != 2"]  # Exclude cancelled documents
		
		if self.condition:
			where_conditions.append(self.condition)
		
		if additional_conditions:
			where_conditions.extend(additional_conditions)
		
		where_clause = " AND ".join(where_conditions)
		
		query = f"SELECT {select_clause} as value FROM `{table_name}` WHERE {where_clause}"
		
		return query
	
	def calculate_statistic(self, additional_conditions=None):
		"""Calculate the statistic value"""
		try:
			query = self.build_sql_query(additional_conditions)
			result = frappe.db.sql(query, as_dict=True)
			
			if result and result[0]['value'] is not None:
				return result[0]['value']
			else:
				return 0
		
		except Exception as e:
			frappe.log_error(f"Error calculating statistic {self.name}: {str(e)}")
			return 0
	
	def format_value(self, value):
		"""Format the calculated value according to format_string"""
		if value is None:
			return "0"
		
		try:
			if self.format_string == 'Int':
				return str(int(value))
			elif self.format_string == 'Float':
				return f"{float(value):.2f}"
			elif self.format_string == 'Currency':
				return frappe.utils.fmt_money(value)
			elif self.format_string == 'Percent':
				return f"{float(value):.2f}%"
			elif self.format_string == 'Date':
				return frappe.utils.formatdate(value)
			elif self.format_string == 'Datetime':
				return frappe.utils.format_datetime(value)
			else:
				return str(value)
		
		except:
			return str(value)
	
	@staticmethod
	def get_doctype_statistics(doctype_name, active_only=True):
		"""Get all statistics configurations for a doctype"""
		filters = {"doctype_name": doctype_name}
		if active_only:
			filters["is_active"] = 1
		
		return frappe.get_all("Statistics Config",
			filters=filters,
			fields=["name", "statistic_name", "field_name", "calculation_type", "format_string", "condition"],
			order_by="statistic_name asc"
		)
	
	@staticmethod
	def create_default_config(doctype_name, statistic_name, field_name, calculation_type, format_string="Data", condition=None):
		"""Create default statistics configuration"""
		if not frappe.db.exists("Statistics Config", {
			"doctype_name": doctype_name,
			"statistic_name": statistic_name
		}):
			doc = frappe.get_doc({
				"doctype": "Statistics Config",
				"doctype_name": doctype_name,
				"statistic_name": statistic_name,
				"field_name": field_name,
				"calculation_type": calculation_type,
				"format_string": format_string,
				"condition": condition,
				"is_active": 1
			})
			doc.insert(ignore_permissions=True)
			return doc
		return None
	
	@staticmethod
	def calculate_all_statistics(doctype_name, additional_conditions=None):
		"""Calculate all active statistics for a doctype"""
		configs = StatisticsConfig.get_doctype_statistics(doctype_name, active_only=True)
		results = {}
		
		for config in configs:
			stat_doc = frappe.get_doc("Statistics Config", config.name)
			value = stat_doc.calculate_statistic(additional_conditions)
			formatted_value = stat_doc.format_value(value)
			
			results[config.statistic_name] = {
				"value": value,
				"formatted_value": formatted_value,
				"field_name": config.field_name,
				"calculation_type": config.calculation_type
			}
		
		return results