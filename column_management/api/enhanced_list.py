# -*- coding: utf-8 -*-
# Copyright (c) 2024, ERPNext Column Management Team and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import json
from frappe import _
from frappe.desk.reportview import get_filters_cond, get_match_cond
from column_management.column_management.services.column_service import ColumnService
from column_management.column_management.services.metadata_service import MetadataService

@frappe.whitelist()
def get_list_data(doctype, columns=None, filters=None, page=1, page_size=20, sort_by=None, sort_order="asc", user=None):
	"""Get list data with column management support - Enhanced for Task 9.2"""
	try:
		# Validate parameters
		if not doctype:
			frappe.throw(_("DocType is required"))
		
		# Use current user if not specified
		if not user:
			user = frappe.session.user
		
		# Check permissions
		if not frappe.has_permission(doctype, "read", user=user):
			frappe.throw(_("No permission to read {0}").format(doctype))
		
		# Parse parameters with enhanced validation
		page = max(1, int(page) if page else 1)
		page_size = int(page_size) if page_size else 20
		page_size = min(max(10, page_size), 200)  # Limit page size for performance (10-200)
		
		if isinstance(filters, str):
			filters = json.loads(filters) if filters else []
		
		if isinstance(columns, str):
			columns = json.loads(columns) if columns else None
		
		# Get column configuration
		column_service = ColumnService()
		if not columns:
			config = column_service.get_user_column_config(doctype, user)
			columns = [col for col in config.get("columns", []) if col.get("visible")]
		
		# Build field list
		fields = []
		for column in columns:
			fieldname = column.get("fieldname")
			if fieldname:
				fields.append(fieldname)
		
		# Ensure 'name' field is always included
		if "name" not in fields:
			fields.insert(0, "name")
		
		# Build filters
		filter_conditions = []
		if filters:
			filter_conditions = _build_filter_conditions(filters)
		
		# Build order by
		order_by = None
		if sort_by:
			sort_order = "desc" if sort_order.lower() == "desc" else "asc"
			order_by = f"{sort_by} {sort_order}"
		else:
			order_by = "modified desc"
		
		# Calculate offset
		start = (page - 1) * page_size
		
		# Get data
		data = frappe.get_all(
			doctype,
			fields=fields,
			filters=filter_conditions,
			order_by=order_by,
			start=start,
			page_length=page_size,
			as_list=False
		)
		
		# Get total count for pagination
		total_count = frappe.db.count(doctype, filters=filter_conditions)
		
		# Calculate pagination info
		total_pages = (total_count + page_size - 1) // page_size
		has_next = page < total_pages
		has_prev = page > 1
		
		# Format data according to column configuration
		formatted_data = _format_list_data(data, columns, doctype)
		
		return {
			"success": True,
			"data": {
				"records": formatted_data,
				"pagination": {
					"current_page": page,
					"page_size": page_size,
					"total_count": total_count,
					"total_pages": total_pages,
					"has_next": has_next,
					"has_prev": has_prev
				},
				"columns": columns,
				"doctype": doctype
			},
			"message": _("List data retrieved successfully")
		}
		
	except Exception as e:
		frappe.log_error(f"Error getting list data: {str(e)}")
		return {
			"success": False,
			"data": None,
			"message": str(e)
		}

@frappe.whitelist()
def get_filtered_data(doctype, filter_config, user=None):
	"""Get data with advanced filtering"""
	try:
		# Validate parameters
		if not doctype:
			frappe.throw(_("DocType is required"))
		
		if not filter_config:
			frappe.throw(_("Filter configuration is required"))
		
		# Parse filter config
		if isinstance(filter_config, str):
			filter_config = json.loads(filter_config)
		
		# Use current user if not specified
		if not user:
			user = frappe.session.user
		
		# Check permissions
		if not frappe.has_permission(doctype, "read", user=user):
			frappe.throw(_("No permission to read {0}").format(doctype))
		
		# Extract parameters from filter config
		filters = filter_config.get("filters", [])
		columns = filter_config.get("columns")
		page = filter_config.get("page", 1)
		page_size = filter_config.get("page_size", 20)
		sort_by = filter_config.get("sort_by")
		sort_order = filter_config.get("sort_order", "asc")
		
		# Use the main get_list_data function
		return get_list_data(
			doctype=doctype,
			columns=columns,
			filters=filters,
			page=page,
			page_size=page_size,
			sort_by=sort_by,
			sort_order=sort_order,
			user=user
		)
		
	except Exception as e:
		frappe.log_error(f"Error getting filtered data: {str(e)}")
		return {
			"success": False,
			"data": None,
			"message": str(e)
		}

@frappe.whitelist()
def export_data(doctype, columns=None, filters=None, format="xlsx", user=None):
	"""Export data with custom column configuration"""
	try:
		# Validate parameters
		if not doctype:
			frappe.throw(_("DocType is required"))
		
		# Use current user if not specified
		if not user:
			user = frappe.session.user
		
		# Check permissions
		if not frappe.has_permission(doctype, "read", user=user):
			frappe.throw(_("No permission to read {0}").format(doctype))
		
		# Parse parameters
		if isinstance(filters, str):
			filters = json.loads(filters) if filters else []
		
		if isinstance(columns, str):
			columns = json.loads(columns) if columns else None
		
		# Get column configuration
		column_service = ColumnService()
		if not columns:
			config = column_service.get_user_column_config(doctype, user)
			columns = [col for col in config.get("columns", []) if col.get("visible")]
		
		# Build field list and headers
		fields = []
		headers = []
		for column in columns:
			fieldname = column.get("fieldname")
			label = column.get("label", fieldname)
			if fieldname:
				fields.append(fieldname)
				headers.append(label)
		
		# Ensure 'name' field is always included
		if "name" not in fields:
			fields.insert(0, "name")
			headers.insert(0, "ID")
		
		# Build filters
		filter_conditions = []
		if filters:
			filter_conditions = _build_filter_conditions(filters)
		
		# Get all data (no pagination for export)
		data = frappe.get_all(
			doctype,
			fields=fields,
			filters=filter_conditions,
			order_by="modified desc",
			as_list=False
		)
		
		# Format data for export
		export_data = []
		for row in data:
			export_row = []
			for field in fields:
				value = row.get(field, "")
				# Format value based on field type
				formatted_value = _format_export_value(value, field, doctype)
				export_row.append(formatted_value)
			export_data.append(export_row)
		
		# Create export file
		from frappe.utils.xlsxutils import make_xlsx
		from frappe.utils.csvutils import to_csv
		
		if format.lower() == "csv":
			# Create CSV
			csv_content = to_csv([headers] + export_data)
			
			# Create file
			file_name = f"{doctype}_export_{frappe.utils.now()}.csv"
			file_doc = frappe.get_doc({
				"doctype": "File",
				"file_name": file_name,
				"content": csv_content,
				"is_private": 1
			})
			file_doc.insert(ignore_permissions=True)
			
		else:
			# Create Excel
			xlsx_file = make_xlsx([headers] + export_data, doctype)
			
			# Create file
			file_name = f"{doctype}_export_{frappe.utils.now()}.xlsx"
			file_doc = frappe.get_doc({
				"doctype": "File",
				"file_name": file_name,
				"content": xlsx_file.getvalue(),
				"is_private": 1
			})
			file_doc.insert(ignore_permissions=True)
		
		return {
			"success": True,
			"data": {
				"file_url": file_doc.file_url,
				"file_name": file_name,
				"record_count": len(export_data),
				"column_count": len(headers)
			},
			"message": _("Data exported successfully")
		}
		
	except Exception as e:
		frappe.log_error(f"Error exporting data: {str(e)}")
		return {
			"success": False,
			"data": None,
			"message": str(e)
		}

@frappe.whitelist()
def get_list_settings(doctype, user=None):
	"""Get list view settings including columns, filters, and pagination preferences"""
	try:
		# Validate parameters
		if not doctype:
			frappe.throw(_("DocType is required"))
		
		# Use current user if not specified
		if not user:
			user = frappe.session.user
		
		# Check permissions
		if not frappe.has_permission(doctype, "read", user=user):
			frappe.throw(_("No permission to read {0}").format(doctype))
		
		# Get column configuration
		column_service = ColumnService()
		column_config = column_service.get_user_column_config(doctype, user)
		
		# Get user preferences
		from column_management.column_management.doctype.user_column_preference.user_column_preference import UserColumnPreference
		user_preferences = UserColumnPreference.get_user_preference(user, doctype)
		
		# Get saved filters
		from column_management.column_management.doctype.saved_filter.saved_filter import SavedFilter
		saved_filters = SavedFilter.get_user_filters(user, doctype)
		
		# Get metadata
		metadata_service = MetadataService()
		filterable_fields = metadata_service.get_filterable_fields(doctype)
		sortable_fields = metadata_service.get_sortable_fields(doctype)
		
		return {
			"success": True,
			"data": {
				"doctype": doctype,
				"columns": column_config,
				"user_preferences": user_preferences,
				"saved_filters": saved_filters,
				"filterable_fields": filterable_fields,
				"sortable_fields": sortable_fields
			},
			"message": _("List settings retrieved successfully")
		}
		
	except Exception as e:
		frappe.log_error(f"Error getting list settings: {str(e)}")
		return {
			"success": False,
			"data": None,
			"message": str(e)
		}

