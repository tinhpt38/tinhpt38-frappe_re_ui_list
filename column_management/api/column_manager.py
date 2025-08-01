# -*- coding: utf-8 -*-
# Copyright (c) 2024, ERPNext Column Management Team and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import json
from frappe import _
from column_management.column_management.services.column_service import ColumnService
from column_management.column_management.services.metadata_service import MetadataService

@frappe.whitelist()
def get_column_config(doctype, user=None):
	"""Get column configuration for a user and doctype"""
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
		
		# Check if user can access column management for this doctype
		if user != frappe.session.user and not frappe.has_permission("Column Config", "read"):
			frappe.throw(_("No permission to access column management"))
		
		# Get column configuration
		column_service = ColumnService()
		config = column_service.get_user_column_config(doctype, user)
		
		return {
			"success": True,
			"data": config,
			"message": _("Column configuration retrieved successfully")
		}
		
	except Exception as e:
		frappe.log_error(f"Error getting column config: {str(e)}")
		return {
			"success": False,
			"data": None,
			"message": str(e)
		}

@frappe.whitelist()
def save_column_config(doctype, config, user=None):
	"""Save column configuration for a user"""
	try:
		# Validate parameters
		if not doctype:
			frappe.throw(_("DocType is required"))
		
		if not config:
			frappe.throw(_("Configuration is required"))
		
		# Parse config if it's a string
		if isinstance(config, str):
			config = json.loads(config)
		
		# Use current user if not specified
		if not user:
			user = frappe.session.user
		
		# Check permissions
		if not frappe.has_permission(doctype, "read", user=user):
			frappe.throw(_("No permission to read {0}").format(doctype))
		
		# Check if user can modify column management
		if user != frappe.session.user and not frappe.has_permission("Column Config", "write"):
			frappe.throw(_("No permission to modify column management"))
		
		# Save column configuration
		column_service = ColumnService()
		result = column_service.save_user_column_config(doctype, user, config)
		
		if result:
			return {
				"success": True,
				"data": None,
				"message": _("Column configuration saved successfully")
			}
		else:
			return {
				"success": False,
				"data": None,
				"message": _("Failed to save column configuration")
			}
		
	except Exception as e:
		frappe.log_error(f"Error saving column config: {str(e)}")
		return {
			"success": False,
			"data": None,
			"message": str(e)
		}

@frappe.whitelist()
def get_doctype_fields(doctype):
	"""Get metadata of fields in a doctype"""
	try:
		# Validate parameters
		if not doctype:
			frappe.throw(_("DocType is required"))
		
		# Check permissions
		if not frappe.has_permission(doctype, "read"):
			frappe.throw(_("No permission to read {0}").format(doctype))
		
		# Get field metadata
		metadata_service = MetadataService()
		doctype_metadata = metadata_service.get_doctype_metadata(doctype)
		
		# Extract fields information
		fields_info = {
			"doctype": doctype,
			"fields": doctype_metadata.get("fields", []),
			"filterable_fields": metadata_service.get_filterable_fields(doctype),
			"sortable_fields": metadata_service.get_sortable_fields(doctype)
		}
		
		return {
			"success": True,
			"data": fields_info,
			"message": _("DocType fields retrieved successfully")
		}
		
	except Exception as e:
		frappe.log_error(f"Error getting doctype fields: {str(e)}")
		return {
			"success": False,
			"data": None,
			"message": str(e)
		}

@frappe.whitelist()
def reset_column_config(doctype, user=None):
	"""Reset column configuration to default"""
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
		
		# Check if user can modify column management
		if user != frappe.session.user and not frappe.has_permission("Column Config", "delete"):
			frappe.throw(_("No permission to reset column management"))
		
		# Reset column configuration
		column_service = ColumnService()
		config = column_service.reset_user_column_config(doctype, user)
		
		return {
			"success": True,
			"data": config,
			"message": _("Column configuration reset to default successfully")
		}
		
	except Exception as e:
		frappe.log_error(f"Error resetting column config: {str(e)}")
		return {
			"success": False,
			"data": None,
			"message": str(e)
		}

