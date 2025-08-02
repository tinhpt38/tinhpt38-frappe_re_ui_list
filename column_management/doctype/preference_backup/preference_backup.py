# -*- coding: utf-8 -*-
# Copyright (c) 2024, ERPNext Column Management Team and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import json
import hashlib
from frappe.model.document import Document
from frappe import _
from frappe.utils import now

class PreferenceBackup(Document):
	def validate(self):
		"""Validate preference backup data"""
		self.validate_user_exists()
		self.validate_backup_data()
		self.set_metadata()
	
	def validate_user_exists(self):
		"""Validate that the user exists"""
		if not frappe.db.exists("User", self.user):
			frappe.throw(_("User {0} does not exist").format(self.user))
	
	def validate_backup_data(self):
		"""Validate backup data structure"""
		if self.backup_data:
			try:
				if isinstance(self.backup_data, str):
					data = json.loads(self.backup_data)
				else:
					data = self.backup_data
				
				# Validate that it's a valid JSON object
				if not isinstance(data, dict):
					frappe.throw(_("Backup data must be a valid JSON object"))
				
				# Validate structure for each doctype preference
				for doctype_name, preferences in data.items():
					if not isinstance(preferences, dict):
						frappe.throw(_("Preferences for {0} must be a dictionary").format(doctype_name))
					
					# Check for required preference sections
					required_sections = ["columns", "filters", "pagination", "sorting", "view_settings"]
					for section in required_sections:
						if section not in preferences:
							frappe.throw(_("Missing required section '{0}' in preferences for {1}").format(section, doctype_name))
			
			except json.JSONDecodeError:
				frappe.throw(_("Invalid JSON format in backup data"))
	
	def set_metadata(self):
		"""Set backup metadata"""
		# Set created timestamp
		if self.is_new():
			self.created_at = now()
		
		# Calculate backup size
		if self.backup_data:
			backup_str = json.dumps(self.backup_data) if isinstance(self.backup_data, dict) else str(self.backup_data)
			self.backup_size = len(backup_str.encode('utf-8'))
		
		# Generate backup hash
		if self.backup_data:
			self.backup_hash = self._generate_backup_hash()
	
	def before_save(self):
		"""Actions before saving the document"""
		# Serialize backup data if it's a dict
		if isinstance(self.backup_data, dict):
			self.backup_data = json.dumps(self.backup_data, indent=2)
	
	def after_insert(self):
		"""Actions after inserting the document"""
		self.log_backup_creation()
	
	def on_trash(self):
		"""Actions before deleting the document"""
		self.log_backup_deletion()
	
	def log_backup_creation(self):
		"""Log backup creation"""
		frappe.logger().info(f"Created preference backup {self.name} for user {self.user} - {self.doctype_name}")
	
	def log_backup_deletion(self):
		"""Log backup deletion"""
		frappe.logger().info(f"Deleted preference backup {self.name} for user {self.user} - {self.doctype_name}")
	
	def get_backup_data(self):
		"""Get deserialized backup data"""
		if not self.backup_data:
			return {}
		
		try:
			if isinstance(self.backup_data, str):
				return json.loads(self.backup_data)
			else:
				return self.backup_data
		except json.JSONDecodeError:
			return {}
	
	def set_backup_data(self, data):
		"""Set backup data with validation"""
		if not isinstance(data, dict):
			frappe.throw(_("Backup data must be a dictionary"))
		
		self.backup_data = data
		self.validate_backup_data()
	
	def get_backup_summary(self):
		"""Get summary of backup contents"""
		try:
			data = self.get_backup_data()
			
			summary = {
				"doctype_count": len(data),
				"doctypes": list(data.keys()),
				"total_preferences": 0,
				"backup_size_mb": round(self.backup_size / (1024 * 1024), 2) if self.backup_size else 0
			}
			
			# Count total preferences
			for doctype_name, preferences in data.items():
				if isinstance(preferences, dict) and "columns" in preferences:
					summary["total_preferences"] += len(preferences.get("columns", {}))
			
			return summary
			
		except Exception as e:
			frappe.log_error(f"Error getting backup summary: {str(e)}")
			return {
				"doctype_count": 0,
				"doctypes": [],
				"total_preferences": 0,
				"backup_size_mb": 0
			}
	
	def compare_with_current(self, user=None):
		"""Compare backup with current user preferences"""
		try:
			if not user:
				user = self.user
			
			backup_data = self.get_backup_data()
			differences = {}
			
			from column_management.column_management.services.preference_service import PreferenceService
			preference_service = PreferenceService()
			
			for doctype_name in backup_data.keys():
				current_prefs = preference_service.get_user_preferences(user, doctype_name)
				backup_prefs = backup_data[doctype_name]
				
				# Simple comparison - in a full implementation, you'd do detailed diff
				current_hash = self._generate_data_hash(current_prefs)
				backup_hash = self._generate_data_hash(backup_prefs)
				
				differences[doctype_name] = {
					"has_changes": current_hash != backup_hash,
					"current_hash": current_hash,
					"backup_hash": backup_hash
				}
			
			return differences
			
		except Exception as e:
			frappe.log_error(f"Error comparing backup with current: {str(e)}")
			return {}
	
	def restore_backup(self, user=None, doctype_names=None):
		"""Restore preferences from this backup"""
		try:
			if not user:
				user = self.user
			
			# Verify user permission
			if user != self.user and not frappe.has_permission("Preference Backup", "write"):
				frappe.throw(_("You can only restore your own backups"))
			
			backup_data = self.get_backup_data()
			
			# Filter by specific doctypes if provided
			if doctype_names:
				backup_data = {k: v for k, v in backup_data.items() if k in doctype_names}
			
			# Restore preferences
			from column_management.column_management.doctype.user_column_preference.user_column_preference import UserColumnPreference
			
			restored_count = 0
			for doctype_name, preferences in backup_data.items():
				try:
					UserColumnPreference.create_or_update_preference(
						user, doctype_name, preferences
					)
					restored_count += 1
					
				except Exception as e:
					frappe.log_error(f"Error restoring preference for {doctype_name}: {str(e)}")
			
			# Log restoration
			frappe.logger().info(f"Restored {restored_count} preferences from backup {self.name}")
			
			return restored_count
			
		except Exception as e:
			frappe.log_error(f"Error restoring backup: {str(e)}")
			frappe.throw(_("Failed to restore backup: {0}").format(str(e)))
	
	def _generate_backup_hash(self):
		"""Generate hash for backup data"""
		try:
			if isinstance(self.backup_data, dict):
				data_str = json.dumps(self.backup_data, sort_keys=True, separators=(',', ':'))
			else:
				data_str = str(self.backup_data)
			
			return hashlib.md5(data_str.encode('utf-8')).hexdigest()
			
		except Exception as e:
			frappe.log_error(f"Error generating backup hash: {str(e)}")
			return None
	
	def _generate_data_hash(self, data):
		"""Generate hash for any data"""
		try:
			data_str = json.dumps(data, sort_keys=True, separators=(',', ':'))
			return hashlib.md5(data_str.encode('utf-8')).hexdigest()
			
		except Exception as e:
			frappe.log_error(f"Error generating data hash: {str(e)}")
			return None
	
	@staticmethod
	def create_backup(user, doctype_name=None, backup_type="manual", description=None):
		"""Create a new preference backup"""
		try:
			from column_management.column_management.services.preference_sync_service import PreferenceSyncService
			sync_service = PreferenceSyncService()
			
			backup_name = sync_service.create_preference_backup(user, doctype_name, backup_type)
			
			if backup_name and description:
				# Update description
				backup_doc = frappe.get_doc("Preference Backup", backup_name)
				backup_doc.description = description
				backup_doc.save(ignore_permissions=True)
			
			return backup_name
			
		except Exception as e:
			frappe.log_error(f"Error creating backup: {str(e)}")
			return None
	
	@staticmethod
	def get_user_backups(user, doctype_name=None, backup_type=None, limit=10):
		"""Get backups for a user"""
		try:
			filters = {"user": user}
			if doctype_name:
				filters["doctype_name"] = doctype_name
			if backup_type:
				filters["backup_type"] = backup_type
			
			backups = frappe.get_all("Preference Backup",
				filters=filters,
				fields=["name", "doctype_name", "backup_type", "created_at", "backup_size", "description"],
				order_by="created_at desc",
				limit=limit
			)
			
			return backups
			
		except Exception as e:
			frappe.log_error(f"Error getting user backups: {str(e)}")
			return []
	
	@staticmethod
	def cleanup_old_backups(user, retention_days=30, max_backups=10):
		"""Clean up old backups for a user"""
		try:
			from column_management.column_management.services.preference_sync_service import PreferenceSyncService
			sync_service = PreferenceSyncService()
			sync_service._cleanup_old_backups(user)
			
			return True
			
		except Exception as e:
			frappe.log_error(f"Error cleaning up old backups: {str(e)}")
			return False