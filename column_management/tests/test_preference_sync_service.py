# -*- coding: utf-8 -*-
# Copyright (c) 2024, ERPNext Column Management Team and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import unittest
import frappe
import json
from frappe.utils import now

class TestPreferenceSyncService(unittest.TestCase):
	"""Test cases for PreferenceSyncService"""
	
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
		
		# Clean up any existing data
		frappe.db.delete("User Column Preference", {
			"user": self.test_user,
			"doctype_name": self.test_doctype
		})
		
		frappe.db.delete("Preference Backup", {
			"user": self.test_user
		})
		
		frappe.db.commit()
	
	def tearDown(self):
		"""Clean up test data"""
		# Clean up test data
		frappe.db.delete("User Column Preference", {
			"user": self.test_user,
			"doctype_name": self.test_doctype
		})
		
		frappe.db.delete("Preference Backup", {
			"user": self.test_user
		})
		
		frappe.db.commit()
	
	def test_create_preference_backup(self):
		"""Test creating a preference backup"""
		from column_management.column_management.services.preference_sync_service import PreferenceSyncService
		from column_management.column_management.services.preference_service import PreferenceService
		
		# First create some preferences
		preference_service = PreferenceService()
		test_preferences = {
			"columns": {
				"name": {"visible": True, "width": 150, "order": 0}
			},
			"filters": {"active_filters": []},
			"pagination": {"page_size": 25, "current_page": 1},
			"sorting": {"field": "creation", "order": "asc"},
			"view_settings": {},
			"last_updated": now(),
			"version": "1.0"
		}
		
		preference_service.save_user_preferences(self.test_user, self.test_doctype, test_preferences)
		
		# Create backup
		sync_service = PreferenceSyncService()
		backup_name = sync_service.create_preference_backup(self.test_user, self.test_doctype, "manual")
		
		self.assertIsNotNone(backup_name)
		
		# Verify backup exists
		backup_doc = frappe.get_doc("Preference Backup", backup_name)
		self.assertEqual(backup_doc.user, self.test_user)
		self.assertEqual(backup_doc.doctype_name, self.test_doctype)
		self.assertEqual(backup_doc.backup_type, "manual")
		
		# Verify backup data
		backup_data = backup_doc.get_backup_data()
		self.assertIn(self.test_doctype, backup_data)
		self.assertEqual(backup_data[self.test_doctype]["pagination"]["page_size"], 25)
	
	def test_restore_preference_backup(self):
		"""Test restoring preferences from backup"""
		from column_management.column_management.services.preference_sync_service import PreferenceSyncService
		from column_management.column_management.services.preference_service import PreferenceService
		
		# Create and save initial preferences
		preference_service = PreferenceService()
		initial_preferences = {
			"columns": {
				"name": {"visible": True, "width": 150, "order": 0}
			},
			"filters": {"active_filters": []},
			"pagination": {"page_size": 25, "current_page": 1},
			"sorting": {"field": "creation", "order": "asc"},
			"view_settings": {},
			"last_updated": now(),
			"version": "1.0"
		}
		
		preference_service.save_user_preferences(self.test_user, self.test_doctype, initial_preferences)
		
		# Create backup
		sync_service = PreferenceSyncService()
		backup_name = sync_service.create_preference_backup(self.test_user, self.test_doctype, "manual")
		
		# Modify preferences
		modified_preferences = initial_preferences.copy()
		modified_preferences["pagination"]["page_size"] = 50
		preference_service.save_user_preferences(self.test_user, self.test_doctype, modified_preferences)
		
		# Verify modification
		current_prefs = preference_service.get_user_preferences(self.test_user, self.test_doctype)
		self.assertEqual(current_prefs["pagination"]["page_size"], 50)
		
		# Restore from backup
		restored_count = sync_service.restore_preference_backup(backup_name, self.test_user)
		self.assertEqual(restored_count, 1)
		
		# Verify restoration
		restored_prefs = preference_service.get_user_preferences(self.test_user, self.test_doctype)
		self.assertEqual(restored_prefs["pagination"]["page_size"], 25)
	
	def test_get_preference_backups(self):
		"""Test getting list of preference backups"""
		from column_management.column_management.services.preference_sync_service import PreferenceSyncService
		from column_management.column_management.services.preference_service import PreferenceService
		
		# Create some preferences
		preference_service = PreferenceService()
		test_preferences = {
			"columns": {"name": {"visible": True, "width": 150, "order": 0}},
			"filters": {"active_filters": []},
			"pagination": {"page_size": 25, "current_page": 1},
			"sorting": {"field": "creation", "order": "asc"},
			"view_settings": {},
			"last_updated": now(),
			"version": "1.0"
		}
		
		preference_service.save_user_preferences(self.test_user, self.test_doctype, test_preferences)
		
		# Create multiple backups
		sync_service = PreferenceSyncService()
		backup1 = sync_service.create_preference_backup(self.test_user, self.test_doctype, "manual")
		backup2 = sync_service.create_preference_backup(self.test_user, self.test_doctype, "automatic")
		
		# Get backups
		backups = sync_service.get_preference_backups(self.test_user, self.test_doctype)
		
		self.assertEqual(len(backups), 2)
		
		# Verify backup details
		backup_names = [b["name"] for b in backups]
		self.assertIn(backup1, backup_names)
		self.assertIn(backup2, backup_names)
		
		# Check backup types
		backup_types = [b["backup_type"] for b in backups]
		self.assertIn("manual", backup_types)
		self.assertIn("automatic", backup_types)
	
	def test_delete_preference_backup(self):
		"""Test deleting a preference backup"""
		from column_management.column_management.services.preference_sync_service import PreferenceSyncService
		from column_management.column_management.services.preference_service import PreferenceService
		
		# Create preferences and backup
		preference_service = PreferenceService()
		test_preferences = {
			"columns": {"name": {"visible": True, "width": 150, "order": 0}},
			"filters": {"active_filters": []},
			"pagination": {"page_size": 25, "current_page": 1},
			"sorting": {"field": "creation", "order": "asc"},
			"view_settings": {},
			"last_updated": now(),
			"version": "1.0"
		}
		
		preference_service.save_user_preferences(self.test_user, self.test_doctype, test_preferences)
		
		sync_service = PreferenceSyncService()
		backup_name = sync_service.create_preference_backup(self.test_user, self.test_doctype, "manual")
		
		# Verify backup exists
		self.assertTrue(frappe.db.exists("Preference Backup", backup_name))
		
		# Delete backup
		success = sync_service.delete_preference_backup(backup_name, self.test_user)
		self.assertTrue(success)
		
		# Verify backup is deleted
		self.assertFalse(frappe.db.exists("Preference Backup", backup_name))
	
	def test_reset_to_default_configuration(self):
		"""Test resetting preferences to default with backup"""
		from column_management.column_management.services.preference_sync_service import PreferenceSyncService
		from column_management.column_management.services.preference_service import PreferenceService
		
		# Create custom preferences
		preference_service = PreferenceService()
		custom_preferences = {
			"columns": {"name": {"visible": True, "width": 300, "order": 0}},
			"filters": {"active_filters": []},
			"pagination": {"page_size": 100, "current_page": 1},
			"sorting": {"field": "name", "order": "asc"},
			"view_settings": {},
			"last_updated": now(),
			"version": "1.0"
		}
		
		preference_service.save_user_preferences(self.test_user, self.test_doctype, custom_preferences)
		
		# Reset to defaults
		sync_service = PreferenceSyncService()
		result = sync_service.reset_to_default_configuration(self.test_user, self.test_doctype)
		
		self.assertTrue(result["success"])
		self.assertIsNotNone(result["backup_name"])
		
		# Verify backup was created
		self.assertTrue(frappe.db.exists("Preference Backup", result["backup_name"]))
		
		# Verify preferences were reset
		current_prefs = preference_service.get_user_preferences(self.test_user, self.test_doctype)
		self.assertEqual(current_prefs["pagination"]["page_size"], 20)  # Default
		self.assertEqual(current_prefs["sorting"]["field"], "modified")  # Default
	
	def test_sync_preferences_across_sessions(self):
		"""Test synchronizing preferences across sessions"""
		from column_management.column_management.services.preference_sync_service import PreferenceSyncService
		from column_management.column_management.services.preference_service import PreferenceService
		
		# Create preferences
		preference_service = PreferenceService()
		test_preferences = {
			"columns": {"name": {"visible": True, "width": 150, "order": 0}},
			"filters": {"active_filters": []},
			"pagination": {"page_size": 25, "current_page": 1},
			"sorting": {"field": "creation", "order": "asc"},
			"view_settings": {},
			"last_updated": now(),
			"version": "1.0"
		}
		
		preference_service.save_user_preferences(self.test_user, self.test_doctype, test_preferences)
		
		# Sync preferences
		sync_service = PreferenceSyncService()
		success = sync_service.sync_preferences_across_sessions(self.test_user, self.test_doctype)
		
		self.assertTrue(success)
		
		# Check sync status
		sync_status = sync_service.get_sync_status(self.test_user, self.test_doctype)
		self.assertTrue(sync_status["is_synced"])
		self.assertIsNotNone(sync_status["last_sync"])
		self.assertIsNotNone(sync_status["sync_hash"])
	
	def test_preference_statistics(self):
		"""Test getting preference statistics"""
		from column_management.column_management.services.preference_sync_service import PreferenceSyncService
		from column_management.column_management.services.preference_service import PreferenceService
		
		# Create preferences and backups
		preference_service = PreferenceService()
		test_preferences = {
			"columns": {"name": {"visible": True, "width": 150, "order": 0}},
			"filters": {"active_filters": []},
			"pagination": {"page_size": 25, "current_page": 1},
			"sorting": {"field": "creation", "order": "asc"},
			"view_settings": {},
			"last_updated": now(),
			"version": "1.0"
		}
		
		preference_service.save_user_preferences(self.test_user, self.test_doctype, test_preferences)
		
		sync_service = PreferenceSyncService()
		backup1 = sync_service.create_preference_backup(self.test_user, self.test_doctype, "manual")
		backup2 = sync_service.create_preference_backup(self.test_user, self.test_doctype, "automatic")
		
		# Get statistics
		stats = sync_service.get_preference_statistics(self.test_user)
		
		self.assertEqual(stats["preference_count"], 1)
		self.assertEqual(stats["backup_count"], 2)
		self.assertIn("manual", stats["backup_types"])
		self.assertIn("automatic", stats["backup_types"])
		self.assertEqual(stats["backup_types"]["manual"], 1)
		self.assertEqual(stats["backup_types"]["automatic"], 1)
		self.assertIsNotNone(stats["latest_backup"])
	
	def test_backup_cleanup(self):
		"""Test automatic backup cleanup"""
		from column_management.column_management.services.preference_sync_service import PreferenceSyncService
		from column_management.column_management.services.preference_service import PreferenceService
		
		# Create preferences
		preference_service = PreferenceService()
		test_preferences = {
			"columns": {"name": {"visible": True, "width": 150, "order": 0}},
			"filters": {"active_filters": []},
			"pagination": {"page_size": 25, "current_page": 1},
			"sorting": {"field": "creation", "order": "asc"},
			"view_settings": {},
			"last_updated": now(),
			"version": "1.0"
		}
		
		preference_service.save_user_preferences(self.test_user, self.test_doctype, test_preferences)
		
		# Create multiple backups
		sync_service = PreferenceSyncService()
		backup_names = []
		for i in range(5):
			backup_name = sync_service.create_preference_backup(self.test_user, self.test_doctype, "manual")
			backup_names.append(backup_name)
		
		# Verify all backups exist
		for backup_name in backup_names:
			self.assertTrue(frappe.db.exists("Preference Backup", backup_name))
		
		# Test cleanup (this is mainly to ensure the method runs without error)
		sync_service._cleanup_old_backups(self.test_user)
		
		# All backups should still exist since we're within limits
		for backup_name in backup_names:
			self.assertTrue(frappe.db.exists("Preference Backup", backup_name))

if __name__ == '__main__':
	unittest.main()