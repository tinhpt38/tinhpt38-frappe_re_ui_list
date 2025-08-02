# -*- coding: utf-8 -*-
# Copyright (c) 2024, ERPNext Column Management Team and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import unittest
import frappe
import json
from frappe.utils import now

class TestPreferenceService(unittest.TestCase):
	"""Test cases for PreferenceService"""
	
	def setUp(self):
		"""Set up test data"""
		self.test_user = "test@example.com"
		self.test_doctype = "User"
		
		# Create test user if not exists
		if not frappe.db.exists("User", self.test_user):
			user_doc = frappe.get_doc({
				"doctype": "User",
				"email": self.test_user,
				"first_name": "Test",
				"last_name": "User",
				"send_welcome_email": 0
			})
			user_doc.insert(ignore_permissions=True)
		
		# Clean up any existing preferences
		frappe.db.delete("User Column Preference", {
			"user": self.test_user,
			"doctype_name": self.test_doctype
		})
		
		frappe.db.commit()
	
	def tearDown(self):
		"""Clean up test data"""
		# Clean up test preferences
		frappe.db.delete("User Column Preference", {
			"user": self.test_user,
			"doctype_name": self.test_doctype
		})
		
		frappe.db.commit()
	
	def test_get_user_preferences_default(self):
		"""Test getting default user preferences"""
		from column_management.column_management.services.preference_service import PreferenceService
		
		service = PreferenceService()
		preferences = service.get_user_preferences(self.test_user, self.test_doctype)
		
		# Check structure
		self.assertIsInstance(preferences, dict)
		self.assertIn("columns", preferences)
		self.assertIn("filters", preferences)
		self.assertIn("pagination", preferences)
		self.assertIn("sorting", preferences)
		self.assertIn("view_settings", preferences)
		self.assertIn("version", preferences)
		
		# Check default values
		self.assertEqual(preferences["pagination"]["page_size"], 20)
		self.assertEqual(preferences["sorting"]["field"], "modified")
		self.assertEqual(preferences["sorting"]["order"], "desc")
	
	def test_save_user_preferences(self):
		"""Test saving user preferences"""
		from column_management.column_management.services.preference_service import PreferenceService
		
		service = PreferenceService()
		
		# Create test preferences
		test_preferences = {
			"columns": {
				"name": {
					"visible": True,
					"width": 150,
					"order": 0,
					"pinned": None,
					"label": "ID"
				},
				"email": {
					"visible": True,
					"width": 200,
					"order": 1,
					"pinned": None,
					"label": "Email"
				}
			},
			"filters": {
				"active_filters": [
					{"fieldname": "enabled", "operator": "=", "value": 1}
				],
				"saved_filters": [],
				"quick_filters": {}
			},
			"pagination": {
				"page_size": 50,
				"current_page": 1
			},
			"sorting": {
				"field": "creation",
				"order": "asc"
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
		
		# Save preferences
		result = service.save_user_preferences(self.test_user, self.test_doctype, test_preferences)
		self.assertTrue(result)
		
		# Verify saved preferences
		saved_preferences = service.get_user_preferences(self.test_user, self.test_doctype)
		
		self.assertEqual(saved_preferences["pagination"]["page_size"], 50)
		self.assertEqual(saved_preferences["sorting"]["field"], "creation")
		self.assertEqual(saved_preferences["sorting"]["order"], "asc")
		self.assertEqual(saved_preferences["columns"]["name"]["width"], 150)
		self.assertEqual(saved_preferences["columns"]["email"]["width"], 200)
	
	def test_update_column_preferences(self):
		"""Test updating specific column preferences"""
		from column_management.column_management.services.preference_service import PreferenceService
		
		service = PreferenceService()
		
		# First get default preferences
		preferences = service.get_user_preferences(self.test_user, self.test_doctype)
		
		# Update column preferences
		column_updates = {
			"name": {
				"width": 180,
				"visible": True
			},
			"email": {
				"width": 250,
				"pinned": "left"
			}
		}
		
		result = service.update_column_preferences(self.test_user, self.test_doctype, column_updates)
		self.assertTrue(result)
		
		# Verify updates
		updated_preferences = service.get_user_preferences(self.test_user, self.test_doctype)
		
		self.assertEqual(updated_preferences["columns"]["name"]["width"], 180)
		self.assertEqual(updated_preferences["columns"]["email"]["width"], 250)
		self.assertEqual(updated_preferences["columns"]["email"]["pinned"], "left")
	
	def test_update_filter_preferences(self):
		"""Test updating filter preferences"""
		from column_management.column_management.services.preference_service import PreferenceService
		
		service = PreferenceService()
		
		# Update filter preferences
		filter_updates = {
			"active_filters": [
				{"fieldname": "enabled", "operator": "=", "value": 1},
				{"fieldname": "user_type", "operator": "=", "value": "System User"}
			]
		}
		
		result = service.update_filter_preferences(self.test_user, self.test_doctype, filter_updates)
		self.assertTrue(result)
		
		# Verify updates
		updated_preferences = service.get_user_preferences(self.test_user, self.test_doctype)
		
		self.assertEqual(len(updated_preferences["filters"]["active_filters"]), 2)
		self.assertEqual(updated_preferences["filters"]["active_filters"][0]["fieldname"], "enabled")
		self.assertEqual(updated_preferences["filters"]["active_filters"][1]["fieldname"], "user_type")
	
	def test_update_pagination_preferences(self):
		"""Test updating pagination preferences"""
		from column_management.column_management.services.preference_service import PreferenceService
		
		service = PreferenceService()
		
		# Update pagination preferences
		pagination_updates = {
			"page_size": 100,
			"current_page": 2
		}
		
		result = service.update_pagination_preferences(self.test_user, self.test_doctype, pagination_updates)
		self.assertTrue(result)
		
		# Verify updates
		updated_preferences = service.get_user_preferences(self.test_user, self.test_doctype)
		
		self.assertEqual(updated_preferences["pagination"]["page_size"], 100)
		self.assertEqual(updated_preferences["pagination"]["current_page"], 2)
	
	def test_auto_save_preferences(self):
		"""Test auto-save functionality"""
		from column_management.column_management.services.preference_service import PreferenceService
		
		service = PreferenceService()
		
		# Test auto-save for columns
		column_updates = {
			"name": {"width": 160}
		}
		
		result = service.auto_save_preferences(self.test_user, self.test_doctype, "columns", column_updates)
		self.assertTrue(result)
		
		# Verify auto-save worked
		preferences = service.get_user_preferences(self.test_user, self.test_doctype)
		self.assertEqual(preferences["columns"]["name"]["width"], 160)
	
	def test_reset_to_defaults(self):
		"""Test resetting preferences to defaults"""
		from column_management.column_management.services.preference_service import PreferenceService
		
		service = PreferenceService()
		
		# First save some custom preferences
		custom_preferences = {
			"columns": {
				"name": {"visible": True, "width": 300, "order": 0}
			},
			"filters": {"active_filters": []},
			"pagination": {"page_size": 100, "current_page": 1},
			"sorting": {"field": "name", "order": "asc"},
			"view_settings": {},
			"last_updated": now(),
			"version": "1.0"
		}
		
		service.save_user_preferences(self.test_user, self.test_doctype, custom_preferences)
		
		# Reset to defaults
		default_preferences = service.reset_to_defaults(self.test_user, self.test_doctype)
		
		# Verify reset worked
		self.assertIsInstance(default_preferences, dict)
		self.assertEqual(default_preferences["pagination"]["page_size"], 20)
		self.assertEqual(default_preferences["sorting"]["field"], "modified")
	
	def test_export_import_preferences(self):
		"""Test exporting and importing preferences"""
		from column_management.column_management.services.preference_service import PreferenceService
		
		service = PreferenceService()
		
		# Create and save test preferences
		test_preferences = {
			"columns": {
				"name": {"visible": True, "width": 200, "order": 0}
			},
			"filters": {"active_filters": []},
			"pagination": {"page_size": 25, "current_page": 1},
			"sorting": {"field": "creation", "order": "desc"},
			"view_settings": {},
			"last_updated": now(),
			"version": "1.0"
		}
		
		service.save_user_preferences(self.test_user, self.test_doctype, test_preferences)
		
		# Export preferences
		export_data = service.export_user_preferences(self.test_user, [self.test_doctype])
		
		self.assertIsInstance(export_data, dict)
		self.assertIn("preferences", export_data)
		self.assertEqual(export_data["user"], self.test_user)
		
		# Clean up existing preferences
		service.reset_to_defaults(self.test_user, self.test_doctype)
		
		# Import preferences
		imported_count = service.import_user_preferences(self.test_user, export_data, overwrite=True)
		
		self.assertEqual(imported_count, 1)
		
		# Verify imported preferences
		imported_preferences = service.get_user_preferences(self.test_user, self.test_doctype)
		self.assertEqual(imported_preferences["pagination"]["page_size"], 25)
		self.assertEqual(imported_preferences["sorting"]["field"], "creation")
	
	def test_preference_validation(self):
		"""Test preference validation"""
		from column_management.column_management.services.preference_service import PreferenceService
		
		service = PreferenceService()
		
		# Test invalid preferences structure
		invalid_preferences = {
			"columns": "invalid",  # Should be dict
			"filters": {},
			"pagination": {},
			"sorting": {},
			"view_settings": {}
		}
		
		with self.assertRaises(frappe.ValidationError):
			service.save_user_preferences(self.test_user, self.test_doctype, invalid_preferences)
		
		# Test invalid column width
		invalid_column_preferences = {
			"columns": {
				"name": {
					"visible": True,
					"width": 10,  # Too small
					"order": 0
				}
			},
			"filters": {},
			"pagination": {},
			"sorting": {},
			"view_settings": {}
		}
		
		with self.assertRaises(frappe.ValidationError):
			service.save_user_preferences(self.test_user, self.test_doctype, invalid_column_preferences)
	
	def test_cache_functionality(self):
		"""Test caching functionality"""
		from column_management.column_management.services.preference_service import PreferenceService
		
		service = PreferenceService()
		
		# First call should fetch from database
		preferences1 = service.get_user_preferences(self.test_user, self.test_doctype)
		
		# Second call should use cache
		preferences2 = service.get_user_preferences(self.test_user, self.test_doctype)
		
		# Should be the same object (from cache)
		self.assertEqual(preferences1, preferences2)
		
		# Clear cache and verify
		service.clear_user_cache(self.test_user, self.test_doctype)
		
		# This should fetch from database again
		preferences3 = service.get_user_preferences(self.test_user, self.test_doctype)
		self.assertEqual(preferences1, preferences3)

if __name__ == '__main__':
	unittest.main()