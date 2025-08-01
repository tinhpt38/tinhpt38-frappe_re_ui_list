# -*- coding: utf-8 -*-
# Copyright (c) 2024, ERPNext Column Management Team and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import json
from frappe import _
from column_management.column_management.services.statistics_service import StatisticsService

@frappe.whitelist()
def get_statistics(doctype, filters=None, statistics_config=None, refresh_cache=False):
	"""Get statistics based on current filters"""
	try:
		# Validate parameters
		if not doctype:
			frappe.throw(_("DocType is required"))
		
		# Check permissions
		if not frappe.has_permission(doctype, "read"):
			frappe.throw(_("No permission to read {0}").format(doctype))
		
		# Parse parameters
		if isinstance(filters, str):
			filters = json.loads(filters) if filters else None
		
		if isinstance(statistics_config, str):
			statistics_config = json.loads(statistics_config) if statistics_config else None
		
		refresh_cache = bool(refresh_cache)
		
		# Get statistics
		statistics_service = StatisticsService()
		
		if filters:
			# Get filtered statistics
			stats = statistics_service.calculate_filtered_statistics(doctype, filters)
		else:
			# Get all statistics
			stats = statistics_service.get_real_time_statistics(doctype, refresh_cache=refresh_cache)
		
		return {
			"success": True,
			"data": {
				"doctype": doctype,
				"statistics": stats,
				"has_filters": bool(filters),
				"filter_count": len(filters) if filters else 0
			},
			"message": _("Statistics retrieved successfully")
		}
		
	except Exception as e:
		frappe.log_error(f"Error getting statistics: {str(e)}")
		return {
			"success": False,
			"data": None,
			"message": str(e)
		}

@frappe.whitelist()
def get_drill_down_statistics(doctype, statistic_name, drill_down_field, filters=None):
	"""Get drill-down statistics grouped by a specific field"""
	try:
		# Validate parameters
		if not doctype:
			frappe.throw(_("DocType is required"))
		
		if not statistic_name:
			frappe.throw(_("Statistic name is required"))
		
		if not drill_down_field:
			frappe.throw(_("Drill-down field is required"))
		
		# Check permissions
		if not frappe.has_permission(doctype, "read"):
			frappe.throw(_("No permission to read {0}").format(doctype))
		
		# Parse filters
		if isinstance(filters, str):
			filters = json.loads(filters) if filters else None
		
		# Get drill-down statistics
		statistics_service = StatisticsService()
		drill_down_data = statistics_service.calculate_drill_down_statistics(
			doctype, statistic_name, drill_down_field, filters
		)
		
		return {
			"success": True,
			"data": {
				"doctype": doctype,
				"statistic_name": statistic_name,
				"drill_down_field": drill_down_field,
				"drill_down_data": drill_down_data,
				"total_groups": len(drill_down_data)
			},
			"message": _("Drill-down statistics retrieved successfully")
		}
		
	except Exception as e:
		frappe.log_error(f"Error getting drill-down statistics: {str(e)}")
		return {
			"success": False,
			"data": None,
			"message": str(e)
		}

@frappe.whitelist()
def get_statistics_summary(doctype):
	"""Get a summary of available statistics for a DocType"""
	try:
		# Validate parameters
		if not doctype:
			frappe.throw(_("DocType is required"))
		
		# Check permissions
		if not frappe.has_permission(doctype, "read"):
			frappe.throw(_("No permission to read {0}").format(doctype))
		
		# Get statistics summary
		statistics_service = StatisticsService()
		summary = statistics_service.get_statistics_summary(doctype)
		
		return {
			"success": True,
			"data": summary,
			"message": _("Statistics summary retrieved successfully")
		}
		
	except Exception as e:
		frappe.log_error(f"Error getting statistics summary: {str(e)}")
		return {
			"success": False,
			"data": None,
			"message": str(e)
		}