def _build_filter_conditions(filters):
	"""Build filter conditions from filter array"""
	conditions = []
	
	for filter_item in filters:
		if not isinstance(filter_item, dict):
			continue
		
		fieldname = filter_item.get("fieldname")
		operator = filter_item.get("operator")
		value = filter_item.get("value")
		
		if not fieldname or not operator:
			continue
		
		# Build condition based on operator
		if operator == "=":
			conditions.append([fieldname, "=", value])
		elif operator == "!=":
			conditions.append([fieldname, "!=", value])
		elif operator == ">":
			conditions.append([fieldname, ">", value])
		elif operator == "<":
			conditions.append([fieldname, "<", value])
		elif operator == ">=":
			conditions.append([fieldname, ">=", value])
		elif operator == "<=":
			conditions.append([fieldname, "<=", value])
		elif operator == "like":
			conditions.append([fieldname, "like", f"%{value}%"])
		elif operator == "not like":
			conditions.append([fieldname, "not like", f"%{value}%"])
		elif operator == "in":
			if isinstance(value, list):
				conditions.append([fieldname, "in", value])
			else:
				conditions.append([fieldname, "=", value])
		elif operator == "not in":
			if isinstance(value, list):
				conditions.append([fieldname, "not in", value])
			else:
				conditions.append([fieldname, "!=", value])
		elif operator == "between":
			if isinstance(value, list) and len(value) == 2:
				conditions.append([fieldname, "between", value])
	
	return conditions

def _format_list_data(data, columns, doctype):
	"""Format list data according to column configuration"""
	formatted_data = []
	
	# Get field types for formatting
	metadata_service = MetadataService()
	doctype_metadata = metadata_service.get_doctype_metadata(doctype)
	field_types = {field["fieldname"]: field["fieldtype"] for field in doctype_metadata.get("fields", [])}
	
	for row in data:
		formatted_row = {}
		
		for column in columns:
			fieldname = column.get("fieldname")
			if fieldname and fieldname in row:
				value = row[fieldname]
				fieldtype = field_types.get(fieldname, "Data")
				
				# Format value based on field type
				formatted_value = _format_field_value(value, fieldtype)
				formatted_row[fieldname] = formatted_value
		
		formatted_data.append(formatted_row)
	
	return formatted_data

def _format_field_value(value, fieldtype):
	"""Format field value based on field type"""
	if value is None:
		return ""
	
	try:
		if fieldtype == "Currency":
			return frappe.utils.fmt_money(value)
		elif fieldtype == "Date":
			return frappe.utils.formatdate(value)
		elif fieldtype == "Datetime":
			return frappe.utils.format_datetime(value)
		elif fieldtype == "Time":
			return frappe.utils.format_time(value)
		elif fieldtype == "Percent":
			return f"{float(value):.2f}%"
		elif fieldtype == "Float":
			return f"{float(value):.2f}"
		elif fieldtype == "Check":
			return "Yes" if value else "No"
		else:
			return str(value)
	except:
		return str(value)

def _format_export_value(value, fieldname, doctype):
	"""Format value for export"""
	if value is None:
		return ""
	
	try:
		# Get field type
		metadata_service = MetadataService()
		field_metadata = metadata_service.get_field_metadata(doctype, fieldname)
		fieldtype = field_metadata.get("fieldtype", "Data")
		
		return _format_field_value(value, fieldtype)
	except:
		return str(value)

@frappe.whitelist()
def get_filterable_fields(doctype, user=None):
	"""Get filterable fields for a DocType"""
	try:
		# Validate parameters
		if not doctype:
			frappe.throw(_("DocType is required"))
		
		# Use current user if not specified
		if not user:
			user = frappe.session.user
		
		# Check permissions
		if not frappe.has_permission(doctype, "read", user=user):
			frappe.throw(_("No permission to read {0}").format(doctype))
		
		# Get metadata
		metadata_service = MetadataService()
		filterable_fields = metadata_service.get_filterable_fields(doctype)
		
		return {
			"success": True,
			"data": {
				"fields": filterable_fields,
				"doctype": doctype
			},
			"message": _("Filterable fields retrieved successfully")
		}
		
	except Exception as e:
		frappe.log_error(f"Error getting filterable fields: {str(e)}")
		return {
			"success": False,
			"data": None,
			"message": str(e)
		}

@frappe.whitelist()
def get_saved_filters(doctype, user=None):
	"""Get saved filters for a DocType and user"""
	try:
		# Validate parameters
		if not doctype:
			frappe.throw(_("DocType is required"))
		
		# Use current user if not specified
		if not user:
			user = frappe.session.user
		
		# Check permissions
		if not frappe.has_permission(doctype, "read", user=user):
			frappe.throw(_("No permission to read {0}").format(doctype))
		
		# Get saved filters
		filters = frappe.get_all(
			"Saved Filter",
			fields=["name", "filter_name", "filter_config", "is_public", "owner", "creation"],
			filters={
				"doctype_name": doctype,
				"or": [
					{"owner": user},
					{"is_public": 1}
				]
			},
			order_by="creation desc"
		)
		
		# Parse filter configurations
		saved_filters = []
		for filter_doc in filters:
			try:
				filter_config = json.loads(filter_doc.get("filter_config", "[]"))
				saved_filters.append({
					"name": filter_doc.get("filter_name"),
					"filter_config": filter_config,
					"is_public": filter_doc.get("is_public", 0),
					"owner": filter_doc.get("owner"),
					"creation": filter_doc.get("creation")
				})
			except:
				continue
		
		return {
			"success": True,
			"data": saved_filters,
			"message": _("Saved filters retrieved successfully")
		}
		
	except Exception as e:
		frappe.log_error(f"Error getting saved filters: {str(e)}")
		return {
			"success": False,
			"data": None,
			"message": str(e)
		}

@frappe.whitelist()
def save_filter(doctype, filter_name, filter_config, is_public=0, user=None):
	"""Save a filter configuration"""
	try:
		# Validate parameters
		if not doctype:
			frappe.throw(_("DocType is required"))
		
		if not filter_name:
			frappe.throw(_("Filter name is required"))
		
		if not filter_config:
			frappe.throw(_("Filter configuration is required"))
		
		# Use current user if not specified
		if not user:
			user = frappe.session.user
		
		# Check permissions
		if not frappe.has_permission(doctype, "read", user=user):
			frappe.throw(_("No permission to read {0}").format(doctype))
		
		# Parse filter config
		if isinstance(filter_config, str):
			filter_config = json.loads(filter_config)
		
		# Check if filter with same name already exists for this user
		existing_filter = frappe.db.exists("Saved Filter", {
			"doctype_name": doctype,
			"filter_name": filter_name,
			"owner": user
		})
		
		if existing_filter:
			# Update existing filter
			filter_doc = frappe.get_doc("Saved Filter", existing_filter)
			filter_doc.filter_config = json.dumps(filter_config)
			filter_doc.is_public = int(is_public)
			filter_doc.save(ignore_permissions=True)
		else:
			# Create new filter
			filter_doc = frappe.get_doc({
				"doctype": "Saved Filter",
				"doctype_name": doctype,
				"filter_name": filter_name,
				"filter_config": json.dumps(filter_config),
				"is_public": int(is_public)
			})
			filter_doc.insert(ignore_permissions=True)
		
		return {
			"success": True,
			"data": {
				"filter_name": filter_name,
				"is_public": int(is_public)
			},
			"message": _("Filter saved successfully")
		}
		
	except Exception as e:
		frappe.log_error(f"Error saving filter: {str(e)}")
		return {
			"success": False,
			"data": None,
			"message": str(e)
		}