@frappe.whitelist()
def get_column_statistics(doctype):
	"""Get statistics about column usage"""
	try:
		# Validate parameters
		if not doctype:
			frappe.throw(_("DocType is required"))
		
		# Check permissions
		if not frappe.has_permission(doctype, "read"):
			frappe.throw(_("No permission to read {0}").format(doctype))
		
		# Check if user can access statistics
		if not frappe.has_permission("Column Config", "read"):
			frappe.throw(_("No permission to access column statistics"))
		
		# Get column statistics
		column_service = ColumnService()
		stats = column_service.get_column_statistics(doctype)
		
		return {
			"success": True,
			"data": {
				"doctype": doctype,
				"statistics": stats
			},
			"message": _("Column statistics retrieved successfully")
		}
		
	except Exception as e:
		frappe.log_error(f"Error getting column statistics: {str(e)}")
		return {
			"success": False,
			"data": None,
			"message": str(e)
		}

@frappe.whitelist()
def get_field_options(doctype, fieldname):
	"""Get options for a specific field (for Link/Select fields)"""
	try:
		# Validate parameters
		if not doctype:
			frappe.throw(_("DocType is required"))
		
		if not fieldname:
			frappe.throw(_("Field name is required"))
		
		# Check permissions
		if not frappe.has_permission(doctype, "read"):
			frappe.throw(_("No permission to read {0}").format(doctype))
		
		# Get field options
		metadata_service = MetadataService()
		options = metadata_service.get_link_field_options(doctype, fieldname)
		
		return {
			"success": True,
			"data": {
				"doctype": doctype,
				"fieldname": fieldname,
				"options": options
			},
			"message": _("Field options retrieved successfully")
		}
		
	except Exception as e:
		frappe.log_error(f"Error getting field options: {str(e)}")
		return {
			"success": False,
			"data": None,
			"message": str(e)
		}

@frappe.whitelist()
def validate_column_config(doctype, config):
	"""Validate column configuration without saving"""
	try:
		# Validate parameters
		if not doctype:
			frappe.throw(_("DocType is required"))
		
		if not config:
			frappe.throw(_("Configuration is required"))
		
		# Parse config if it's a string
		if isinstance(config, str):
			config = json.loads(config)
		
		# Check permissions
		if not frappe.has_permission(doctype, "read"):
			frappe.throw(_("No permission to read {0}").format(doctype))
		
		# Validate column configuration
		column_service = ColumnService()
		column_service.validate_column_config(doctype, config)
		
		return {
			"success": True,
			"data": None,
			"message": _("Column configuration is valid")
		}
		
	except Exception as e:
		frappe.log_error(f"Error validating column config: {str(e)}")
		return {
			"success": False,
			"data": None,
			"message": str(e)
		}

