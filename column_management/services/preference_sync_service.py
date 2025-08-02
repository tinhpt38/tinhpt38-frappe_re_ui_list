# -*- coding: utf-8 -*-
# Copyright (c) 2024, ERPNext Column Management Team and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import json
import hashlib
from frappe import _
from frappe.utils import now, get_datetime, add_to_date

class PreferenceSyncService:
	"""Service for synchronizing preferences across multiple sessions and backup management"""
	
	def __init__(self):
		self.cache = frappe.cache()
		self.cache_prefix = "column_management_sync"
		self.sync_interval = 30  # seconds
		self.backup_retention_days = 30
		self.max_backups_per_user = 10
	
	def sync_preferences_across_sessions(self, user, doctype_name):
		"""Synchronize preferences across multiple user sessions"""
		try:
			# Get the latest preference from database
			from column_management.column_management.services.preference_service import PreferenceService
			preference_service = PreferenceService()
			
			latest_preferences = preference_service.get_user_preferences(user, doctype_name)
			
			# Create sync notification for all active sessions of this user
			sync_data = {
				"user": user,
				"doctype_name": doctype_name,
				"preferences": latest_preferences,
				"sync_timestamp": now(),
				"sync_hash": self._generate_preference_hash(latest_preferences)
			}
			
			# Store sync data in cache for active sessions to pick up
			sync_key = f"{self.cache_prefix}:sync:{user}:{doctype_name}"
			self.cache.set(sync_key, json.dumps(sync_data), expire=self.sync_interval * 2)
			
			# Publish real-time update to all user sessions
			frappe.publish_realtime(
				event="preference_sync_update",
				message=sync_data,
				user=user
			)
			
			frappe.logger().info(f"Synchronized preferences for {user} - {doctype_name}")
			return True
			
		except Exception as e:
			frappe.log_error(f"Error synchronizing preferences: {str(e)}")
			return False
	
	def check_for_preference_updates(self, user, doctype_name, current_hash=None):
		"""Check if preferences have been updated in other sessions"""
		try:
			sync_key = f"{self.cache_prefix}:sync:{user}:{doctype_name}"
			sync_data_str = self.cache.get(sync_key)
			
			if not sync_data_str:
				return None
			
			sync_data = json.loads(sync_data_str)
			
			# Check if this is a newer version
			if current_hash and sync_data.get("sync_hash") == current_hash:
				return None  # No update needed
			
			return sync_data
			
		except Exception as e:
			frappe.log_error(f"Error checking for preference updates: {str(e)}")
			return None
	
	def create_preference_backup(self, user, doctype_name=None, backup_type="manual"):
		"""Create a backup of user preferences"""
		try:
			# Get all preferences for user or specific doctype
			from column_management.column_management.services.preference_service import PreferenceService
			preference_service = PreferenceService()
			
			if doctype_name:
				# Backup specific doctype preferences
				preferences = {
					doctype_name: preference_service.get_user_preferences(user, doctype_name)
				}
			else:
				# Backup all user preferences
				user_prefs = frappe.get_all("User Column Preference",
					filters={"user": user},
					fields=["doctype_name", "preference_data"]
				)
				
				preferences = {}
				for pref in user_prefs:
					try:
						pref_data = json.loads(pref.preference_data) if isinstance(pref.preference_data, str) else pref.preference_data
						preferences[pref.doctype_name] = pref_data
					except (json.JSONDecodeError, TypeError):
						continue
			
			# Create backup document
			backup_doc = frappe.get_doc({
				"doctype": "Preference Backup",
				"user": user,
				"doctype_name": doctype_name or "All",
				"backup_type": backup_type,
				"backup_data": json.dumps(preferences, indent=2),
				"backup_hash": self._generate_preference_hash(preferences),
				"created_at": now()
			})
			
			backup_doc.insert(ignore_permissions=True)
			
			# Clean up old backups
			self._cleanup_old_backups(user)
			
			frappe.logger().info(f"Created preference backup for {user} - {doctype_name or 'All'}")
			return backup_doc.name
			
		except Exception as e:
			frappe.log_error(f"Error creating preference backup: {str(e)}")
			return None
	
	def restore_preference_backup(self, backup_name, user=None):
		"""Restore preferences from a backup"""
		try:
			# Get backup document
			backup_doc = frappe.get_doc("Preference Backup", backup_name)
			
			# Verify user permission
			if user and backup_doc.user != user:
				frappe.throw(_("You can only restore your own backups"))
			
			# Parse backup data
			backup_data = json.loads(backup_doc.backup_data)
			
			# Restore preferences
			from column_management.column_management.doctype.user_column_preference.user_column_preference import UserColumnPreference
			
			restored_count = 0
			for doctype_name, preferences in backup_data.items():
				try:
					UserColumnPreference.create_or_update_preference(
						backup_doc.user, doctype_name, preferences
					)
					
					# Sync across sessions
					self.sync_preferences_across_sessions(backup_doc.user, doctype_name)
					
					restored_count += 1
					
				except Exception as e:
					frappe.log_error(f"Error restoring preference for {doctype_name}: {str(e)}")
			
			frappe.logger().info(f"Restored {restored_count} preferences from backup {backup_name}")
			return restored_count
			
		except Exception as e:
			frappe.log_error(f"Error restoring preference backup: {str(e)}")
			frappe.throw(_("Failed to restore backup: {0}").format(str(e)))
	
	def get_preference_backups(self, user, doctype_name=None, limit=10):
		"""Get list of preference backups for a user"""
		try:
			filters = {"user": user}
			if doctype_name:
				filters["doctype_name"] = doctype_name
			
			backups = frappe.get_all("Preference Backup",
				filters=filters,
				fields=["name", "doctype_name", "backup_type", "created_at", "backup_hash"],
				order_by="created_at desc",
				limit=limit
			)
			
			return backups
			
		except Exception as e:
			frappe.log_error(f"Error getting preference backups: {str(e)}")
			return []
	
	def delete_preference_backup(self, backup_name, user=None):
		"""Delete a preference backup"""
		try:
			# Get backup document
			backup_doc = frappe.get_doc("Preference Backup", backup_name)
			
			# Verify user permission
			if user and backup_doc.user != user:
				frappe.throw(_("You can only delete your own backups"))
			
			# Delete the backup
			frappe.delete_doc("Preference Backup", backup_name, ignore_permissions=True)
			
			frappe.logger().info(f"Deleted preference backup {backup_name}")
			return True
			
		except Exception as e:
			frappe.log_error(f"Error deleting preference backup: {str(e)}")
			frappe.throw(_("Failed to delete backup: {0}").format(str(e)))
	
	def schedule_automatic_backup(self, user, doctype_name=None):
		"""Schedule automatic backup for user preferences"""
		try:
			# Check if automatic backup is due
			last_backup = frappe.db.get_value("Preference Backup", {
				"user": user,
				"doctype_name": doctype_name or "All",
				"backup_type": "automatic"
			}, "created_at", order_by="created_at desc")
			
			if last_backup:
				last_backup_date = get_datetime(last_backup)
				next_backup_due = add_to_date(last_backup_date, days=1)  # Daily automatic backup
				
				if get_datetime(now()) < next_backup_due:
					return False  # Not due yet
			
			# Create automatic backup
			backup_name = self.create_preference_backup(user, doctype_name, "automatic")
			
			if backup_name:
				frappe.logger().info(f"Created automatic backup for {user} - {doctype_name or 'All'}")
				return True
			
			return False
			
		except Exception as e:
			frappe.log_error(f"Error scheduling automatic backup: {str(e)}")
			return False
	
	def reset_to_default_configuration(self, user, doctype_name):
		"""Reset user preferences to default configuration with backup"""
		try:
			# Create backup before reset
			backup_name = self.create_preference_backup(user, doctype_name, "before_reset")
			
			if not backup_name:
				frappe.throw(_("Failed to create backup before reset"))
			
			# Reset preferences
			from column_management.column_management.services.preference_service import PreferenceService
			preference_service = PreferenceService()
			
			default_preferences = preference_service.reset_to_defaults(user, doctype_name)
			
			# Sync across sessions
			self.sync_preferences_across_sessions(user, doctype_name)
			
			frappe.logger().info(f"Reset preferences to defaults for {user} - {doctype_name}")
			
			return {
				"success": True,
				"backup_name": backup_name,
				"default_preferences": default_preferences
			}
			
		except Exception as e:
			frappe.log_error(f"Error resetting to default configuration: {str(e)}")
			frappe.throw(_("Failed to reset to defaults: {0}").format(str(e)))
	
	def compare_preference_versions(self, user, doctype_name, version1_hash, version2_hash):
		"""Compare two versions of preferences"""
		try:
			# This is a placeholder for preference version comparison
			# In a full implementation, you would store version history
			# and provide detailed diff information
			
			return {
				"version1": version1_hash,
				"version2": version2_hash,
				"differences": [],  # Would contain detailed diff
				"summary": "Version comparison not fully implemented"
			}
			
		except Exception as e:
			frappe.log_error(f"Error comparing preference versions: {str(e)}")
			return None
	
	def get_sync_status(self, user, doctype_name):
		"""Get synchronization status for user preferences"""
		try:
			sync_key = f"{self.cache_prefix}:sync:{user}:{doctype_name}"
			sync_data_str = self.cache.get(sync_key)
			
			if sync_data_str:
				sync_data = json.loads(sync_data_str)
				return {
					"is_synced": True,
					"last_sync": sync_data.get("sync_timestamp"),
					"sync_hash": sync_data.get("sync_hash")
				}
			else:
				return {
					"is_synced": False,
					"last_sync": None,
					"sync_hash": None
				}
				
		except Exception as e:
			frappe.log_error(f"Error getting sync status: {str(e)}")
			return {
				"is_synced": False,
				"last_sync": None,
				"sync_hash": None,
				"error": str(e)
			}
	
	def force_sync_all_sessions(self, user):
		"""Force synchronization of all preferences across all user sessions"""
		try:
			# Get all doctypes with preferences for this user
			user_prefs = frappe.get_all("User Column Preference",
				filters={"user": user},
				fields=["doctype_name"],
				distinct=True
			)
			
			synced_count = 0
			for pref in user_prefs:
				if self.sync_preferences_across_sessions(user, pref.doctype_name):
					synced_count += 1
			
			frappe.logger().info(f"Force synced {synced_count} preferences for {user}")
			return synced_count
			
		except Exception as e:
			frappe.log_error(f"Error force syncing all sessions: {str(e)}")
			return 0
	
	def _generate_preference_hash(self, preferences):
		"""Generate hash for preference data to detect changes"""
		try:
			# Convert preferences to a consistent string representation
			pref_str = json.dumps(preferences, sort_keys=True, separators=(',', ':'))
			
			# Generate MD5 hash
			return hashlib.md5(pref_str.encode('utf-8')).hexdigest()
			
		except Exception as e:
			frappe.log_error(f"Error generating preference hash: {str(e)}")
			return None
	
	def _cleanup_old_backups(self, user):
		"""Clean up old backups to maintain storage limits"""
		try:
			# Get all backups for user, ordered by creation date
			all_backups = frappe.get_all("Preference Backup",
				filters={"user": user},
				fields=["name", "created_at", "backup_type"],
				order_by="created_at desc"
			)
			
			# Separate manual and automatic backups
			manual_backups = [b for b in all_backups if b.backup_type == "manual"]
			automatic_backups = [b for b in all_backups if b.backup_type == "automatic"]
			
			# Keep only the latest backups within limits
			backups_to_delete = []
			
			# Keep max_backups_per_user manual backups
			if len(manual_backups) > self.max_backups_per_user:
				backups_to_delete.extend(manual_backups[self.max_backups_per_user:])
			
			# Keep automatic backups within retention period
			retention_date = add_to_date(now(), days=-self.backup_retention_days)
			for backup in automatic_backups:
				if get_datetime(backup.created_at) < get_datetime(retention_date):
					backups_to_delete.append(backup)
			
			# Delete old backups
			for backup in backups_to_delete:
				frappe.delete_doc("Preference Backup", backup.name, ignore_permissions=True)
			
			if backups_to_delete:
				frappe.logger().info(f"Cleaned up {len(backups_to_delete)} old backups for {user}")
			
		except Exception as e:
			frappe.log_error(f"Error cleaning up old backups: {str(e)}")
	
	def get_preference_statistics(self, user):
		"""Get statistics about user's preferences and backups"""
		try:
			# Count preferences
			pref_count = frappe.db.count("User Column Preference", {"user": user})
			
			# Count backups
			backup_count = frappe.db.count("Preference Backup", {"user": user})
			
			# Get backup types
			backup_types = frappe.db.sql("""
				SELECT backup_type, COUNT(*) as count
				FROM `tabPreference Backup`
				WHERE user = %s
				GROUP BY backup_type
			""", (user,), as_dict=True)
			
			# Get latest backup date
			latest_backup = frappe.db.get_value("Preference Backup", 
				{"user": user}, 
				"created_at", 
				order_by="created_at desc"
			)
			
			return {
				"preference_count": pref_count,
				"backup_count": backup_count,
				"backup_types": {bt.backup_type: bt.count for bt in backup_types},
				"latest_backup": latest_backup
			}
			
		except Exception as e:
			frappe.log_error(f"Error getting preference statistics: {str(e)}")
			return {
				"preference_count": 0,
				"backup_count": 0,
				"backup_types": {},
				"latest_backup": None
			}