@frappe.whitelist()
def delete_filter(doctype, filter_name, user=None):
	"""Delete a saved filter"""
	try:
		# Validate parameters
		if not doctype:
			frappe.throw(_("DocType is required"))
		
		if not filter_name:
			frappe.throw(_("Filter name is required"))
		
		# Use current user if not specified
		if not user:
			user = frappe.session.user
		
		# Find the filter
		filter_doc = frappe.db.get_value("Saved Filter", {
			"doctype_name": doctype,
			"filter_name": filter_name,
			"owner": user
		}, "name")
		
		if not filter_doc:
			frappe.throw(_("Filter not found or you don't have permission to delete it"))
		
		# Delete the filter
		frappe.delete_doc("Saved Filter", filter_doc, ignore_permissions=True)
		
		return {
			"success": True,
			"data": {
				"filter_name": filter_name
			},
			"message": _("Filter deleted successfully")
		}
		
	except Exception as e:
		frappe.log_error(f"Error deleting filter: {str(e)}")
		return {
			"success": False,
			"data": None,
			"message": str(e)
		}

@frappe.whitelist()
def apply_advanced_filters(doctype, filters, columns=None, page=1, page_size=20, sort_by=None, sort_order="asc", user=None):
	"""Apply advanced filters with AND/OR logic"""
	try:
		# Validate parameters
		if not doctype:
			frappe.throw(_("DocType is required"))
		
		# Use current user if not specified
		if not user:
			user = frappe.session.user
		
		# Check permissions
		if not frappe.has_permission(doctype, "read", user=user):
			frappe.throw(_("No permission to read {0}").format(doctype))
		
		# Parse parameters
		if isinstance(filters, str):
			filters = json.loads(filters) if filters else []
		
		if isinstance(columns, str):
			columns = json.loads(columns) if columns else None
		
		# Build advanced filter conditions with AND/OR logic
		filter_conditions = _build_advanced_filter_conditions(filters)
		
		# Get list data with advanced filters
		return get_list_data(
			doctype=doctype,
			columns=columns,
			filters=filter_conditions,
			page=page,
			page_size=page_size,
			sort_by=sort_by,
			sort_order=sort_order,
			user=user
		)
		
	except Exception as e:
		frappe.log_error(f"Error applying advanced filters: {str(e)}")
		return {
			"success": False,
			"data": None,
			"message": str(e)
		}

def _build_advanced_filter_conditions(filters):
	"""Build advanced filter conditions with AND/OR logic support"""
	if not filters:
		return []
	
	conditions = []
	current_group = []
	current_logic = "AND"
	
	for i, filter_item in enumerate(filters):
		if not isinstance(filter_item, dict):
			continue
		
		fieldname = filter_item.get("fieldname")
		operator = filter_item.get("operator")
		value = filter_item.get("value")
		logic = filter_item.get("logic", "AND")
		
		if not fieldname or not operator or value == "":
			continue
		
		# Build individual condition
		condition = _build_single_condition(fieldname, operator, value)
		if not condition:
			continue
		
		# Handle logic grouping
		if i == 0:
			# First condition
			current_group.append(condition)
			current_logic = logic
		elif logic == current_logic:
			# Same logic, add to current group
			current_group.append(condition)
		else:
			# Different logic, finalize current group and start new one
			if current_group:
				if len(current_group) == 1:
					conditions.extend(current_group)
				else:
					# Group conditions with current logic
					if current_logic == "OR":
						conditions.append(["or", current_group])
					else:
						conditions.extend(current_group)
			
			# Start new group
			current_group = [condition]
			current_logic = logic
	
	# Add final group
	if current_group:
		if len(current_group) == 1:
			conditions.extend(current_group)
		else:
			if current_logic == "OR":
				conditions.append(["or", current_group])
			else:
				conditions.extend(current_group)
	
	return conditions

def _build_single_condition(fieldname, operator, value):
	"""Build a single filter condition"""
	try:
		# Handle different operators
		if operator == "=":
			return [fieldname, "=", value]
		elif operator == "!=":
			return [fieldname, "!=", value]
		elif operator == ">":
			return [fieldname, ">", value]
		elif operator == "<":
			return [fieldname, "<", value]
		elif operator == ">=":
			return [fieldname, ">=", value]
		elif operator == "<=":
			return [fieldname, "<=", value]
		elif operator == "like":
			return [fieldname, "like", f"%{value}%"]
		elif operator == "not like":
			return [fieldname, "not like", f"%{value}%"]
		elif operator == "in":
			if isinstance(value, str):
				# Split comma-separated values
				value_list = [v.strip() for v in value.split(",") if v.strip()]
				return [fieldname, "in", value_list]
			elif isinstance(value, list):
				return [fieldname, "in", value]
			else:
				return [fieldname, "=", value]
		elif operator == "not in":
			if isinstance(value, str):
				# Split comma-separated values
				value_list = [v.strip() for v in value.split(",") if v.strip()]
				return [fieldname, "not in", value_list]
			elif isinstance(value, list):
				return [fieldname, "not in", value]
			else:
				return [fieldname, "!=", value]
		elif operator == "between":
			if isinstance(value, list) and len(value) == 2:
				return [fieldname, "between", value]
			elif isinstance(value, str) and "," in value:
				# Split comma-separated range
				range_values = [v.strip() for v in value.split(",", 1)]
				if len(range_values) == 2:
					return [fieldname, "between", range_values]
		
		return None
		
	except Exception as e:
		frappe.log_error(f"Error building single condition: {str(e)}")
		return None

@frappe.whitelist()
def get_paginated_filtered_data(doctype, filter_state=None, pagination_state=None, user=None):
	"""Enhanced pagination with filter integration - Task 9.2"""
	try:
		# Validate parameters
		if not doctype:
			frappe.throw(_("DocType is required"))
		
		# Use current user if not specified
		if not user:
			user = frappe.session.user
		
		# Check permissions
		if not frappe.has_permission(doctype, "read", user=user):
			frappe.throw(_("No permission to read {0}").format(doctype))
		
		# Parse filter state
		if isinstance(filter_state, str):
			filter_state = json.loads(filter_state) if filter_state else {}
		filter_state = filter_state or {}
		
		# Parse pagination state
		if isinstance(pagination_state, str):
			pagination_state = json.loads(pagination_state) if pagination_state else {}
		pagination_state = pagination_state or {}
		
		# Extract filter parameters
		filters = filter_state.get("filters", [])
		active_saved_filter = filter_state.get("active_saved_filter")
		
		# If using saved filter, load its configuration
		if active_saved_filter:
			saved_filter_config = _get_saved_filter_config(doctype, active_saved_filter, user)
			if saved_filter_config:
				filters = saved_filter_config.get("filters", [])
		
		# Extract pagination parameters
		page = pagination_state.get("page", 1)
		page_size = pagination_state.get("page_size", 20)
		sort_by = pagination_state.get("sort_by")
		sort_order = pagination_state.get("sort_order", "asc")
		
		# Get column configuration
		column_service = ColumnService()
		config = column_service.get_user_column_config(doctype, user)
		columns = [col for col in config.get("columns", []) if col.get("visible")]
		
		# Get data using main function
		result = get_list_data(
			doctype=doctype,
			columns=columns,
			filters=filters,
			page=page,
			page_size=page_size,
			sort_by=sort_by,
			sort_order=sort_order,
			user=user
		)
		
		# Add filter state to response
		if result.get("success"):
			result["data"]["filter_state"] = {
				"filters": filters,
				"active_saved_filter": active_saved_filter,
				"filter_count": len([f for f in filters if f.get("fieldname")])
			}
			result["data"]["pagination_state"] = pagination_state
		
		return result
		
	except Exception as e:
		frappe.log_error(f"Error getting paginated filtered data: {str(e)}")
		return {
			"success": False,
			"data": None,
			"message": str(e),
			"error_type": "pagination_filter_error"
		}

@frappe.whitelist()
def reset_pagination_on_filter_change(doctype, new_filters, user=None):
	"""Reset pagination when filters change - Task 9.2"""
	try:
		# Validate parameters
		if not doctype:
			frappe.throw(_("DocType is required"))
		
		# Use current user if not specified
		if not user:
			user = frappe.session.user
		
		# Parse new filters
		if isinstance(new_filters, str):
			new_filters = json.loads(new_filters) if new_filters else []
		
		# Get total count with new filters
		filter_conditions = _build_filter_conditions(new_filters)
		total_count = frappe.db.count(doctype, filters=filter_conditions)
		
		# Calculate pagination info for first page
		page_size = 20  # Default page size
		total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 1
		
		return {
			"success": True,
			"data": {
				"reset_to_page": 1,
				"total_count": total_count,
				"total_pages": total_pages,
				"page_size": page_size,
				"filter_count": len([f for f in new_filters if f.get("fieldname")])
			},
			"message": _("Pagination reset for new filters")
		}
		
	except Exception as e:
		frappe.log_error(f"Error resetting pagination: {str(e)}")
		return {
			"success": False,
			"data": None,
			"message": str(e)
		}