@frappe.whitelist()
def refresh_statistics_cache(doctype):
	"""Refresh statistics cache for a DocType"""
	try:
		# Validate parameters
		if not doctype:
			frappe.throw(_("DocType is required"))
		
		# Check permissions
		if not frappe.has_permission(doctype, "read"):
			frappe.throw(_("No permission to read {0}").format(doctype))
		
		# Check if user can refresh cache (admin permission)
		if not frappe.has_permission("Statistics Config", "write"):
			frappe.throw(_("No permission to refresh statistics cache"))
		
		# Refresh cache
		statistics_service = StatisticsService()
		statistics_service.invalidate_statistics_cache(doctype)
		
		# Get fresh statistics
		fresh_stats = statistics_service.get_real_time_statistics(doctype, refresh_cache=True)
		
		return {
			"success": True,
			"data": {
				"doctype": doctype,
				"statistics": fresh_stats,
				"cache_refreshed": True
			},
			"message": _("Statistics cache refreshed successfully")
		}
		
	except Exception as e:
		frappe.log_error(f"Error refreshing statistics cache: {str(e)}")
		return {
			"success": False,
			"data": None,
			"message": str(e)
		}

@frappe.whitelist()
def create_statistics_config(doctype, statistic_name, field_name, calculation_type, format_string="Data", condition=None, description=None):
	"""Create a new statistics configuration"""
	try:
		# Validate parameters
		if not doctype:
			frappe.throw(_("DocType is required"))
		
		if not statistic_name:
			frappe.throw(_("Statistic name is required"))
		
		if not field_name:
			frappe.throw(_("Field name is required"))
		
		if not calculation_type:
			frappe.throw(_("Calculation type is required"))
		
		# Check permissions
		if not frappe.has_permission(doctype, "read"):
			frappe.throw(_("No permission to read {0}").format(doctype))
		
		if not frappe.has_permission("Statistics Config", "create"):
			frappe.throw(_("No permission to create statistics configuration"))
		
		# Create statistics configuration
		from column_management.column_management.doctype.statistics_config.statistics_config import StatisticsConfig
		
		config_doc = StatisticsConfig.create_default_config(
			doctype_name=doctype,
			statistic_name=statistic_name,
			field_name=field_name,
			calculation_type=calculation_type,
			format_string=format_string,
			condition=condition
		)
		
		if config_doc:
			# Add description if provided
			if description:
				config_doc.description = description
				config_doc.save(ignore_permissions=True)
			
			return {
				"success": True,
				"data": {
					"name": config_doc.name,
					"doctype": doctype,
					"statistic_name": statistic_name,
					"field_name": field_name,
					"calculation_type": calculation_type
				},
				"message": _("Statistics configuration created successfully")
			}
		else:
			return {
				"success": False,
				"data": None,
				"message": _("Statistics configuration already exists")
			}
		
	except Exception as e:
		frappe.log_error(f"Error creating statistics config: {str(e)}")
		return {
			"success": False,
			"data": None,
			"message": str(e)
		}

@frappe.whitelist()
def get_statistics_config(doctype):
	"""Get all statistics configurations for a DocType"""
	try:
		# Validate parameters
		if not doctype:
			frappe.throw(_("DocType is required"))
		
		# Check permissions
		if not frappe.has_permission(doctype, "read"):
			frappe.throw(_("No permission to read {0}").format(doctype))
		
		# Get statistics configurations
		from column_management.column_management.doctype.statistics_config.statistics_config import StatisticsConfig
		configs = StatisticsConfig.get_doctype_statistics(doctype, active_only=False)
		
		return {
			"success": True,
			"data": {
				"doctype": doctype,
				"configurations": configs,
				"total_count": len(configs)
			},
			"message": _("Statistics configurations retrieved successfully")
		}
		
	except Exception as e:
		frappe.log_error(f"Error getting statistics config: {str(e)}")
		return {
			"success": False,
			"data": None,
			"message": str(e)
		}