@frappe.whitelist()
def copy_column_config(source_doctype, target_doctype, user=None):
	"""Copy column configuration from one doctype to another"""
	try:
		# Validate parameters
		if not source_doctype or not target_doctype:
			frappe.throw(_("Source and target DocTypes are required"))
		
		# Use current user if not specified
		if not user:
			user = frappe.session.user
		
		# Check permissions
		if not frappe.has_permission(source_doctype, "read", user=user):
			frappe.throw(_("No permission to read {0}").format(source_doctype))
		
		if not frappe.has_permission(target_doctype, "read", user=user):
			frappe.throw(_("No permission to read {0}").format(target_doctype))
		
		# Check if user can modify column management
		if user != frappe.session.user and not frappe.has_permission("Column Config", "write"):
			frappe.throw(_("No permission to modify column management"))
		
		# Get source configuration
		column_service = ColumnService()
		source_config = column_service.get_user_column_config(source_doctype, user)
		
		# Get target doctype fields to validate compatibility
		target_fields = column_service.get_default_columns(target_doctype)
		target_fieldnames = {field["fieldname"] for field in target_fields}
		
		# Filter source columns to only include fields that exist in target
		compatible_columns = []
		for column in source_config.get("columns", []):
			if column["fieldname"] in target_fieldnames:
				compatible_columns.append(column)
		
		if not compatible_columns:
			frappe.throw(_("No compatible fields found between source and target DocTypes"))
		
		# Create target configuration
		target_config = {
			"doctype": target_doctype,
			"user": user,
			"columns": compatible_columns
		}
		
		# Save target configuration
		result = column_service.save_user_column_config(target_doctype, user, target_config)
		
		if result:
			return {
				"success": True,
				"data": {
					"copied_fields": len(compatible_columns),
					"total_source_fields": len(source_config.get("columns", []))
				},
				"message": _("Column configuration copied successfully. {0} compatible fields copied.").format(len(compatible_columns))
			}
		else:
			return {
				"success": False,
				"data": None,
				"message": _("Failed to copy column configuration")
			}
		
	except Exception as e:
		frappe.log_error(f"Error copying column config: {str(e)}")
		return {
			"success": False,
			"data": None,
			"message": str(e)
		}

@frappe.whitelist()
def save_column_width(doctype, fieldname, width, user=None):
	"""Save column width for a specific field"""
	try:
		# Validate parameters
		if not doctype:
			frappe.throw(_("DocType is required"))
		
		if not fieldname:
			frappe.throw(_("Field name is required"))
		
		if not width:
			frappe.throw(_("Width is required"))
		
		# Use current user if not specified
		if not user:
			user = frappe.session.user
		
		# Check permissions
		if not frappe.has_permission(doctype, "read", user=user):
			frappe.throw(_("No permission to read {0}").format(doctype))
		
		# Check if user can modify column management
		if user != frappe.session.user and not frappe.has_permission("Column Config", "write"):
			frappe.throw(_("No permission to modify column management"))
		
		# Save column width
		column_service = ColumnService()
		result = column_service.save_column_width(doctype, user, fieldname, int(width))
		
		if result:
			return {
				"success": True,
				"data": {
					"fieldname": fieldname,
					"width": int(width)
				},
				"message": _("Column width saved successfully")
			}
		else:
			return {
				"success": False,
				"data": None,
				"message": _("Failed to save column width")
			}
		
	except Exception as e:
		frappe.log_error(f"Error saving column width: {str(e)}")
		return {
			"success": False,
			"data": None,
			"message": str(e)
		}

@frappe.whitelist()
def save_multiple_column_widths(doctype, width_data, user=None):
	"""Save multiple column widths at once"""
	try:
		# Validate parameters
		if not doctype:
			frappe.throw(_("DocType is required"))
		
		if not width_data:
			frappe.throw(_("Width data is required"))
		
		# Parse width_data if it's a string
		if isinstance(width_data, str):
			width_data = json.loads(width_data)
		
		# Use current user if not specified
		if not user:
			user = frappe.session.user
		
		# Check permissions
		if not frappe.has_permission(doctype, "read", user=user):
			frappe.throw(_("No permission to read {0}").format(doctype))
		
		# Check if user can modify column management
		if user != frappe.session.user and not frappe.has_permission("Column Config", "write"):
			frappe.throw(_("No permission to modify column management"))
		
		# Save multiple column widths
		column_service = ColumnService()
		result = column_service.save_multiple_column_widths(doctype, user, width_data)
		
		if result:
			return {
				"success": True,
				"data": {
					"updated_fields": list(width_data.keys()),
					"field_count": len(width_data)
				},
				"message": _("Column widths saved successfully")
			}
		else:
			return {
				"success": False,
				"data": None,
				"message": _("Failed to save column widths")
			}
		
	except Exception as e:
		frappe.log_error(f"Error saving multiple column widths: {str(e)}")
		return {
			"success": False,
			"data": None,
			"message": str(e)
		}