@frappe.whitelist()
def get_filter_statistics(doctype, filters=None, user=None):
	"""Get statistics for current filter set - Task 9.2"""
	try:
		# Validate parameters
		if not doctype:
			frappe.throw(_("DocType is required"))
		
		# Use current user if not specified
		if not user:
			user = frappe.session.user
		
		# Check permissions
		if not frappe.has_permission(doctype, "read", user=user):
			frappe.throw(_("No permission to read {0}").format(doctype))
		
		# Parse filters
		if isinstance(filters, str):
			filters = json.loads(filters) if filters else []
		
		# Build filter conditions
		filter_conditions = _build_filter_conditions(filters) if filters else []
		
		# Get basic statistics
		total_count = frappe.db.count(doctype, filters=filter_conditions)
		
		# Get additional statistics if available
		statistics = {
			"total_records": total_count,
			"filtered_records": total_count,
			"filter_count": len([f for f in filters if f.get("fieldname")]) if filters else 0
		}
		
		# Calculate pages info
		page_sizes = [10, 20, 50, 100, 200]
		pages_info = {}
		for size in page_sizes:
			pages_info[str(size)] = (total_count + size - 1) // size if total_count > 0 else 1
		
		statistics["pages_by_size"] = pages_info
		
		return {
			"success": True,
			"data": statistics,
			"message": _("Filter statistics retrieved successfully")
		}
		
	except Exception as e:
		frappe.log_error(f"Error getting filter statistics: {str(e)}")
		return {
			"success": False,
			"data": None,
			"message": str(e)
		}

def _get_saved_filter_config(doctype, filter_name, user):
	"""Get saved filter configuration"""
	try:
		filter_doc = frappe.db.get_value(
			"Saved Filter",
			{
				"doctype_name": doctype,
				"filter_name": filter_name,
				"or": [
					{"owner": user},
					{"is_public": 1}
				]
			},
			"filter_config"
		)
		
		if filter_doc:
			return json.loads(filter_doc)
		
		return None
		
	except Exception as e:
		frappe.log_error(f"Error getting saved filter config: {str(e)}")
		return None

@frappe.whitelist()
def validate_pagination_state(doctype, pagination_state, filters=None, user=None):
	"""Validate and adjust pagination state based on current filters - Task 9.2"""
	try:
		# Validate parameters
		if not doctype:
			frappe.throw(_("DocType is required"))
		
		# Use current user if not specified
		if not user:
			user = frappe.session.user
		
		# Parse parameters
		if isinstance(pagination_state, str):
			pagination_state = json.loads(pagination_state) if pagination_state else {}
		
		if isinstance(filters, str):
			filters = json.loads(filters) if filters else []
		
		# Get current total count with filters
		filter_conditions = _build_filter_conditions(filters) if filters else []
		total_count = frappe.db.count(doctype, filters=filter_conditions)
		
		# Extract pagination parameters
		current_page = pagination_state.get("page", 1)
		page_size = pagination_state.get("page_size", 20)
		
		# Calculate valid pagination
		total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 1
		valid_page = min(max(1, current_page), total_pages)
		
		# Determine if pagination needs adjustment
		needs_adjustment = (current_page != valid_page) or (total_count == 0 and current_page > 1)
		
		adjusted_state = {
			"page": valid_page,
			"page_size": page_size,
			"total_count": total_count,
			"total_pages": total_pages,
			"needs_adjustment": needs_adjustment,
			"has_next": valid_page < total_pages,
			"has_prev": valid_page > 1
		}
		
		return {
			"success": True,
			"data": adjusted_state,
			"message": _("Pagination state validated")
		}
		
	except Exception as e:
		frappe.log_error(f"Error validating pagination state: {str(e)}")
		return {
			"success": False,
			"data": None,
			"message": str(e)
		}
		
# Advanced Filter Logic and Execution - Task 10.2

@frappe.whitelist()
def process_complex_filters(doctype, filter_conditions, user=None):
	"""Process complex filter conditions with AND/OR logic and proper precedence"""
	try:
		# Validate parameters
		if not doctype:
			frappe.throw(_("DocType is required"))
		
		# Use current user if not specified
		if not user:
			user = frappe.session.user
		
		# Check permissions
		if not frappe.has_permission(doctype, "read", user=user):
			frappe.throw(_("No permission to read {0}").format(doctype))
		
		# Parse filter conditions
		if isinstance(filter_conditions, str):
			filter_conditions = json.loads(filter_conditions) if filter_conditions else []
		
		# Build optimized filter query
		optimized_filters = _build_optimized_filter_conditions(filter_conditions, doctype)
		
		# Validate filter conditions
		validation_result = _validate_filter_conditions(filter_conditions, doctype)
		
		return {
			"success": True,
			"data": {
				"optimized_filters": optimized_filters,
				"validation": validation_result,
				"original_conditions": filter_conditions
			},
			"message": _("Complex filters processed successfully")
		}
		
	except Exception as e:
		frappe.log_error(f"Error processing complex filters: {str(e)}")
		return {
			"success": False,
			"data": None,
			"message": str(e)
		}

def _build_optimized_filter_conditions(filter_conditions, doctype):
	"""Build optimized filter conditions with proper AND/OR precedence"""
	if not filter_conditions:
		return []
	
	# Group conditions by logic operator
	and_groups = []
	or_groups = []
	current_and_group = []
	current_or_group = []
	
	for i, condition in enumerate(filter_conditions):
		if not isinstance(condition, dict):
			continue
		
		fieldname = condition.get("fieldname")
		operator = condition.get("operator")
		value = condition.get("value")
		logic = condition.get("logic", "AND")
		
		if not fieldname or not operator:
			continue
		
		# Build the condition
		built_condition = _build_single_optimized_condition(fieldname, operator, value, doctype)
		if not built_condition:
			continue
		
		# Group by logic operator
		if i == 0 or logic == "AND":
			current_and_group.append(built_condition)
		else:  # OR logic
			# Finalize current AND group if it exists
			if current_and_group:
				and_groups.append(current_and_group)
				current_and_group = []
			
			current_or_group.append(built_condition)
	
	# Finalize remaining groups
	if current_and_group:
		and_groups.append(current_and_group)
	if current_or_group:
		or_groups.append(current_or_group)
	
	# Build final filter structure with proper precedence
	final_filters = []
	
	# Add AND groups
	for and_group in and_groups:
		if len(and_group) == 1:
			final_filters.extend(and_group)
		else:
			final_filters.extend(and_group)
	
	# Add OR groups
	for or_group in or_groups:
		if len(or_group) == 1:
			final_filters.extend(or_group)
		else:
			final_filters.append(["or", or_group])
	
	return final_filters

def _build_single_optimized_condition(fieldname, operator, value, doctype):
	"""Build a single optimized filter condition with database optimization"""
	try:
		# Get field metadata for optimization
		metadata_service = MetadataService()
		field_metadata = metadata_service.get_field_metadata(doctype, fieldname)
		fieldtype = field_metadata.get("fieldtype", "Data")
		
		# Optimize value based on field type
		optimized_value = _optimize_filter_value(value, fieldtype, operator)
		
		# Handle special operators with optimization
		if operator == "=":
			return [fieldname, "=", optimized_value]
		elif operator == "!=":
			return [fieldname, "!=", optimized_value]
		elif operator == ">":
			return [fieldname, ">", optimized_value]
		elif operator == "<":
			return [fieldname, "<", optimized_value]
		elif operator == ">=":
			return [fieldname, ">=", optimized_value]
		elif operator == "<=":
			return [fieldname, "<=", optimized_value]
		elif operator == "like":
			# Optimize LIKE queries
			if fieldtype in ["Data", "Text", "Small Text", "Long Text"]:
				# Use index-friendly patterns when possible
				if optimized_value and not optimized_value.startswith("%"):
					return [fieldname, "like", f"{optimized_value}%"]
				else:
					return [fieldname, "like", f"%{optimized_value}%"]
			else:
				return [fieldname, "like", f"%{optimized_value}%"]
		elif operator == "not like":
			return [fieldname, "not like", f"%{optimized_value}%"]
		elif operator == "in":
			if isinstance(optimized_value, str):
				# Split comma-separated values and clean them
				value_list = [v.strip() for v in optimized_value.split(",") if v.strip()]
				return [fieldname, "in", value_list]
			elif isinstance(optimized_value, list):
				return [fieldname, "in", optimized_value]
			else:
				return [fieldname, "=", optimized_value]
		elif operator == "not in":
			if isinstance(optimized_value, str):
				value_list = [v.strip() for v in optimized_value.split(",") if v.strip()]
				return [fieldname, "not in", value_list]
			elif isinstance(optimized_value, list):
				return [fieldname, "not in", optimized_value]
			else:
				return [fieldname, "!=", optimized_value]
		elif operator == "between":
			if isinstance(optimized_value, list) and len(optimized_value) == 2:
				# Ensure proper ordering for between
				val1, val2 = optimized_value
				if fieldtype in ["Int", "Float", "Currency"]:
					try:
						val1, val2 = float(val1), float(val2)
						if val1 > val2:
							val1, val2 = val2, val1
					except:
						pass
				return [fieldname, "between", [val1, val2]]
			elif isinstance(optimized_value, str) and "," in optimized_value:
				range_values = [v.strip() for v in optimized_value.split(",", 1)]
				if len(range_values) == 2:
					return [fieldname, "between", range_values]
		elif operator == "is":
			if optimized_value in ["null", "None", "", None]:
				return [fieldname, "is", "null"]
			else:
				return [fieldname, "is", "not null"]
		elif operator == "is not":
			if optimized_value in ["null", "None", "", None]:
				return [fieldname, "is", "not null"]
			else:
				return [fieldname, "is", "null"]
		
		return None
		
	except Exception as e:
		frappe.log_error(f"Error building optimized condition: {str(e)}")
		return None

