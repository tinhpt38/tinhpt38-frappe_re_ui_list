# -*- coding: utf-8 -*-
# Copyright (c) 2024, ERPNext Column Management Team and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import json
from frappe import _

class ColumnService:
	def __init__(self):
		# Use lazy import for CacheService to avoid import issues
		try:
			from column_management.column_management.services.cache_service import CacheService
			self.cache = CacheService()
		except ImportError:
			# Fallback to frappe cache if CacheService is not available
			self.cache = frappe.cache()
		
		self.cache_prefix = "column_management"
		self.cache_ttl = 3600  # 1 hour
	
	def get_user_column_config(self, doctype, user):
		"""Get column configuration for a user and doctype"""
		cache_key = f"{self.cache_prefix}:columns:{doctype}:{user}"
		
		# Try to get from cache first
		cached_config = self.cache.get(cache_key)
		if cached_config:
			return json.loads(cached_config)
		
		# Get from database
		config = self._fetch_user_column_config(doctype, user)
		
		# Cache the result
		self.cache.set(cache_key, json.dumps(config), expire=self.cache_ttl)
		
		return config
	
	def _fetch_user_column_config(self, doctype, user):
		"""Fetch column configuration from database"""
		# Get user's column configurations
		user_columns = frappe.get_all("Column Config",
			filters={
				"doctype_name": doctype,
				"user": user
			},
			fields=["fieldname", "label", "width", "pinned", "visible", "`order`"],
			order_by="`order` asc, fieldname asc"
		)
		
		# If no user config exists, create default configuration
		if not user_columns:
			user_columns = self._create_default_user_config(doctype, user)
		
		# Get available fields from DocType metadata
		available_fields = self._get_doctype_fields(doctype)
		
		# Merge user config with available fields
		config = {
			"doctype": doctype,
			"user": user,
			"columns": [],
			"available_fields": available_fields
		}
		
		# Create lookup for user columns
		user_column_map = {col["fieldname"]: col for col in user_columns}
		
		# Process each available field
		for field in available_fields:
			fieldname = field["fieldname"]
			user_col = user_column_map.get(fieldname, {})
			
			column_config = {
				"fieldname": fieldname,
				"label": user_col.get("label", field["label"]),
				"fieldtype": field["fieldtype"],
				"width": user_col.get("width", field.get("width", 100)),
				"pinned": user_col.get("pinned"),
				"visible": user_col.get("visible", field.get("in_list_view", 0)),
				"sortable": field.get("sortable", 1),
				"filterable": field.get("filterable", 1),
				"order": user_col.get("order", field.get("idx", 0))
			}
			
			config["columns"].append(column_config)
		
		# Sort by order
		config["columns"].sort(key=lambda x: x["order"])
		
		return config
	
	def save_user_column_config(self, doctype, user, config):
		"""Save column configuration for a user"""
		try:
			# Validate the configuration
			self.validate_column_config(doctype, config)
			
			# Get existing configurations
			existing_configs = frappe.get_all("Column Config",
				filters={
					"doctype_name": doctype,
					"user": user
				},
				fields=["name", "fieldname"]
			)
			
			existing_map = {conf["fieldname"]: conf["name"] for conf in existing_configs}
			
			# Process each column in the new configuration
			for column in config.get("columns", []):
				fieldname = column["fieldname"]
				
				column_data = {
					"doctype_name": doctype,
					"user": user,
					"fieldname": fieldname,
					"label": column.get("label", fieldname.replace("_", " ").title()),
					"width": column.get("width", 100),
					"pinned": column.get("pinned"),
					"visible": column.get("visible", 1),
					"order": column.get("order", 0)
				}
				
				if fieldname in existing_map:
					# Update existing configuration
					doc = frappe.get_doc("Column Config", existing_map[fieldname])
					for key, value in column_data.items():
						if key != "doctype_name":  # Don't update doctype field
							setattr(doc, key, value)
					doc.save(ignore_permissions=True)
				else:
					# Create new configuration
					doc = frappe.get_doc({
						"doctype": "Column Config",
						**column_data
					})
					doc.insert(ignore_permissions=True)
			
			# Clear cache
			self.clear_user_cache(doctype, user)
			
			return True
			
		except Exception as e:
			frappe.log_error(f"Error saving column config: {str(e)}")
			frappe.throw(_("Failed to save column configuration: {0}").format(str(e)))
	
	def get_default_columns(self, doctype):
		"""Get default column configuration from DocType metadata"""
		return self._get_doctype_fields(doctype)
	
	def _get_doctype_fields(self, doctype):
		"""Get fields from DocType metadata"""
		try:
			meta = frappe.get_meta(doctype)
			fields = []
			
			for field in meta.fields:
				# Skip certain field types
				if field.fieldtype in ["Section Break", "Column Break", "Tab Break", "HTML"]:
					continue
				
				# Skip hidden fields
				if field.hidden:
					continue
				
				field_config = {
					"fieldname": field.fieldname,
					"label": field.label or field.fieldname.replace("_", " ").title(),
					"fieldtype": field.fieldtype,
					"width": self._get_default_width(field.fieldtype),
					"in_list_view": field.in_list_view,
					"sortable": 1 if field.fieldtype not in ["Text", "Long Text", "HTML Editor"] else 0,
					"filterable": 1,
					"idx": field.idx
				}
				
				fields.append(field_config)
			
			# Add standard fields
			standard_fields = [
				{
					"fieldname": "name",
					"label": "ID",
					"fieldtype": "Data",
					"width": 140,
					"in_list_view": 1,
					"sortable": 1,
					"filterable": 1,
					"idx": 0
				},
				{
					"fieldname": "creation",
					"label": "Created On",
					"fieldtype": "Datetime",
					"width": 140,
					"in_list_view": 0,
					"sortable": 1,
					"filterable": 1,
					"idx": 9999
				},
				{
					"fieldname": "modified",
					"label": "Last Modified",
					"fieldtype": "Datetime",
					"width": 140,
					"in_list_view": 0,
					"sortable": 1,
					"filterable": 1,
					"idx": 10000
				}
			]
			
			fields.extend(standard_fields)
			
			# Sort by idx
			fields.sort(key=lambda x: x["idx"])
			
			return fields
			
		except Exception as e:
			frappe.log_error(f"Error getting DocType fields: {str(e)}")
			return []
	
	def _get_default_width(self, fieldtype):
		"""Get default width based on field type"""
		width_map = {
			"Data": 140,
			"Link": 140,
			"Select": 120,
			"Int": 100,
			"Float": 120,
			"Currency": 120,
			"Percent": 100,
			"Date": 100,
			"Datetime": 140,
			"Time": 100,
			"Check": 80,
			"Text": 200,
			"Small Text": 200,
			"Long Text": 300,
			"Text Editor": 300,
			"HTML Editor": 300
		}
		
		return width_map.get(fieldtype, 140)
	
	def _create_default_user_config(self, doctype, user):
		"""Create default column configuration for a user"""
		try:
			available_fields = self._get_doctype_fields(doctype)
			user_columns = []
			
			for field in available_fields:
				if field.get("in_list_view"):
					# Create column config for fields that are in list view by default
					doc = frappe.get_doc({
						"doctype": "Column Config",
						"doctype_name": doctype,
						"user": user,
						"fieldname": field["fieldname"],
						"label": field["label"],
						"width": field["width"],
						"visible": 1,
						"order": field["idx"]
					})
					doc.insert(ignore_permissions=True)
					
					user_columns.append({
						"fieldname": field["fieldname"],
						"label": field["label"],
						"width": field["width"],
						"pinned": None,
						"visible": 1,
						"order": field["idx"]
					})
			
			return user_columns
			
		except Exception as e:
			frappe.log_error(f"Error creating default user config: {str(e)}")
			return []
	
	def validate_column_config(self, doctype, config):
		"""Validate column configuration"""
		if not isinstance(config, dict):
			frappe.throw(_("Configuration must be a dictionary"))
		
		if "columns" not in config:
			frappe.throw(_("Configuration must contain 'columns' key"))
		
		if not isinstance(config["columns"], list):
			frappe.throw(_("Columns must be a list"))
		
		# Get available fields
		available_fields = self._get_doctype_fields(doctype)
		available_fieldnames = {field["fieldname"] for field in available_fields}
		
		for column in config["columns"]:
			if not isinstance(column, dict):
				frappe.throw(_("Each column must be a dictionary"))
			
			if "fieldname" not in column:
				frappe.throw(_("Column must have 'fieldname'"))
			
			fieldname = column["fieldname"]
			if fieldname not in available_fieldnames:
				frappe.throw(_("Field '{0}' does not exist in DocType '{1}'").format(fieldname, doctype))
			
			# Validate width
			width = column.get("width", 100)
			if not isinstance(width, int) or width < 50 or width > 1000:
				frappe.throw(_("Column width must be between 50 and 1000 pixels"))
			
			# Validate pinned
			pinned = column.get("pinned")
			if pinned and pinned not in ["left", "right"]:
				frappe.throw(_("Pinned position must be 'left' or 'right'"))
	
	def reset_user_column_config(self, doctype, user):
		"""Reset user column configuration to default"""
		try:
			# Delete existing configurations
			frappe.db.delete("Column Config", {
				"doctype_name": doctype,
				"user": user
			})
			
			# Clear cache
			self.clear_user_cache(doctype, user)
			
			# Return new default configuration
			return self.get_user_column_config(doctype, user)
			
		except Exception as e:
			frappe.log_error(f"Error resetting column config: {str(e)}")
			frappe.throw(_("Failed to reset column configuration: {0}").format(str(e)))
	
	def clear_user_cache(self, doctype, user):
		"""Clear cache for a specific user and doctype"""
		cache_key = f"{self.cache_prefix}:columns:{doctype}:{user}"
		self.cache.delete(cache_key)
	
	def clear_doctype_cache(self, doctype):
		"""Clear cache for all users of a doctype"""
		# This is a simplified approach - in production you might want to use cache tags
		cache_pattern = f"{self.cache_prefix}:columns:{doctype}:*"
		# Note: frappe.cache doesn't support pattern deletion, so we'll need to track keys
		# For now, we'll just clear the entire cache namespace
		pass
	
	def save_column_width(self, doctype, user, fieldname, width):
		"""Save column width for a specific field"""
		try:
			# Validate width
			if not isinstance(width, (int, float)) or width < 50 or width > 1000:
				frappe.throw(_("Column width must be between 50 and 1000 pixels"))
			
			# Get or create column config
			existing_config = frappe.db.get_value("Column Config", {
				"doctype_name": doctype,
				"user": user,
				"fieldname": fieldname
			}, "name")
			
			if existing_config:
				# Update existing configuration
				doc = frappe.get_doc("Column Config", existing_config)
				doc.width = int(width)
				doc.save(ignore_permissions=True)
			else:
				# Create new configuration with default values
				field_info = self._get_field_info(doctype, fieldname)
				doc = frappe.get_doc({
					"doctype": "Column Config",
					"doctype_name": doctype,
					"user": user,
					"fieldname": fieldname,
					"label": field_info.get("label", fieldname.replace("_", " ").title()),
					"width": int(width),
					"visible": field_info.get("in_list_view", 0),
					"order": field_info.get("idx", 0)
				})
				doc.insert(ignore_permissions=True)
			
			# Clear cache
			self.clear_user_cache(doctype, user)
			
			return True
			
		except Exception as e:
			frappe.log_error(f"Error saving column width: {str(e)}")
			frappe.throw(_("Failed to save column width: {0}").format(str(e)))
	
	def save_multiple_column_widths(self, doctype, user, width_data):
		"""Save multiple column widths at once"""
		try:
			# Validate input
			if not isinstance(width_data, dict):
				frappe.throw(_("Width data must be a dictionary"))
			
			# Process each field width
			for fieldname, width in width_data.items():
				self.save_column_width(doctype, user, fieldname, width)
			
			return True
			
		except Exception as e:
			frappe.log_error(f"Error saving multiple column widths: {str(e)}")
			frappe.throw(_("Failed to save column widths: {0}").format(str(e)))
	
	def get_column_width(self, doctype, user, fieldname):
		"""Get saved column width for a specific field"""
		try:
			# Try to get from user's column config
			width = frappe.db.get_value("Column Config", {
				"doctype_name": doctype,
				"user": user,
				"fieldname": fieldname
			}, "width")
			
			if width:
				return width
			
			# Fall back to default width calculation
			return self._calculate_default_width(doctype, fieldname)
			
		except Exception as e:
			frappe.log_error(f"Error getting column width: {str(e)}")
			return self._calculate_default_width(doctype, fieldname)
	
	def get_all_column_widths(self, doctype, user):
		"""Get all saved column widths for a user and doctype"""
		try:
			# Get saved widths from database
			saved_widths = frappe.get_all("Column Config",
				filters={
					"doctype_name": doctype,
					"user": user
				},
				fields=["fieldname", "width"],
				as_dict=True
			)
			
			# Convert to dictionary
			width_map = {item["fieldname"]: item["width"] for item in saved_widths}
			
			# Get all available fields and add default widths for missing ones
			available_fields = self._get_doctype_fields(doctype)
			for field in available_fields:
				fieldname = field["fieldname"]
				if fieldname not in width_map:
					width_map[fieldname] = self._calculate_default_width(doctype, fieldname)
			
			return width_map
			
		except Exception as e:
			frappe.log_error(f"Error getting all column widths: {str(e)}")
			return {}
	
	def restore_column_widths(self, doctype, user):
		"""Restore column widths when loading list views"""
		try:
			# Get user's column configuration
			config = self.get_user_column_config(doctype, user)
			
			# Extract width information
			width_data = {}
			for column in config.get("columns", []):
				fieldname = column.get("fieldname")
				width = column.get("width")
				if fieldname and width:
					width_data[fieldname] = width
			
			return width_data
			
		except Exception as e:
			frappe.log_error(f"Error restoring column widths: {str(e)}")
			return {}
	
	def _calculate_default_width(self, doctype, fieldname):
		"""Calculate default width for a new column"""
		try:
			# Get field information
			field_info = self._get_field_info(doctype, fieldname)
			
			if field_info:
				fieldtype = field_info.get("fieldtype", "Data")
				label = field_info.get("label", fieldname)
				
				# Calculate width based on field type and label length
				base_width = self._get_default_width(fieldtype)
				
				# Adjust based on label length
				label_width = len(label) * 8 + 40  # Approximate character width + padding
				
				# Use the larger of base width or label width, with limits
				calculated_width = max(base_width, label_width)
				calculated_width = min(calculated_width, 300)  # Max width
				calculated_width = max(calculated_width, 80)   # Min width
				
				return calculated_width
			
			# Default fallback
			return 140
			
		except Exception as e:
			frappe.log_error(f"Error calculating default width: {str(e)}")
			return 140
	
	def _get_field_info(self, doctype, fieldname):
		"""Get field information from DocType metadata"""
		try:
			# Handle standard fields
			if fieldname in ["name", "creation", "modified", "owner", "modified_by"]:
				standard_fields = {
					"name": {"label": "ID", "fieldtype": "Data", "in_list_view": 1, "idx": 0},
					"creation": {"label": "Created On", "fieldtype": "Datetime", "in_list_view": 0, "idx": 9999},
					"modified": {"label": "Last Modified", "fieldtype": "Datetime", "in_list_view": 0, "idx": 10000},
					"owner": {"label": "Created By", "fieldtype": "Link", "in_list_view": 0, "idx": 10001},
					"modified_by": {"label": "Modified By", "fieldtype": "Link", "in_list_view": 0, "idx": 10002}
				}
				return standard_fields.get(fieldname, {})
			
			# Get from DocType metadata
			meta = frappe.get_meta(doctype)
			for field in meta.fields:
				if field.fieldname == fieldname:
					return {
						"label": field.label or fieldname.replace("_", " ").title(),
						"fieldtype": field.fieldtype,
						"in_list_view": field.in_list_view,
						"idx": field.idx
					}
			
			return {}
			
		except Exception as e:
			frappe.log_error(f"Error getting field info: {str(e)}")
			return {}
	
	def update_width_preferences(self, doctype, user, width_preferences):
		"""Update width preferences in user column preference"""
		try:
			from column_management.column_management.doctype.user_column_preference.user_column_preference import UserColumnPreference
			
			# Get or create user preference
			existing_pref = UserColumnPreference.get_user_preference(user, doctype)
			
			# Update width preferences
			if not existing_pref:
				existing_pref = {}
			
			existing_pref["column_widths"] = width_preferences
			
			# Save updated preferences
			UserColumnPreference.create_or_update_preference(user, doctype, existing_pref)
			
			return True
			
		except Exception as e:
			frappe.log_error(f"Error updating width preferences: {str(e)}")
			return False
	
	def get_width_preferences(self, doctype, user):
		"""Get width preferences from user column preference"""
		try:
			from column_management.column_management.doctype.user_column_preference.user_column_preference import UserColumnPreference
			
			# Get user preferences
			preferences = UserColumnPreference.get_user_preference(user, doctype)
			
			# Return width preferences or empty dict
			return preferences.get("column_widths", {})
			
		except Exception as e:
			frappe.log_error(f"Error getting width preferences: {str(e)}")
			return {}

	def get_column_statistics(self, doctype):
		"""Get statistics about column usage"""
		try:
			stats = frappe.db.sql("""
				SELECT 
					fieldname,
					COUNT(*) as user_count,
					AVG(width) as avg_width,
					SUM(CASE WHEN visible = 1 THEN 1 ELSE 0 END) as visible_count,
					SUM(CASE WHEN pinned IS NOT NULL THEN 1 ELSE 0 END) as pinned_count
				FROM `tabColumn Config`
				WHERE doctype_name = %s
				GROUP BY fieldname
				ORDER BY user_count DESC
			""", (doctype,), as_dict=True)
			
			return stats
			
		except Exception as e:
			frappe.log_error(f"Error getting column statistics: {str(e)}")
			return []