@frappe.whitelist()
def get_column_width(doctype, fieldname, user=None):
	"""Get saved column width for a specific field"""
	try:
		# Validate parameters
		if not doctype:
			frappe.throw(_("DocType is required"))
		
		if not fieldname:
			frappe.throw(_("Field name is required"))
		
		# Use current user if not specified
		if not user:
			user = frappe.session.user
		
		# Check permissions
		if not frappe.has_permission(doctype, "read", user=user):
			frappe.throw(_("No permission to read {0}").format(doctype))
		
		# Get column width
		column_service = ColumnService()
		width = column_service.get_column_width(doctype, user, fieldname)
		
		return {
			"success": True,
			"data": {
				"fieldname": fieldname,
				"width": width
			},
			"message": _("Column width retrieved successfully")
		}
		
	except Exception as e:
		frappe.log_error(f"Error getting column width: {str(e)}")
		return {
			"success": False,
			"data": None,
			"message": str(e)
		}

@frappe.whitelist()
def get_all_column_widths(doctype, user=None):
	"""Get all saved column widths for a user and doctype"""
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
		
		# Get all column widths
		column_service = ColumnService()
		width_data = column_service.get_all_column_widths(doctype, user)
		
		return {
			"success": True,
			"data": {
				"doctype": doctype,
				"column_widths": width_data,
				"field_count": len(width_data)
			},
			"message": _("Column widths retrieved successfully")
		}
		
	except Exception as e:
		frappe.log_error(f"Error getting all column widths: {str(e)}")
		return {
			"success": False,
			"data": None,
			"message": str(e)
		}

@frappe.whitelist()
def restore_column_widths(doctype, user=None):
	"""Restore column widths when loading list views"""
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
		
		# Restore column widths
		column_service = ColumnService()
		width_data = column_service.restore_column_widths(doctype, user)
		
		return {
			"success": True,
			"data": {
				"doctype": doctype,
				"column_widths": width_data,
				"restored_fields": list(width_data.keys())
			},
			"message": _("Column widths restored successfully")
		}
		
	except Exception as e:
		frappe.log_error(f"Error restoring column widths: {str(e)}")
		return {
			"success": False,
			"data": None,
			"message": str(e)
		}

@frappe.whitelist()
def calculate_default_width(doctype, fieldname):
	"""Calculate default width for a new column"""
	try:
		# Validate parameters
		if not doctype:
			frappe.throw(_("DocType is required"))
		
		if not fieldname:
			frappe.throw(_("Field name is required"))
		
		# Check permissions
		if not frappe.has_permission(doctype, "read"):
			frappe.throw(_("No permission to read {0}").format(doctype))
		
		# Calculate default width
		column_service = ColumnService()
		width = column_service._calculate_default_width(doctype, fieldname)
		
		return {
			"success": True,
			"data": {
				"fieldname": fieldname,
				"default_width": width
			},
			"message": _("Default width calculated successfully")
		}
		
	except Exception as e:
		frappe.log_error(f"Error calculating default width: {str(e)}")
		return {
			"success": False,
			"data": None,
			"message": str(e)
		}

@frappe.whitelist()
def get_user_doctypes():
	"""Get list of DocTypes that user has access to"""
	try:
		# Get all DocTypes
		metadata_service = MetadataService()
		all_doctypes = metadata_service.get_doctype_list()
		
		# Filter by user permissions
		accessible_doctypes = []
		for doctype_info in all_doctypes:
			doctype = doctype_info["name"]
			if frappe.has_permission(doctype, "read"):
				accessible_doctypes.append(doctype_info)
		
		return {
			"success": True,
			"data": {
				"doctypes": accessible_doctypes,
				"total_count": len(accessible_doctypes)
			},
			"message": _("Accessible DocTypes retrieved successfully")
		}
		
	except Exception as e:
		frappe.log_error(f"Error getting user doctypes: {str(e)}")
		return {
			"success": False,
			"data": None,
			"message": str(e)
		}