def _optimize_filter_value(value, fieldtype, operator):
	"""Optimize filter value based on field type and operator"""
	if value is None or value == "":
		return value
	
	try:
		# Type-specific optimizations
		if fieldtype in ["Int", "Float", "Currency"]:
			if operator in ["=", "!=", ">", "<", ">=", "<="]:
				return float(value) if fieldtype in ["Float", "Currency"] else int(float(value))
			elif operator == "between":
				if isinstance(value, list):
					return [float(v) if fieldtype in ["Float", "Currency"] else int(float(v)) for v in value]
		
		elif fieldtype == "Date":
			if operator in ["=", "!=", ">", "<", ">=", "<=", "between"]:
				# Ensure proper date format
				if isinstance(value, str):
					try:
						parsed_date = frappe.utils.getdate(value)
						return parsed_date.strftime("%Y-%m-%d")
					except:
						return value
				elif isinstance(value, list):
					return [frappe.utils.getdate(v).strftime("%Y-%m-%d") for v in value]
		
		elif fieldtype == "Datetime":
			if operator in ["=", "!=", ">", "<", ">=", "<=", "between"]:
				# Ensure proper datetime format
				if isinstance(value, str):
					try:
						parsed_datetime = frappe.utils.get_datetime(value)
						return parsed_datetime.strftime("%Y-%m-%d %H:%M:%S")
					except:
						return value
				elif isinstance(value, list):
					return [frappe.utils.get_datetime(v).strftime("%Y-%m-%d %H:%M:%S") for v in value]
		
		elif fieldtype == "Check":
			# Convert to boolean
			if isinstance(value, str):
				return value.lower() in ["1", "true", "yes", "on"]
			return bool(value)
		
		elif fieldtype in ["Data", "Text", "Small Text", "Long Text"]:
			# String optimizations
			if operator in ["like", "not like"]:
				# Remove unnecessary wildcards for optimization
				return str(value).strip()
		
		return value
		
	except Exception as e:
		frappe.log_error(f"Error optimizing filter value: {str(e)}")
		return value

def _validate_filter_conditions(filter_conditions, doctype):
	"""Validate filter conditions for correctness and performance"""
	validation = {
		"is_valid": True,
		"errors": [],
		"warnings": [],
		"performance_score": 100,
		"optimization_suggestions": []
	}
	
	if not filter_conditions:
		return validation
	
	try:
		# Get doctype metadata for validation
		metadata_service = MetadataService()
		doctype_metadata = metadata_service.get_doctype_metadata(doctype)
		available_fields = {field["fieldname"]: field for field in doctype_metadata.get("fields", [])}
		
		# Validate each condition
		for i, condition in enumerate(filter_conditions):
			if not isinstance(condition, dict):
				validation["errors"].append(f"Condition {i+1}: Invalid condition format")
				validation["is_valid"] = False
				continue
			
			fieldname = condition.get("fieldname")
			operator = condition.get("operator")
			value = condition.get("value")
			
			# Validate field exists
			if not fieldname:
				validation["errors"].append(f"Condition {i+1}: Field name is required")
				validation["is_valid"] = False
				continue
			
			if fieldname not in available_fields:
				validation["errors"].append(f"Condition {i+1}: Field '{fieldname}' does not exist")
				validation["is_valid"] = False
				continue
			
			# Validate operator
			if not operator:
				validation["errors"].append(f"Condition {i+1}: Operator is required")
				validation["is_valid"] = False
				continue
			
			field_info = available_fields[fieldname]
			fieldtype = field_info.get("fieldtype")
			
			# Validate operator for field type
			valid_operators = _get_valid_operators_for_fieldtype(fieldtype)
			if operator not in valid_operators:
				validation["errors"].append(f"Condition {i+1}: Operator '{operator}' is not valid for field type '{fieldtype}'")
				validation["is_valid"] = False
				continue
			
			# Validate value
			value_validation = _validate_filter_value(value, fieldtype, operator)
			if not value_validation["is_valid"]:
				validation["errors"].extend([f"Condition {i+1}: {error}" for error in value_validation["errors"]])
				validation["is_valid"] = False
			
			# Performance analysis
			performance_impact = _analyze_condition_performance(fieldname, operator, value, field_info)
			validation["performance_score"] -= performance_impact["penalty"]
			if performance_impact["suggestions"]:
				validation["optimization_suggestions"].extend(performance_impact["suggestions"])
		
		# Analyze overall filter structure
		structure_analysis = _analyze_filter_structure(filter_conditions)
		validation["warnings"].extend(structure_analysis["warnings"])
		validation["optimization_suggestions"].extend(structure_analysis["suggestions"])
		
		# Final performance score
		validation["performance_score"] = max(0, validation["performance_score"])
		
		return validation
		
	except Exception as e:
		frappe.log_error(f"Error validating filter conditions: {str(e)}")
		validation["errors"].append(f"Validation error: {str(e)}")
		validation["is_valid"] = False
		return validation

def _get_valid_operators_for_fieldtype(fieldtype):
	"""Get valid operators for a specific field type"""
	operator_map = {
		"Data": ["=", "!=", "like", "not like", "in", "not in", "is", "is not"],
		"Text": ["=", "!=", "like", "not like", "in", "not in", "is", "is not"],
		"Small Text": ["=", "!=", "like", "not like", "in", "not in", "is", "is not"],
		"Long Text": ["=", "!=", "like", "not like", "in", "not in", "is", "is not"],
		"Link": ["=", "!=", "like", "not like", "in", "not in", "is", "is not"],
		"Select": ["=", "!=", "in", "not in", "is", "is not"],
		"Int": ["=", "!=", ">", "<", ">=", "<=", "between", "in", "not in", "is", "is not"],
		"Float": ["=", "!=", ">", "<", ">=", "<=", "between", "in", "not in", "is", "is not"],
		"Currency": ["=", "!=", ">", "<", ">=", "<=", "between", "in", "not in", "is", "is not"],
		"Date": ["=", "!=", ">", "<", ">=", "<=", "between", "is", "is not"],
		"Datetime": ["=", "!=", ">", "<", ">=", "<=", "between", "is", "is not"],
		"Time": ["=", "!=", ">", "<", ">=", "<=", "between", "is", "is not"],
		"Check": ["=", "!=", "is", "is not"],
		"Attach": ["=", "!=", "like", "not like", "is", "is not"],
		"Attach Image": ["=", "!=", "like", "not like", "is", "is not"],
		"Code": ["=", "!=", "like", "not like", "in", "not in", "is", "is not"],
		"Table": ["is", "is not"]
	}
	
	return operator_map.get(fieldtype, ["=", "!=", "is", "is not"])