@frappe.whitelist()
def update_statistics_config(config_name, is_active=None, condition=None, description=None):
	"""Update an existing statistics configuration"""
	try:
		# Validate parameters
		if not config_name:
			frappe.throw(_("Configuration name is required"))
		
		# Check if config exists
		if not frappe.db.exists("Statistics Config", config_name):
			frappe.throw(_("Statistics configuration not found"))
		
		# Check permissions
		if not frappe.has_permission("Statistics Config", "write"):
			frappe.throw(_("No permission to update statistics configuration"))
		
		# Update configuration
		config_doc = frappe.get_doc("Statistics Config", config_name)
		
		if is_active is not None:
			config_doc.is_active = bool(is_active)
		
		if condition is not None:
			config_doc.condition = condition
		
		if description is not None:
			config_doc.description = description
		
		config_doc.save(ignore_permissions=True)
		
		return {
			"success": True,
			"data": {
				"name": config_doc.name,
				"is_active": config_doc.is_active,
				"condition": config_doc.condition,
				"description": config_doc.description
			},
			"message": _("Statistics configuration updated successfully")
		}
		
	except Exception as e:
		frappe.log_error(f"Error updating statistics config: {str(e)}")
		return {
			"success": False,
			"data": None,
			"message": str(e)
		}

@frappe.whitelist()
def delete_statistics_config(config_name):
	"""Delete a statistics configuration"""
	try:
		# Validate parameters
		if not config_name:
			frappe.throw(_("Configuration name is required"))
		
		# Check if config exists
		if not frappe.db.exists("Statistics Config", config_name):
			frappe.throw(_("Statistics configuration not found"))
		
		# Check permissions
		if not frappe.has_permission("Statistics Config", "delete"):
			frappe.throw(_("No permission to delete statistics configuration"))
		
		# Get config info before deletion
		config_doc = frappe.get_doc("Statistics Config", config_name)
		doctype_name = config_doc.doctype_name
		statistic_name = config_doc.statistic_name
		
		# Delete configuration
		frappe.delete_doc("Statistics Config", config_name, ignore_permissions=True)
		
		return {
			"success": True,
			"data": {
				"deleted_config": config_name,
				"doctype": doctype_name,
				"statistic_name": statistic_name
			},
			"message": _("Statistics configuration deleted successfully")
		}
		
	except Exception as e:
		frappe.log_error(f"Error deleting statistics config: {str(e)}")
		return {
			"success": False,
			"data": None,
			"message": str(e)
		}

@frappe.whitelist()
def calculate_custom_statistic(doctype, field_name, calculation_type, filters=None, condition=None):
	"""Calculate a custom statistic without saving configuration"""
	try:
		# Validate parameters
		if not doctype:
			frappe.throw(_("DocType is required"))
		
		if not field_name:
			frappe.throw(_("Field name is required"))
		
		if not calculation_type:
			frappe.throw(_("Calculation type is required"))
		
		# Check permissions
		if not frappe.has_permission(doctype, "read"):
			frappe.throw(_("No permission to read {0}").format(doctype))
		
		# Parse filters
		if isinstance(filters, str):
			filters = json.loads(filters) if filters else None
		
		# Create temporary statistics config
		temp_config = [{
			"name": "temp_config",
			"statistic_name": "Custom Calculation",
			"field_name": field_name,
			"calculation_type": calculation_type,
			"format_string": "Data",
			"condition": condition
		}]
		
		# Calculate statistics
		statistics_service = StatisticsService()
		
		if filters:
			# Convert filters to SQL conditions
			sql_conditions = statistics_service._convert_filters_to_sql(filters)
			if condition:
				sql_conditions.append(condition)
			result = statistics_service._calculate_from_database(doctype, temp_config, sql_conditions)
		else:
			additional_conditions = [condition] if condition else None
			result = statistics_service._calculate_from_database(doctype, temp_config, additional_conditions)
		
		custom_result = result.get("Custom Calculation", {})
		
		return {
			"success": True,
			"data": {
				"doctype": doctype,
				"field_name": field_name,
				"calculation_type": calculation_type,
				"value": custom_result.get("value", 0),
				"formatted_value": custom_result.get("formatted_value", "0"),
				"has_filters": bool(filters),
				"has_condition": bool(condition)
			},
			"message": _("Custom statistic calculated successfully")
		}
		
	except Exception as e:
		frappe.log_error(f"Error calculating custom statistic: {str(e)}")
		return {
			"success": False,
			"data": None,
			"message": str(e)
		}