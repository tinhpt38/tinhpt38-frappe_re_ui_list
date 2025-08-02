# -*- coding: utf-8 -*-
# Copyright (c) 2024, ERPNext Column Management Team and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import json
from frappe import _
from frappe.utils import now, get_datetime

class PreferenceService:
	"""Service for managing user preferences with automatic saving and loading"""
	
	def __init__(self):
		self.cache = frappe.cache()
		self.cache_prefix = "column_management_prefs"
		self.cache_ttl = 3600  # 1 hour
		self.auto_save_enabled = True
		self.auto_save_delay = 2  # seconds
	
	def get_user_preferences(self, user, doctype_name):
		"""Get comprehensive user preferences for a doctype"""
		cache_key = f"{self.cache_prefix}:user:{user}:{doctype_name}"
		
		# Try cache first
		cached_prefs = self.cache.get(cache_key)
		if cached_prefs:
			return json.loads(cached_prefs)
		
		# Get from database
		preferences = self._fetch_user_preferences(user, doctype_name)
		
		# Cache the result
		self.cache.set(cache_key, json.dumps(preferences), expire=self.cache_ttl)
		
		return preferences
	
	def _fetch_user_preferences(self, user, doctype_name):
		"""Fetch user preferences from database"""
		try:
			from column_management.column_management.doctype.user_column_preference.user_column_preference import UserColumnPreference
			
			# Get user preference document
			pref_data = UserColumnPreference.get_user_preference(user, doctype_name)
			
			if not pref_data:
				# Create default preferences
				pref_data = self._create_default_preferences(user, doctype_name)
			
			# Ensure all required sections exist
			default_structure = {
				"columns": {},
				"filters": {},
				"pagination": {},
				"sorting": {},
				"view_settings": {},
				"last_updated": now(),
				"version": "1.0"
			}
			
			# Merge with defaults
			for key, default_value in default_structure.items():
				if key not in pref_data:
					pref_data[key] = default_value
			
			return pref_data
			
		except Exception as e:
			frappe.log_error(f"Error fetching user preferences: {str(e)}")
			return self._create_default_preferences(user, doctype_name)
	
	def _create_default_preferences(self, user, doctype_name):
		"""Create default preferences for a user and doctype"""
		try:
			# Get column service for default column configuration
			from column_management.column_management.services.column_service import ColumnService
			column_service = ColumnService()
			
			# Get default column configuration
			default_columns = column_service.get_default_columns(doctype_name)
			
			# Create column preferences from defaults
			column_prefs = {}
			for field in default_columns:
				if field.get("in_list_view"):
					column_prefs[field["fieldname"]] = {
						"visible": True,
						"width": field.get("width", 140),
						"order": field.get("idx", 0),
						"pinned": None,
						"label": field.get("label", field["fieldname"].replace("_", " ").title())
					}
			
			# Create default preferences structure
			default_prefs = {
				"columns": column_prefs,
				"filters": {
					"active_filters": [],
					"saved_filters": [],
					"quick_filters": {}
				},
				"pagination": {
					"page_size": 20,
					"current_page": 1
				},
				"sorting": {
					"field": "modified",
					"order": "desc"
				},
				"view_settings": {
					"show_statistics": True,
					"compact_view": False,
					"auto_refresh": False,
					"refresh_interval": 30
				},
				"last_updated": now(),
				"version": "1.0"
			}
			
			return default_prefs
			
		except Exception as e:
			frappe.log_error(f"Error creating default preferences: {str(e)}")
			return {
				"columns": {},
				"filters": {},
				"pagination": {"page_size": 20, "current_page": 1},
				"sorting": {"field": "modified", "order": "desc"},
				"view_settings": {},
				"last_updated": now(),
				"version": "1.0"
			}
	
	def save_user_preferences(self, user, doctype_name, preferences, auto_save=False):
		"""Save user preferences with validation"""
		try:
			# Validate preferences structure
			self._validate_preferences(preferences)
			
			# Update timestamp
			preferences["last_updated"] = now()
			
			# Save to database
			from column_management.column_management.doctype.user_column_preference.user_column_preference import UserColumnPreference
			UserColumnPreference.create_or_update_preference(user, doctype_name, preferences)
			
			# Update cache
			cache_key = f"{self.cache_prefix}:user:{user}:{doctype_name}"
			self.cache.set(cache_key, json.dumps(preferences), expire=self.cache_ttl)
			
			# Log auto-save if enabled
			if auto_save:
				frappe.logger().info(f"Auto-saved preferences for {user} - {doctype_name}")
			
			return True
			
		except Exception as e:
			frappe.log_error(f"Error saving user preferences: {str(e)}")
			if not auto_save:  # Don't throw errors for auto-save
				frappe.throw(_("Failed to save preferences: {0}").format(str(e)))
			return False
	
	def _validate_preferences(self, preferences):
		"""Validate preferences structure"""
		if not isinstance(preferences, dict):
			frappe.throw(_("Preferences must be a dictionary"))
		
		required_sections = ["columns", "filters", "pagination", "sorting", "view_settings"]
		for section in required_sections:
			if section not in preferences:
				frappe.throw(_("Missing required preference section: {0}").format(section))
		
		# Validate columns section
		if not isinstance(preferences["columns"], dict):
			frappe.throw(_("Columns preferences must be a dictionary"))
		
		# Validate each column preference
		for fieldname, column_pref in preferences["columns"].items():
			if not isinstance(column_pref, dict):
				frappe.throw(_("Column preference for {0} must be a dictionary").format(fieldname))
			
			# Check required fields
			required_fields = ["visible", "width", "order"]
			for field in required_fields:
				if field not in column_pref:
					frappe.throw(_("Column preference for {0} missing {1}").format(fieldname, field))
			
			# Validate width
			width = column_pref["width"]
			if not isinstance(width, (int, float)) or width < 50 or width > 1000:
				frappe.throw(_("Invalid width for column {0}: must be between 50 and 1000").format(fieldname))
	
	def update_column_preferences(self, user, doctype_name, column_updates):
		"""Update specific column preferences"""
		try:
			# Get current preferences
			current_prefs = self.get_user_preferences(user, doctype_name)
			
			# Update column preferences
			for fieldname, updates in column_updates.items():
				if fieldname not in current_prefs["columns"]:
					# Create new column preference
					current_prefs["columns"][fieldname] = {
						"visible": True,
						"width": 140,
						"order": 0,
						"pinned": None,
						"label": fieldname.replace("_", " ").title()
					}
				
				# Apply updates
				current_prefs["columns"][fieldname].update(updates)
			
			# Save updated preferences
			return self.save_user_preferences(user, doctype_name, current_prefs, auto_save=True)
			
		except Exception as e:
			frappe.log_error(f"Error updating column preferences: {str(e)}")
			return False
	
	def update_filter_preferences(self, user, doctype_name, filter_updates):
		"""Update filter preferences"""
		try:
			# Get current preferences
			current_prefs = self.get_user_preferences(user, doctype_name)
			
			# Update filter preferences
			current_prefs["filters"].update(filter_updates)
			
			# Save updated preferences
			return self.save_user_preferences(user, doctype_name, current_prefs, auto_save=True)
			
		except Exception as e:
			frappe.log_error(f"Error updating filter preferences: {str(e)}")
			return False
	
	def update_pagination_preferences(self, user, doctype_name, pagination_updates):
		"""Update pagination preferences"""
		try:
			# Get current preferences
			current_prefs = self.get_user_preferences(user, doctype_name)
			
			# Update pagination preferences
			current_prefs["pagination"].update(pagination_updates)
			
			# Save updated preferences
			return self.save_user_preferences(user, doctype_name, current_prefs, auto_save=True)
			
		except Exception as e:
			frappe.log_error(f"Error updating pagination preferences: {str(e)}")
			return False
	
	def update_sorting_preferences(self, user, doctype_name, sorting_updates):
		"""Update sorting preferences"""
		try:
			# Get current preferences
			current_prefs = self.get_user_preferences(user, doctype_name)
			
			# Update sorting preferences
			current_prefs["sorting"].update(sorting_updates)
			
			# Save updated preferences
			return self.save_user_preferences(user, doctype_name, current_prefs, auto_save=True)
			
		except Exception as e:
			frappe.log_error(f"Error updating sorting preferences: {str(e)}")
			return False
	
	def update_view_settings(self, user, doctype_name, view_updates):
		"""Update view settings preferences"""
		try:
			# Get current preferences
			current_prefs = self.get_user_preferences(user, doctype_name)
			
			# Update view settings
			current_prefs["view_settings"].update(view_updates)
			
			# Save updated preferences
			return self.save_user_preferences(user, doctype_name, current_prefs, auto_save=True)
			
		except Exception as e:
			frappe.log_error(f"Error updating view settings: {str(e)}")
			return False
	
	def restore_preferences_on_login(self, user):
		"""Restore user preferences when user logs in"""
		try:
			# Get all doctypes the user has preferences for
			user_prefs = frappe.get_all("User Column Preference",
				filters={"user": user},
				fields=["doctype_name", "preference_data", "modified_at"],
				order_by="modified_at desc"
			)
			
			restored_count = 0
			for pref in user_prefs:
				try:
					# Warm up cache with user preferences
					cache_key = f"{self.cache_prefix}:user:{user}:{pref.doctype_name}"
					self.cache.set(cache_key, pref.preference_data, expire=self.cache_ttl)
					restored_count += 1
				except Exception as e:
					frappe.log_error(f"Error restoring preference for {pref.doctype_name}: {str(e)}")
			
			frappe.logger().info(f"Restored {restored_count} preferences for user {user}")
			return restored_count
			
		except Exception as e:
			frappe.log_error(f"Error restoring preferences on login: {str(e)}")
			return 0
	
	def get_per_doctype_preferences(self, user, doctype_name):
		"""Get preferences specific to a doctype"""
		return self.get_user_preferences(user, doctype_name)
	
	def set_per_doctype_preferences(self, user, doctype_name, preferences):
		"""Set preferences specific to a doctype"""
		return self.save_user_preferences(user, doctype_name, preferences)
	
	def auto_save_preferences(self, user, doctype_name, preference_type, updates):
		"""Auto-save preferences with debouncing"""
		if not self.auto_save_enabled:
			return False
		
		try:
			# Create a unique key for debouncing
			debounce_key = f"auto_save:{user}:{doctype_name}:{preference_type}"
			
			# Check if we should debounce this save
			if self.cache.get(debounce_key):
				return False  # Skip this save, another one is pending
			
			# Set debounce flag
			self.cache.set(debounce_key, True, expire=self.auto_save_delay)
			
			# Perform the update based on preference type
			if preference_type == "columns":
				return self.update_column_preferences(user, doctype_name, updates)
			elif preference_type == "filters":
				return self.update_filter_preferences(user, doctype_name, updates)
			elif preference_type == "pagination":
				return self.update_pagination_preferences(user, doctype_name, updates)
			elif preference_type == "sorting":
				return self.update_sorting_preferences(user, doctype_name, updates)
			elif preference_type == "view_settings":
				return self.update_view_settings(user, doctype_name, updates)
			else:
				frappe.log_error(f"Unknown preference type: {preference_type}")
				return False
			
		except Exception as e:
			frappe.log_error(f"Error in auto-save preferences: {str(e)}")
			return False
	
	def clear_user_cache(self, user, doctype_name=None):
		"""Clear cached preferences for a user"""
		try:
			if doctype_name:
				# Clear specific doctype cache
				cache_key = f"{self.cache_prefix}:user:{user}:{doctype_name}"
				self.cache.delete(cache_key)
			else:
				# Clear all preferences for user (pattern-based deletion not supported, so we'll track keys)
				# For now, we'll just clear the entire cache namespace
				pass
			
		except Exception as e:
			frappe.log_error(f"Error clearing user cache: {str(e)}")
	
	def get_preference_history(self, user, doctype_name, limit=10):
		"""Get preference change history"""
		try:
			# Get preference document versions
			history = frappe.get_all("Version",
				filters={
					"ref_doctype": "User Column Preference",
					"docname": f"UCP-{user}-{doctype_name}"
				},
				fields=["creation", "data", "owner"],
				order_by="creation desc",
				limit=limit
			)
			
			return history
			
		except Exception as e:
			frappe.log_error(f"Error getting preference history: {str(e)}")
			return []
	
	def export_user_preferences(self, user, doctype_names=None):
		"""Export user preferences for backup"""
		try:
			filters = {"user": user}
			if doctype_names:
				filters["doctype_name"] = ["in", doctype_names]
			
			preferences = frappe.get_all("User Column Preference",
				filters=filters,
				fields=["doctype_name", "preference_data", "is_default", "created_at", "modified_at"]
			)
			
			export_data = {
				"user": user,
				"export_date": now(),
				"preferences": preferences
			}
			
			return export_data
			
		except Exception as e:
			frappe.log_error(f"Error exporting user preferences: {str(e)}")
			return None
	
	def import_user_preferences(self, user, import_data, overwrite=False):
		"""Import user preferences from backup"""
		try:
			if not isinstance(import_data, dict) or "preferences" not in import_data:
				frappe.throw(_("Invalid import data format"))
			
			imported_count = 0
			for pref_data in import_data["preferences"]:
				doctype_name = pref_data["doctype_name"]
				preference_data = pref_data["preference_data"]
				
				# Check if preference already exists
				existing = frappe.db.exists("User Column Preference", {
					"user": user,
					"doctype_name": doctype_name
				})
				
				if existing and not overwrite:
					continue  # Skip if exists and not overwriting
				
				# Create or update preference
				from column_management.column_management.doctype.user_column_preference.user_column_preference import UserColumnPreference
				UserColumnPreference.create_or_update_preference(
					user, doctype_name, preference_data, 
					is_default=pref_data.get("is_default", False)
				)
				
				# Clear cache
				self.clear_user_cache(user, doctype_name)
				
				imported_count += 1
			
			return imported_count
			
		except Exception as e:
			frappe.log_error(f"Error importing user preferences: {str(e)}")
			frappe.throw(_("Failed to import preferences: {0}").format(str(e)))
	
	def reset_to_defaults(self, user, doctype_name):
		"""Reset user preferences to default values"""
		try:
			# Delete existing preference
			existing = frappe.db.get_value("User Column Preference", {
				"user": user,
				"doctype_name": doctype_name
			})
			
			if existing:
				frappe.delete_doc("User Column Preference", existing, ignore_permissions=True)
			
			# Clear cache
			self.clear_user_cache(user, doctype_name)
			
			# Return new default preferences
			return self.get_user_preferences(user, doctype_name)
			
		except Exception as e:
			frappe.log_error(f"Error resetting preferences to defaults: {str(e)}")
			frappe.throw(_("Failed to reset preferences: {0}").format(str(e)))
	
	def get_preference_summary(self, user):
		"""Get summary of user's preferences across all doctypes"""
		try:
			summary = frappe.db.sql("""
				SELECT 
					doctype_name,
					is_default,
					created_at,
					modified_at,
					CHAR_LENGTH(preference_data) as data_size
				FROM `tabUser Column Preference`
				WHERE user = %s
				ORDER BY modified_at DESC
			""", (user,), as_dict=True)
			
			return summary
			
		except Exception as e:
			frappe.log_error(f"Error getting preference summary: {str(e)}")
			return []