def _validate_filter_value(value, fieldtype, operator):
	"""Validate filter value for field type and operator"""
	validation = {
		"is_valid": True,
		"errors": []
	}
	
	# Special operators that don't require values
	if operator in ["is", "is not"]:
		return validation
	
	# Check if value is required
	if value is None or value == "":
		if operator not in ["is", "is not"]:
			validation["errors"].append("Value is required for this operator")
			validation["is_valid"] = False
		return validation
	
	try:
		# Type-specific validation
		if fieldtype in ["Int", "Float", "Currency"]:
			if operator == "between":
				if isinstance(value, list):
					if len(value) != 2:
						validation["errors"].append("Between operator requires exactly two values")
						validation["is_valid"] = False
					else:
						for v in value:
							try:
								float(v)
							except:
								validation["errors"].append(f"Value '{v}' is not a valid number")
								validation["is_valid"] = False
				elif isinstance(value, str) and "," in value:
					range_values = value.split(",", 1)
					for v in range_values:
						try:
							float(v.strip())
						except:
							validation["errors"].append(f"Value '{v.strip()}' is not a valid number")
							validation["is_valid"] = False
				else:
					validation["errors"].append("Between operator requires two comma-separated values")
					validation["is_valid"] = False
			elif operator in ["in", "not in"]:
				if isinstance(value, str):
					values = [v.strip() for v in value.split(",")]
					for v in values:
						try:
							float(v)
						except:
							validation["errors"].append(f"Value '{v}' is not a valid number")
							validation["is_valid"] = False
				elif isinstance(value, list):
					for v in value:
						try:
							float(v)
						except:
							validation["errors"].append(f"Value '{v}' is not a valid number")
							validation["is_valid"] = False
			else:
				try:
					float(value)
				except:
					validation["errors"].append("Value must be a valid number")
					validation["is_valid"] = False
		
		elif fieldtype in ["Date", "Datetime"]:
			if operator == "between":
				if isinstance(value, list) and len(value) == 2:
					for v in value:
						try:
							frappe.utils.getdate(v) if fieldtype == "Date" else frappe.utils.get_datetime(v)
						except:
							validation["errors"].append(f"Value '{v}' is not a valid date")
							validation["is_valid"] = False
				else:
					validation["errors"].append("Between operator requires two date values")
					validation["is_valid"] = False
			else:
				try:
					frappe.utils.getdate(value) if fieldtype == "Date" else frappe.utils.get_datetime(value)
				except:
					validation["errors"].append("Value must be a valid date")
					validation["is_valid"] = False
		
		elif fieldtype == "Check":
			if operator in ["=", "!="]:
				if not isinstance(value, bool) and str(value).lower() not in ["0", "1", "true", "false", "yes", "no"]:
					validation["errors"].append("Value must be a boolean (true/false)")
					validation["is_valid"] = False
		
		return validation
		
	except Exception as e:
		validation["errors"].append(f"Validation error: {str(e)}")
		validation["is_valid"] = False
		return validation

def _analyze_condition_performance(fieldname, operator, value, field_info):
	"""Analyze performance impact of a filter condition"""
	analysis = {
		"penalty": 0,
		"suggestions": []
	}
	
	try:
		# Check if field is indexed
		is_indexed = field_info.get("search_index") or fieldname in ["name", "owner", "creation", "modified"]
		
		# Operator-specific analysis
		if operator in ["like", "not like"]:
			if not is_indexed:
				analysis["penalty"] += 20
				analysis["suggestions"].append(f"Consider adding search index to field '{fieldname}' for better LIKE performance")
			
			if isinstance(value, str) and value.startswith("%"):
				analysis["penalty"] += 15
				analysis["suggestions"].append(f"Leading wildcard in LIKE pattern for '{fieldname}' may cause slow queries")
		
		elif operator in ["in", "not in"]:
			if isinstance(value, (list, str)):
				value_count = len(value) if isinstance(value, list) else len(value.split(","))
				if value_count > 100:
					analysis["penalty"] += 25
					analysis["suggestions"].append(f"Large IN list ({value_count} values) for '{fieldname}' may impact performance")
				elif value_count > 20:
					analysis["penalty"] += 10
		
		elif operator == "!=":
			if not is_indexed:
				analysis["penalty"] += 15
				analysis["suggestions"].append(f"NOT EQUAL operator on unindexed field '{fieldname}' may be slow")
		
		# Field type specific analysis
		fieldtype = field_info.get("fieldtype")
		if fieldtype in ["Text", "Long Text"] and operator in ["=", "!="]:
			analysis["penalty"] += 10
			analysis["suggestions"].append(f"Exact match on text field '{fieldname}' may be inefficient, consider using LIKE")
		
		return analysis
		
	except Exception as e:
		frappe.log_error(f"Error analyzing condition performance: {str(e)}")
		return analysis

def _analyze_filter_structure(filter_conditions):
	"""Analyze overall filter structure for optimization opportunities"""
	analysis = {
		"warnings": [],
		"suggestions": []
	}
	
	try:
		if len(filter_conditions) <= 1:
			return analysis
		
		# Check for mixed AND/OR logic
		logic_operators = [condition.get("logic", "AND") for condition in filter_conditions[1:]]
		has_and = "AND" in logic_operators
		has_or = "OR" in logic_operators
		
		if has_and and has_or:
			analysis["warnings"].append("Mixed AND/OR logic detected. Consider using parentheses for complex conditions to ensure proper precedence.")
		
		# Check for redundant conditions
		field_operators = {}
		for condition in filter_conditions:
			fieldname = condition.get("fieldname")
			operator = condition.get("operator")
			if fieldname and operator:
				key = f"{fieldname}_{operator}"
				if key in field_operators:
					analysis["warnings"].append(f"Duplicate condition detected for field '{fieldname}' with operator '{operator}'")
				field_operators[key] = True
		
		# Check for potentially conflicting conditions
		field_conditions = {}
		for condition in filter_conditions:
			fieldname = condition.get("fieldname")
			if fieldname:
				if fieldname not in field_conditions:
					field_conditions[fieldname] = []
				field_conditions[fieldname].append(condition)
		
		for fieldname, conditions in field_conditions.items():
			if len(conditions) > 1:
				# Check for conflicting equality conditions
				equality_values = []
				for condition in conditions:
					if condition.get("operator") == "=" and condition.get("logic", "AND") == "AND":
						equality_values.append(condition.get("value"))
				
				if len(equality_values) > 1:
					analysis["warnings"].append(f"Multiple AND equality conditions for field '{fieldname}' may result in no matches")
		
		# Performance suggestions
		if len(filter_conditions) > 5:
			analysis["suggestions"].append("Consider reducing the number of filter conditions for better performance")
		
		return analysis
		
	except Exception as e:
		frappe.log_error(f"Error analyzing filter structure: {str(e)}")
		return analysis

@frappe.whitelist()
def optimize_filter_query(doctype, filter_conditions, user=None):
	"""Optimize filter query for better database performance"""
	try:
		# Validate parameters
		if not doctype:
			frappe.throw(_("DocType is required"))
		
		# Use current user if not specified
		if not user:
			user = frappe.session.user
		
		# Parse filter conditions
		if isinstance(filter_conditions, str):
			filter_conditions = json.loads(filter_conditions) if filter_conditions else []
		
		# Get doctype metadata
		metadata_service = MetadataService()
		doctype_metadata = metadata_service.get_doctype_metadata(doctype)
		
		# Analyze and optimize conditions
		optimization_result = _optimize_filter_conditions(filter_conditions, doctype_metadata)
		
		return {
			"success": True,
			"data": {
				"original_conditions": filter_conditions,
				"optimized_conditions": optimization_result["optimized"],
				"optimization_applied": optimization_result["optimizations"],
				"performance_improvement": optimization_result["improvement_estimate"]
			},
			"message": _("Filter query optimized successfully")
		}
		
	except Exception as e:
		frappe.log_error(f"Error optimizing filter query: {str(e)}")
		return {
			"success": False,
			"data": None,
			"message": str(e)
		}

def _optimize_filter_conditions(filter_conditions, doctype_metadata):
	"""Apply various optimizations to filter conditions"""
	optimization_result = {
		"optimized": [],
		"optimizations": [],
		"improvement_estimate": 0
	}
	
	try:
		available_fields = {field["fieldname"]: field for field in doctype_metadata.get("fields", [])}
		indexed_fields = [field["fieldname"] for field in doctype_metadata.get("fields", []) 
						 if field.get("search_index") or field["fieldname"] in ["name", "owner", "creation", "modified"]]
		
		# Sort conditions to put indexed fields first
		sorted_conditions = sorted(filter_conditions, 
								 key=lambda x: 0 if x.get("fieldname") in indexed_fields else 1)
		
		if sorted_conditions != filter_conditions:
			optimization_result["optimizations"].append("Reordered conditions to prioritize indexed fields")
			optimization_result["improvement_estimate"] += 15
		
		# Optimize individual conditions
		for condition in sorted_conditions:
			fieldname = condition.get("fieldname")
			operator = condition.get("operator")
			value = condition.get("value")
			
			if not fieldname or not operator:
				continue
			
			field_info = available_fields.get(fieldname, {})
			optimized_condition = _optimize_single_condition(condition, field_info)
			
			if optimized_condition != condition:
				optimization_result["optimizations"].append(f"Optimized condition for field '{fieldname}'")
				optimization_result["improvement_estimate"] += 5
			
			optimization_result["optimized"].append(optimized_condition)
		
		return optimization_result
		
	except Exception as e:
		frappe.log_error(f"Error in filter optimization: {str(e)}")
		return optimization_result

