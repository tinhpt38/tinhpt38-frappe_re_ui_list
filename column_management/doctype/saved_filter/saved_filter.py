# -*- coding: utf-8 -*-
# Copyright (c) 2024, ERPNext Column Management Team and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import json
from frappe.model.document import Document
from frappe import _

class SavedFilter(Document):
	def validate(self):
		"""Validate saved filter data"""
		self.validate_doctype_exists()
		self.validate_unique_filter_name()
		self.validate_filter_config()
		self.validate_permissions()
		self.set_timestamps()
	
	def validate_doctype_exists(self):
		"""Validate that the DocType exists"""
		if not frappe.db.exists("DocType", self.doctype_name):
			frappe.throw(_("DocType {0} does not exist").format(self.doctype_name))
	
	def validate_unique_filter_name(self):
		"""Ensure unique filter name per user and doctype"""
		existing = frappe.db.get_value("Saved Filter", {
			"user": self.user,
			"doctype_name": self.doctype_name,
			"filter_name": self.filter_name,
			"name": ["!=", self.name]
		})
		
		if existing:
			frappe.throw(_("Filter with name '{0}' already exists for {1} - {2}").format(
				self.filter_name, self.user, self.doctype_name))
	
	def validate_filter_config(self):
		"""Validate filter configuration structure"""
		if self.filter_config:
			try:
				if isinstance(self.filter_config, str):
					config = json.loads(self.filter_config)
				else:
					config = self.filter_config
				
				# Validate required structure
				if not isinstance(config, dict):
					frappe.throw(_("Filter configuration must be a valid JSON object"))
				
				# Validate filters structure if present
				if 'filters' in config:
					if not isinstance(config['filters'], list):
						frappe.throw(_("Filters must be a list"))
					
					for filter_item in config['filters']:
						if not isinstance(filter_item, dict):
							frappe.throw(_("Each filter must be a dictionary"))
						
						required_fields = ['fieldname', 'operator', 'value']
						for field in required_fields:
							if field not in filter_item:
								frappe.throw(_("Filter missing required field: {0}").format(field))
						
						# Validate field exists in DocType
						if self.doctype_name and filter_item['fieldname']:
							meta = frappe.get_meta(self.doctype_name)
							if not meta.get_field(filter_item['fieldname']):
								frappe.throw(_("Field {0} does not exist in DocType {1}").format(
									filter_item['fieldname'], self.doctype_name))
			
			except json.JSONDecodeError:
				frappe.throw(_("Invalid JSON format in filter configuration"))
	
	def validate_permissions(self):
		"""Validate user permissions for public filters"""
		if self.is_public:
			# Check if user has permission to create public filters
			if not frappe.has_permission(self.doctype_name, "write"):
				frappe.throw(_("You don't have permission to create public filters for {0}").format(
					self.doctype_name))
	
	def set_timestamps(self):
		"""Set created_at timestamp"""
		if self.is_new():
			self.created_at = frappe.utils.now()
	
	def before_save(self):
		"""Actions before saving the document"""
		# Serialize filter config if it's a dict
		if isinstance(self.filter_config, dict):
			self.filter_config = json.dumps(self.filter_config, indent=2)
		
		# Ensure only one default filter per user per doctype
		if self.is_default:
			frappe.db.sql("""
				UPDATE `tabSaved Filter` 
				SET is_default = 0 
				WHERE user = %s AND doctype_name = %s AND name != %s
			""", (self.user, self.doctype_name, self.name))
	
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
			from column_management.column_management.services.column_service import ColumnService
			service = ColumnService()
			service.clear_filter_cache(self.doctype_name, self.user)
		except ImportError:
			pass
	
	def get_filter_config(self):
		"""Get deserialized filter configuration"""
		if not self.filter_config:
			return {}
		
		try:
			if isinstance(self.filter_config, str):
				return json.loads(self.filter_config)
			else:
				return self.filter_config
		except json.JSONDecodeError:
			return {}
	
	def set_filter_config(self, config):
		"""Set filter configuration with validation"""
		if not isinstance(config, dict):
			frappe.throw(_("Filter configuration must be a dictionary"))
		
		self.filter_config = config
		self.validate_filter_config()
	
	@staticmethod
	def get_user_filters(user, doctype_name, include_public=True):
		"""Get saved filters for a user and doctype"""
		filters = {"doctype_name": doctype_name}
		
		if include_public:
			filters = [
				["doctype_name", "=", doctype_name],
				["or", [
					["user", "=", user],
					["is_public", "=", 1]
				]]
			]
		else:
			filters["user"] = user
		
		return frappe.get_all("Saved Filter",
			filters=filters,
			fields=["name", "filter_name", "description", "is_public", "is_default", "user"],
			order_by="is_default desc, filter_name asc"
		)
	
	@staticmethod
	def get_default_filter(user, doctype_name):
		"""Get default filter for user and doctype"""
		return frappe.db.get_value("Saved Filter", {
			"user": user,
			"doctype_name": doctype_name,
			"is_default": 1
		}, ["name", "filter_config"], as_dict=True)
	
	@staticmethod
	def create_filter(user, doctype_name, filter_name, filter_config, description=None, is_public=False, is_default=False):
		"""Create a new saved filter"""
		doc = frappe.get_doc({
			"doctype": "Saved Filter",
			"user": user,
			"doctype_name": doctype_name,
			"filter_name": filter_name,
			"filter_config": filter_config,
			"description": description,
			"is_public": is_public,
			"is_default": is_default
		})
		doc.insert(ignore_permissions=True)
		return doc
	
	@staticmethod
	def share_filter(filter_name, target_users):
		"""Share a filter with other users by creating copies"""
		original = frappe.get_doc("Saved Filter", filter_name)
		
		if not original.is_public:
			frappe.throw(_("Only public filters can be shared"))
		
		shared_filters = []
		for user in target_users:
			if user != original.user:
				# Create a copy for the target user
				copy_doc = frappe.get_doc({
					"doctype": "Saved Filter",
					"user": user,
					"doctype_name": original.doctype_name,
					"filter_name": f"{original.filter_name} (Shared)",
					"filter_config": original.filter_config,
					"description": f"Shared from {original.user}: {original.description or ''}",
					"is_public": False,
					"is_default": False
				})
				copy_doc.insert(ignore_permissions=True)
				shared_filters.append(copy_doc.name)
		
		return shared_filters
		# Enhanced Saved Filter Management - Task 10.3
	
	@staticmethod
	def get_filter_categories(user, doctype_name):
		"""Get filter categories for organization"""
		filters = frappe.get_all("Saved Filter",
			filters={
				"doctype_name": doctype_name,
				"or": [
					["user", "=", user],
					["is_public", "=", 1]
				]
			},
			fields=["category"],
			distinct=True
		)
		
		categories = [f.category for f in filters if f.category]
		return sorted(list(set(categories)))
	
	@staticmethod
	def organize_filters_by_category(user, doctype_name):
		"""Organize filters by category for better management"""
		filters = frappe.get_all("Saved Filter",
			filters={
				"doctype_name": doctype_name,
				"or": [
					["user", "=", user],
					["is_public", "=", 1]
				]
			},
			fields=["name", "filter_name", "description", "category", "is_public", "is_default", "user", "creation", "modified"],
			order_by="category asc, filter_name asc"
		)
		
		organized = {
			"uncategorized": [],
			"categories": {}
		}
		
		for filter_doc in filters:
			category = filter_doc.get("category")
			if category:
				if category not in organized["categories"]:
					organized["categories"][category] = []
				organized["categories"][category].append(filter_doc)
			else:
				organized["uncategorized"].append(filter_doc)
		
		return organized
	
	@staticmethod
	def duplicate_filter(filter_name, new_name, user=None):
		"""Duplicate an existing filter"""
		original = frappe.get_doc("Saved Filter", filter_name)
		
		# Use original user if not specified
		if not user:
			user = original.user
		
		# Check permissions
		if original.user != frappe.session.user and not original.is_public:
			frappe.throw(_("You don't have permission to duplicate this filter"))
		
		# Create duplicate
		duplicate = frappe.get_doc({
			"doctype": "Saved Filter",
			"user": user,
			"doctype_name": original.doctype_name,
			"filter_name": new_name,
			"filter_config": original.filter_config,
			"description": f"Copy of: {original.description or original.filter_name}",
			"category": original.category,
			"is_public": False,  # Duplicates are private by default
			"is_default": False
		})
		duplicate.insert(ignore_permissions=True)
		return duplicate
	
	@staticmethod
	def export_filter(filter_name):
		"""Export filter configuration for sharing"""
		filter_doc = frappe.get_doc("Saved Filter", filter_name)
		
		# Check permissions
		if filter_doc.user != frappe.session.user and not filter_doc.is_public:
			frappe.throw(_("You don't have permission to export this filter"))
		
		export_data = {
			"filter_name": filter_doc.filter_name,
			"doctype_name": filter_doc.doctype_name,
			"filter_config": filter_doc.get_filter_config(),
			"description": filter_doc.description,
			"category": filter_doc.category,
			"exported_by": frappe.session.user,
			"exported_at": frappe.utils.now(),
			"version": "1.0"
		}
		
		return export_data
	
	@staticmethod
	def import_filter(import_data, user=None):
		"""Import filter configuration from export data"""
		if not user:
			user = frappe.session.user
		
		# Validate import data
		required_fields = ["filter_name", "doctype_name", "filter_config"]
		for field in required_fields:
			if field not in import_data:
				frappe.throw(_("Import data missing required field: {0}").format(field))
		
		# Check if DocType exists
		if not frappe.db.exists("DocType", import_data["doctype_name"]):
			frappe.throw(_("DocType {0} does not exist").format(import_data["doctype_name"]))
		
		# Check for name conflicts
		existing = frappe.db.exists("Saved Filter", {
			"user": user,
			"doctype_name": import_data["doctype_name"],
			"filter_name": import_data["filter_name"]
		})
		
		filter_name = import_data["filter_name"]
		if existing:
			# Generate unique name
			counter = 1
			while existing:
				filter_name = f"{import_data['filter_name']} ({counter})"
				existing = frappe.db.exists("Saved Filter", {
					"user": user,
					"doctype_name": import_data["doctype_name"],
					"filter_name": filter_name
				})
				counter += 1
		
		# Create imported filter
		imported_filter = frappe.get_doc({
			"doctype": "Saved Filter",
			"user": user,
			"doctype_name": import_data["doctype_name"],
			"filter_name": filter_name,
			"filter_config": import_data["filter_config"],
			"description": f"Imported: {import_data.get('description', '')}",
			"category": import_data.get("category"),
			"is_public": False,
			"is_default": False
		})
		imported_filter.insert(ignore_permissions=True)
		return imported_filter
	
	@staticmethod
	def get_filter_usage_stats(user, doctype_name):
		"""Get usage statistics for saved filters"""
		# This would require tracking usage in a separate table
		# For now, return basic stats
		filters = frappe.get_all("Saved Filter",
			filters={
				"doctype_name": doctype_name,
				"or": [
					["user", "=", user],
					["is_public", "=", 1]
				]
			},
			fields=["name", "filter_name", "user", "is_public", "creation", "modified"]
		)
		
		stats = {
			"total_filters": len(filters),
			"personal_filters": len([f for f in filters if f.user == user]),
			"public_filters": len([f for f in filters if f.is_public]),
			"recent_filters": sorted(filters, key=lambda x: x.modified, reverse=True)[:5]
		}
		
		return stats
	
	@staticmethod
	def cleanup_unused_filters(user, doctype_name, days_old=90):
		"""Clean up old unused filters"""
		cutoff_date = frappe.utils.add_days(frappe.utils.now(), -days_old)
		
		old_filters = frappe.get_all("Saved Filter",
			filters={
				"user": user,
				"doctype_name": doctype_name,
				"is_default": 0,
				"modified": ["<", cutoff_date]
			},
			fields=["name", "filter_name"]
		)
		
		deleted_count = 0
		for filter_doc in old_filters:
			try:
				frappe.delete_doc("Saved Filter", filter_doc.name, ignore_permissions=True)
				deleted_count += 1
			except:
				continue
		
		return {
			"deleted_count": deleted_count,
			"total_checked": len(old_filters)
		}
	
	@staticmethod
	def merge_filters(primary_filter_name, secondary_filter_name, merged_name):
		"""Merge two filters into one"""
		primary = frappe.get_doc("Saved Filter", primary_filter_name)
		secondary = frappe.get_doc("Saved Filter", secondary_filter_name)
		
		# Check permissions
		if primary.user != frappe.session.user or secondary.user != frappe.session.user:
			frappe.throw(_("You can only merge your own filters"))
		
		if primary.doctype_name != secondary.doctype_name:
			frappe.throw(_("Cannot merge filters from different DocTypes"))
		
		# Merge filter configurations
		primary_config = primary.get_filter_config()
		secondary_config = secondary.get_filter_config()
		
		merged_config = {
			"filters": primary_config.get("filters", []) + secondary_config.get("filters", []),
			"columns": primary_config.get("columns") or secondary_config.get("columns"),
			"sort_by": primary_config.get("sort_by") or secondary_config.get("sort_by"),
			"sort_order": primary_config.get("sort_order") or secondary_config.get("sort_order")
		}
		
		# Create merged filter
		merged_filter = frappe.get_doc({
			"doctype": "Saved Filter",
			"user": primary.user,
			"doctype_name": primary.doctype_name,
			"filter_name": merged_name,
			"filter_config": merged_config,
			"description": f"Merged from: {primary.filter_name} + {secondary.filter_name}",
			"category": primary.category or secondary.category,
			"is_public": False,
			"is_default": False
		})
		merged_filter.insert(ignore_permissions=True)
		
		return merged_filter
	
	@staticmethod
	def validate_filter_compatibility(filter_name, target_doctype):
		"""Validate if a filter can be applied to a different DocType"""
		filter_doc = frappe.get_doc("Saved Filter", filter_name)
		filter_config = filter_doc.get_filter_config()
		
		if not filter_config.get("filters"):
			return {"compatible": True, "issues": []}
		
		target_meta = frappe.get_meta(target_doctype)
		target_fields = {field.fieldname: field for field in target_meta.fields}
		
		issues = []
		compatible_filters = []
		
		for filter_condition in filter_config["filters"]:
			fieldname = filter_condition.get("fieldname")
			
			if fieldname not in target_fields:
				issues.append(f"Field '{fieldname}' does not exist in {target_doctype}")
			else:
				target_field = target_fields[fieldname]
				source_meta = frappe.get_meta(filter_doc.doctype_name)
				source_field = source_meta.get_field(fieldname)
				
				if source_field and target_field.fieldtype != source_field.fieldtype:
					issues.append(f"Field '{fieldname}' has different type in {target_doctype}")
				else:
					compatible_filters.append(filter_condition)
		
		return {
			"compatible": len(issues) == 0,
			"issues": issues,
			"compatible_filters": compatible_filters,
			"compatibility_score": len(compatible_filters) / len(filter_config["filters"]) * 100
		}
	
	def get_sharing_permissions(self):
		"""Get sharing permissions for the filter"""
		if not self.is_public:
			return {"can_share": False, "reason": "Filter is not public"}
		
		if self.user != frappe.session.user:
			return {"can_share": False, "reason": "You are not the owner"}
		
		return {"can_share": True, "reason": ""}
	
	def update_category(self, new_category):
		"""Update filter category"""
		if self.user != frappe.session.user and not frappe.has_permission("Saved Filter", "write"):
			frappe.throw(_("You don't have permission to update this filter"))
		
		self.category = new_category
		self.save(ignore_permissions=True)
	
	def toggle_public_status(self):
		"""Toggle public/private status of the filter"""
		if self.user != frappe.session.user:
			frappe.throw(_("You can only change the status of your own filters"))
		
		# Check permissions for making public
		if not self.is_public and not frappe.has_permission(self.doctype_name, "write"):
			frappe.throw(_("You don't have permission to make this filter public"))
		
		self.is_public = not self.is_public
		self.save(ignore_permissions=True)
		
		return self.is_public
	
	def set_as_default(self):
		"""Set this filter as default for the user"""
		if self.user != frappe.session.user:
			frappe.throw(_("You can only set your own filters as default"))
		
		# Remove default from other filters
		frappe.db.sql("""
			UPDATE `tabSaved Filter` 
			SET is_default = 0 
			WHERE user = %s AND doctype_name = %s AND name != %s
		""", (self.user, self.doctype_name, self.name))
		
		self.is_default = 1
		self.save(ignore_permissions=True)
	
	def get_filter_summary(self):
		"""Get a summary of the filter for display"""
		config = self.get_filter_config()
		filters = config.get("filters", [])
		
		summary = {
			"name": self.filter_name,
			"description": self.description,
			"condition_count": len(filters),
			"conditions": [],
			"has_sorting": bool(config.get("sort_by")),
			"sort_info": {
				"field": config.get("sort_by"),
				"order": config.get("sort_order", "asc")
			} if config.get("sort_by") else None
		}
		
		# Summarize conditions
		for condition in filters[:3]:  # Show first 3 conditions
			fieldname = condition.get("fieldname", "")
			operator = condition.get("operator", "")
			value = condition.get("value", "")
			
			# Truncate long values
			if isinstance(value, str) and len(value) > 20:
				value = value[:17] + "..."
			
			summary["conditions"].append({
				"field": fieldname,
				"operator": operator,
				"value": value,
				"logic": condition.get("logic", "AND")
			})
		
		if len(filters) > 3:
			summary["conditions"].append({
				"field": "...",
				"operator": "",
				"value": f"and {len(filters) - 3} more",
				"logic": ""
			})
		
		return summary