def _optimize_single_condition(condition, field_info):
	"""Optimize a single filter condition"""
	optimized = condition.copy()
	
	try:
		fieldname = condition.get("fieldname")
		operator = condition.get("operator")
		value = condition.get("value")
		fieldtype = field_info.get("fieldtype", "Data")
		
		# Optimize LIKE patterns
		if operator == "like" and isinstance(value, str):
			# Remove unnecessary leading wildcards if possible
			if value.startswith("%") and not value.endswith("%"):
				# Check if we can use a more efficient pattern
				clean_value = value.lstrip("%")
				if clean_value and not any(char in clean_value for char in ["%", "_"]):
					optimized["operator"] = ">="
					optimized["value"] = clean_value
		
		# Optimize IN conditions with single values
		elif operator == "in":
			if isinstance(value, list) and len(value) == 1:
				optimized["operator"] = "="
				optimized["value"] = value[0]
			elif isinstance(value, str) and "," not in value:
				optimized["operator"] = "="
				optimized["value"] = value.strip()
		
		# Optimize NOT IN conditions with single values
		elif operator == "not in":
			if isinstance(value, list) and len(value) == 1:
				optimized["operator"] = "!="
				optimized["value"] = value[0]
			elif isinstance(value, str) and "," not in value:
				optimized["operator"] = "!="
				optimized["value"] = value.strip()
		
		# Optimize range conditions
		elif operator == "between" and isinstance(value, list) and len(value) == 2:
			val1, val2 = value
			if val1 == val2:
				optimized["operator"] = "="
				optimized["value"] = val1
		
		return optimized
		
	except Exception as e:
		frappe.log_error(f"Error optimizing single condition: {str(e)}")
		return condition

@frappe.whitelist()
def execute_optimized_filters(doctype, optimized_conditions, columns=None, page=1, page_size=20, sort_by=None, sort_order="asc", user=None):
	"""Execute optimized filter conditions with performance monitoring"""
	try:
		import time
		start_time = time.time()
		
		# Validate parameters
		if not doctype:
			frappe.throw(_("DocType is required"))
		
		# Use current user if not specified
		if not user:
			user = frappe.session.user
		
		# Check permissions
		if not frappe.has_permission(doctype, "read", user=user):
			frappe.throw(_("No permission to read {0}").format(doctype))
		
		# Parse parameters
		if isinstance(optimized_conditions, str):
			optimized_conditions = json.loads(optimized_conditions) if optimized_conditions else []
		
		# Execute the optimized query
		result = get_list_data(
			doctype=doctype,
			columns=columns,
			filters=optimized_conditions,
			page=page,
			page_size=page_size,
			sort_by=sort_by,
			sort_order=sort_order,
			user=user
		)
		
		# Add performance metrics
		execution_time = time.time() - start_time
		
		if result.get("success"):
			result["data"]["performance"] = {
				"execution_time": round(execution_time * 1000, 2),  # in milliseconds
				"conditions_count": len(optimized_conditions),
				"records_returned": len(result["data"]["records"]),
				"total_records": result["data"]["pagination"]["total_count"]
			}
		
		return result
		
	except Exception as e:
		frappe.log_error(f"Error executing optimized filters: {str(e)}")
		return {
			"success": False,
			"data": None,
			"message": str(e)
		}
		
# Enhanced Saved Filter Management API - Task 10.3

@frappe.whitelist()
def get_filter_categories(doctype, user=None):
	"""Get available filter categories for organization"""
	try:
		if not doctype:
			frappe.throw(_("DocType is required"))
		
		if not user:
			user = frappe.session.user
		
		# Check permissions
		if not frappe.has_permission(doctype, "read", user=user):
			frappe.throw(_("No permission to read {0}").format(doctype))
		
		from column_management.column_management.doctype.saved_filter.saved_filter import SavedFilter
		categories = SavedFilter.get_filter_categories(user, doctype)
		
		return {
			"success": True,
			"data": {
				"categories": categories,
				"doctype": doctype
			},
			"message": _("Filter categories retrieved successfully")
		}
		
	except Exception as e:
		frappe.log_error(f"Error getting filter categories: {str(e)}")
		return {
			"success": False,
			"data": None,
			"message": str(e)
		}

@frappe.whitelist()
def get_organized_filters(doctype, user=None):
	"""Get filters organized by category"""
	try:
		if not doctype:
			frappe.throw(_("DocType is required"))
		
		if not user:
			user = frappe.session.user
		
		# Check permissions
		if not frappe.has_permission(doctype, "read", user=user):
			frappe.throw(_("No permission to read {0}").format(doctype))
		
		from column_management.column_management.doctype.saved_filter.saved_filter import SavedFilter
		organized_filters = SavedFilter.organize_filters_by_category(user, doctype)
		
		return {
			"success": True,
			"data": {
				"organized_filters": organized_filters,
				"doctype": doctype
			},
			"message": _("Organized filters retrieved successfully")
		}
		
	except Exception as e:
		frappe.log_error(f"Error getting organized filters: {str(e)}")
		return {
			"success": False,
			"data": None,
			"message": str(e)
		}

@frappe.whitelist()
def duplicate_saved_filter(filter_name, new_name, user=None):
	"""Duplicate an existing saved filter"""
	try:
		if not filter_name:
			frappe.throw(_("Filter name is required"))
		
		if not new_name:
			frappe.throw(_("New filter name is required"))
		
		if not user:
			user = frappe.session.user
		
		from column_management.column_management.doctype.saved_filter.saved_filter import SavedFilter
		duplicated_filter = SavedFilter.duplicate_filter(filter_name, new_name, user)
		
		return {
			"success": True,
			"data": {
				"filter_name": duplicated_filter.name,
				"new_name": duplicated_filter.filter_name
			},
			"message": _("Filter duplicated successfully")
		}
		
	except Exception as e:
		frappe.log_error(f"Error duplicating filter: {str(e)}")
		return {
			"success": False,
			"data": None,
			"message": str(e)
		}

@frappe.whitelist()
def export_saved_filter(filter_name):
	"""Export a saved filter for sharing"""
	try:
		if not filter_name:
			frappe.throw(_("Filter name is required"))
		
		from column_management.column_management.doctype.saved_filter.saved_filter import SavedFilter
		export_data = SavedFilter.export_filter(filter_name)
		
		return {
			"success": True,
			"data": {
				"export_data": export_data,
				"filter_name": export_data["filter_name"]
			},
			"message": _("Filter exported successfully")
		}
		
	except Exception as e:
		frappe.log_error(f"Error exporting filter: {str(e)}")
		return {
			"success": False,
			"data": None,
			"message": str(e)
		}

@frappe.whitelist()
def import_saved_filter(import_data, user=None):
	"""Import a saved filter from export data"""
	try:
		if not import_data:
			frappe.throw(_("Import data is required"))
		
		if isinstance(import_data, str):
			import_data = json.loads(import_data)
		
		if not user:
			user = frappe.session.user
		
		from column_management.column_management.doctype.saved_filter.saved_filter import SavedFilter
		imported_filter = SavedFilter.import_filter(import_data, user)
		
		return {
			"success": True,
			"data": {
				"filter_name": imported_filter.name,
				"imported_name": imported_filter.filter_name,
				"doctype": imported_filter.doctype_name
			},
			"message": _("Filter imported successfully")
		}
		
	except Exception as e:
		frappe.log_error(f"Error importing filter: {str(e)}")
		return {
			"success": False,
			"data": None,
			"message": str(e)
		}

@frappe.whitelist()
def get_filter_usage_stats(doctype, user=None):
	"""Get usage statistics for saved filters"""
	try:
		if not doctype:
			frappe.throw(_("DocType is required"))
		
		if not user:
			user = frappe.session.user
		
		# Check permissions
		if not frappe.has_permission(doctype, "read", user=user):
			frappe.throw(_("No permission to read {0}").format(doctype))
		
		from column_management.column_management.doctype.saved_filter.saved_filter import SavedFilter
		stats = SavedFilter.get_filter_usage_stats(user, doctype)
		
		return {
			"success": True,
			"data": {
				"stats": stats,
				"doctype": doctype
			},
			"message": _("Filter usage statistics retrieved successfully")
		}
		
	except Exception as e:
		frappe.log_error(f"Error getting filter usage stats: {str(e)}")
		return {
			"success": False,
			"data": None,
			"message": str(e)
		}

@frappe.whitelist()
def cleanup_unused_filters(doctype, days_old=90, user=None):
	"""Clean up old unused filters"""
	try:
		if not doctype:
			frappe.throw(_("DocType is required"))
		
		if not user:
			user = frappe.session.user
		
		days_old = int(days_old) if days_old else 90
		
		from column_management.column_management.doctype.saved_filter.saved_filter import SavedFilter
		cleanup_result = SavedFilter.cleanup_unused_filters(user, doctype, days_old)
		
		return {
			"success": True,
			"data": {
				"cleanup_result": cleanup_result,
				"doctype": doctype,
				"days_old": days_old
			},
			"message": _("Filter cleanup completed successfully")
		}
		
	except Exception as e:
		frappe.log_error(f"Error cleaning up filters: {str(e)}")
		return {
			"success": False,
			"data": None,
			"message": str(e)
		}

@frappe.whitelist()
def merge_saved_filters(primary_filter, secondary_filter, merged_name):
	"""Merge two saved filters into one"""
	try:
		if not primary_filter or not secondary_filter:
			frappe.throw(_("Both primary and secondary filter names are required"))
		
		if not merged_name:
			frappe.throw(_("Merged filter name is required"))
		
		from column_management.column_management.doctype.saved_filter.saved_filter import SavedFilter
		merged_filter = SavedFilter.merge_filters(primary_filter, secondary_filter, merged_name)
		
		return {
			"success": True,
			"data": {
				"merged_filter": merged_filter.name,
				"merged_name": merged_filter.filter_name,
				"doctype": merged_filter.doctype_name
			},
			"message": _("Filters merged successfully")
		}
		
	except Exception as e:
		frappe.log_error(f"Error merging filters: {str(e)}")
		return {
			"success": False,
			"data": None,
			"message": str(e)
		}

@frappe.whitelist()
def validate_filter_compatibility(filter_name, target_doctype):
	"""Validate if a filter can be applied to a different DocType"""
	try:
		if not filter_name:
			frappe.throw(_("Filter name is required"))
		
		if not target_doctype:
			frappe.throw(_("Target DocType is required"))
		
		from column_management.column_management.doctype.saved_filter.saved_filter import SavedFilter
		compatibility = SavedFilter.validate_filter_compatibility(filter_name, target_doctype)
		
		return {
			"success": True,
			"data": {
				"compatibility": compatibility,
				"filter_name": filter_name,
				"target_doctype": target_doctype
			},
			"message": _("Filter compatibility validated successfully")
		}
		
	except Exception as e:
		frappe.log_error(f"Error validating filter compatibility: {str(e)}")
		return {
			"success": False,
			"data": None,
			"message": str(e)
		}

@frappe.whitelist()
def update_filter_category(filter_name, category):
	"""Update the category of a saved filter"""
	try:
		if not filter_name:
			frappe.throw(_("Filter name is required"))
		
		filter_doc = frappe.get_doc("Saved Filter", filter_name)
		filter_doc.update_category(category)
		
		return {
			"success": True,
			"data": {
				"filter_name": filter_name,
				"new_category": category
			},
			"message": _("Filter category updated successfully")
		}
		
	except Exception as e:
		frappe.log_error(f"Error updating filter category: {str(e)}")
		return {
			"success": False,
			"data": None,
			"message": str(e)
		}

@frappe.whitelist()
def toggle_filter_public_status(filter_name):
	"""Toggle public/private status of a saved filter"""
	try:
		if not filter_name:
			frappe.throw(_("Filter name is required"))
		
		filter_doc = frappe.get_doc("Saved Filter", filter_name)
		new_status = filter_doc.toggle_public_status()
		
		return {
			"success": True,
			"data": {
				"filter_name": filter_name,
				"is_public": new_status
			},
			"message": _("Filter status updated successfully")
		}
		
	except Exception as e:
		frappe.log_error(f"Error toggling filter status: {str(e)}")
		return {
			"success": False,
			"data": None,
			"message": str(e)
		}

@frappe.whitelist()
def set_default_filter(filter_name):
	"""Set a saved filter as default for the user"""
	try:
		if not filter_name:
			frappe.throw(_("Filter name is required"))
		
		filter_doc = frappe.get_doc("Saved Filter", filter_name)
		filter_doc.set_as_default()
		
		return {
			"success": True,
			"data": {
				"filter_name": filter_name,
				"is_default": True
			},
			"message": _("Default filter set successfully")
		}
		
	except Exception as e:
		frappe.log_error(f"Error setting default filter: {str(e)}")
		return {
			"success": False,
			"data": None,
			"message": str(e)
		}

@frappe.whitelist()
def get_filter_summary(filter_name):
	"""Get a summary of a saved filter"""
	try:
		if not filter_name:
			frappe.throw(_("Filter name is required"))
		
		filter_doc = frappe.get_doc("Saved Filter", filter_name)
		
		# Check permissions
		if filter_doc.user != frappe.session.user and not filter_doc.is_public:
			frappe.throw(_("You don't have permission to view this filter"))
		
		summary = filter_doc.get_filter_summary()
		
		return {
			"success": True,
			"data": {
				"summary": summary,
				"filter_name": filter_name
			},
			"message": _("Filter summary retrieved successfully")
		}
		
	except Exception as e:
		frappe.log_error(f"Error getting filter summary: {str(e)}")
		return {
			"success": False,
			"data": None,
			"message": str(e)
		}

@frappe.whitelist()
def share_filter_with_users(filter_name, target_users):
	"""Share a filter with specific users"""
	try:
		if not filter_name:
			frappe.throw(_("Filter name is required"))
		
		if not target_users:
			frappe.throw(_("Target users are required"))
		
		if isinstance(target_users, str):
			target_users = json.loads(target_users)
		
		from column_management.column_management.doctype.saved_filter.saved_filter import SavedFilter
		shared_filters = SavedFilter.share_filter(filter_name, target_users)
		
		return {
			"success": True,
			"data": {
				"shared_filters": shared_filters,
				"target_users": target_users,
				"original_filter": filter_name
			},
			"message": _("Filter shared successfully with {0} users").format(len(target_users))
		}
		
	except Exception as e:
		frappe.log_error(f"Error sharing filter: {str(e)}")
		return {
			"success": False,
			"data": None,
			"message": str(e)
		}

@frappe.whitelist()
def bulk_filter_operations(operations):
	"""Perform bulk operations on multiple filters"""
	try:
		if not operations:
			frappe.throw(_("Operations are required"))
		
		if isinstance(operations, str):
			operations = json.loads(operations)
		
		results = []
		
		for operation in operations:
			op_type = operation.get("type")
			filter_name = operation.get("filter_name")
			
			try:
				if op_type == "delete":
					frappe.delete_doc("Saved Filter", filter_name, ignore_permissions=True)
					results.append({"filter_name": filter_name, "status": "deleted", "error": None})
				
				elif op_type == "toggle_public":
					filter_doc = frappe.get_doc("Saved Filter", filter_name)
					new_status = filter_doc.toggle_public_status()
					results.append({"filter_name": filter_name, "status": "toggled", "is_public": new_status, "error": None})
				
				elif op_type == "update_category":
					category = operation.get("category")
					filter_doc = frappe.get_doc("Saved Filter", filter_name)
					filter_doc.update_category(category)
					results.append({"filter_name": filter_name, "status": "category_updated", "category": category, "error": None})
				
				else:
					results.append({"filter_name": filter_name, "status": "error", "error": f"Unknown operation: {op_type}"})
			
			except Exception as e:
				results.append({"filter_name": filter_name, "status": "error", "error": str(e)})
		
		success_count = len([r for r in results if r["status"] != "error"])
		error_count = len([r for r in results if r["status"] == "error"])
		
		return {
			"success": True,
			"data": {
				"results": results,
				"summary": {
					"total_operations": len(operations),
					"successful": success_count,
					"failed": error_count
				}
			},
			"message": _("Bulk operations completed: {0} successful, {1} failed").format(success_count, error_count)
		}
		
	except Exception as e:
		frappe.log_error(f"Error performing bulk filter operations: {str(e)}")
		return {
			"success": False,
			"data": None,
			"message": str(e)
		}