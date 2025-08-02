# -*- coding: utf-8 -*-
# Copyright (c) 2024, ERPNext Column Management Team and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import json
from frappe import _

@frappe.whitelist()
def get_user_preferences(doctype_name, user=None):
	"""Get user preferences for a doctype"""
	try:
		if not user:
			user = frappe.session.user
		
		# Check permissions
		if not frappe.has_permission(doctype_name, "read", user=user):
			frappe.throw(_("No permission to access {0}").format(doctype_name))
		
		# Get preference service
		from column_management.column_management.services.preference_service import PreferenceService
		service = PreferenceService()
		
		# Get preferences
		preferences = service.get_user_preferences(user, doctype_name)
		
		return {
			"success": True,
			"preferences": preferences
		}
		
	except Exception as e:
		frappe.log_error(f"Error getting user preferences: {str(e)}")
		return {
			"success": False,
			"error": str(e)
		}

@frappe.whitelist()
def save_user_preferences(doctype_name, preferences, user=None):
	"""Save user preferences for a doctype"""
	try:
		if not user:
			user = frappe.session.user
		
		# Check permissions
		if not frappe.has_permission(doctype_name, "read", user=user):
			frappe.throw(_("No permission to access {0}").format(doctype_name))
		
		# Parse preferences if string
		if isinstance(preferences, str):
			preferences = json.loads(preferences)
		
		# Get preference service
		from column_management.column_management.services.preference_service import PreferenceService
		service = PreferenceService()
		
		# Save preferences
		success = service.save_user_preferences(user, doctype_name, preferences)
		
		return {
			"success": success,
			"message": _("Preferences saved successfully") if success else _("Failed to save preferences")
		}
		
	except Exception as e:
		frappe.log_error(f"Error saving user preferences: {str(e)}")
		return {
			"success": False,
			"error": str(e)
		}

@frappe.whitelist()
def update_column_preferences(doctype_name, column_updates, user=None):
	"""Update specific column preferences"""
	try:
		if not user:
			user = frappe.session.user
		
		# Check permissions
		if not frappe.has_permission(doctype_name, "read", user=user):
			frappe.throw(_("No permission to access {0}").format(doctype_name))
		
		# Parse updates if string
		if isinstance(column_updates, str):
			column_updates = json.loads(column_updates)
		
		# Get preference service
		from column_management.column_management.services.preference_service import PreferenceService
		service = PreferenceService()
		
		# Update column preferences
		success = service.update_column_preferences(user, doctype_name, column_updates)
		
		return {
			"success": success,
			"message": _("Column preferences updated successfully") if success else _("Failed to update column preferences")
		}
		
	except Exception as e:
		frappe.log_error(f"Error updating column preferences: {str(e)}")
		return {
			"success": False,
			"error": str(e)
		}

@frappe.whitelist()
def update_filter_preferences(doctype_name, filter_updates, user=None):
	"""Update filter preferences"""
	try:
		if not user:
			user = frappe.session.user
		
		# Check permissions
		if not frappe.has_permission(doctype_name, "read", user=user):
			frappe.throw(_("No permission to access {0}").format(doctype_name))
		
		# Parse updates if string
		if isinstance(filter_updates, str):
			filter_updates = json.loads(filter_updates)
		
		# Get preference service
		from column_management.column_management.services.preference_service import PreferenceService
		service = PreferenceService()
		
		# Update filter preferences
		success = service.update_filter_preferences(user, doctype_name, filter_updates)
		
		return {
			"success": success,
			"message": _("Filter preferences updated successfully") if success else _("Failed to update filter preferences")
		}
		
	except Exception as e:
		frappe.log_error(f"Error updating filter preferences: {str(e)}")
		return {
			"success": False,
			"error": str(e)
		}

@frappe.whitelist()
def update_pagination_preferences(doctype_name, pagination_updates, user=None):
	"""Update pagination preferences"""
	try:
		if not user:
			user = frappe.session.user
		
		# Check permissions
		if not frappe.has_permission(doctype_name, "read", user=user):
			frappe.throw(_("No permission to access {0}").format(doctype_name))
		
		# Parse updates if string
		if isinstance(pagination_updates, str):
			pagination_updates = json.loads(pagination_updates)
		
		# Get preference service
		from column_management.column_management.services.preference_service import PreferenceService
		service = PreferenceService()
		
		# Update pagination preferences
		success = service.update_pagination_preferences(user, doctype_name, pagination_updates)
		
		return {
			"success": success,
			"message": _("Pagination preferences updated successfully") if success else _("Failed to update pagination preferences")
		}
		
	except Exception as e:
		frappe.log_error(f"Error updating pagination preferences: {str(e)}")
		return {
			"success": False,
			"error": str(e)
		}

@frappe.whitelist()
def auto_save_preferences(doctype_name, preference_type, updates, user=None):
	"""Auto-save preferences with debouncing"""
	try:
		if not user:
			user = frappe.session.user
		
		# Check permissions
		if not frappe.has_permission(doctype_name, "read", user=user):
			return {"success": False, "error": "No permission"}
		
		# Parse updates if string
		if isinstance(updates, str):
			updates = json.loads(updates)
		
		# Get preference service
		from column_management.column_management.services.preference_service import PreferenceService
		service = PreferenceService()
		
		# Auto-save preferences
		success = service.auto_save_preferences(user, doctype_name, preference_type, updates)
		
		return {
			"success": success
		}
		
	except Exception as e:
		frappe.log_error(f"Error in auto-save preferences: {str(e)}")
		return {
			"success": False,
			"error": str(e)
		}

@frappe.whitelist()
def restore_preferences_on_login(user=None):
	"""Restore user preferences when user logs in"""
	try:
		if not user:
			user = frappe.session.user
		
		# Get preference service
		from column_management.column_management.services.preference_service import PreferenceService
		service = PreferenceService()
		
		# Restore preferences
		restored_count = service.restore_preferences_on_login(user)
		
		return {
			"success": True,
			"restored_count": restored_count,
			"message": _("Restored {0} preferences").format(restored_count)
		}
		
	except Exception as e:
		frappe.log_error(f"Error restoring preferences on login: {str(e)}")
		return {
			"success": False,
			"error": str(e)
		}

@frappe.whitelist()
def reset_to_defaults(doctype_name, user=None):
	"""Reset user preferences to default values"""
	try:
		if not user:
			user = frappe.session.user
		
		# Check permissions
		if not frappe.has_permission(doctype_name, "read", user=user):
			frappe.throw(_("No permission to access {0}").format(doctype_name))
		
		# Get preference service
		from column_management.column_management.services.preference_service import PreferenceService
		service = PreferenceService()
		
		# Reset to defaults
		default_preferences = service.reset_to_defaults(user, doctype_name)
		
		return {
			"success": True,
			"preferences": default_preferences,
			"message": _("Preferences reset to defaults successfully")
		}
		
	except Exception as e:
		frappe.log_error(f"Error resetting preferences to defaults: {str(e)}")
		return {
			"success": False,
			"error": str(e)
		}

@frappe.whitelist()
def export_user_preferences(doctype_names=None, user=None):
	"""Export user preferences for backup"""
	try:
		if not user:
			user = frappe.session.user
		
		# Parse doctype_names if string
		if isinstance(doctype_names, str):
			doctype_names = json.loads(doctype_names) if doctype_names else None
		
		# Get preference service
		from column_management.column_management.services.preference_service import PreferenceService
		service = PreferenceService()
		
		# Export preferences
		export_data = service.export_user_preferences(user, doctype_names)
		
		return {
			"success": True,
			"export_data": export_data,
			"message": _("Preferences exported successfully")
		}
		
	except Exception as e:
		frappe.log_error(f"Error exporting user preferences: {str(e)}")
		return {
			"success": False,
			"error": str(e)
		}

@frappe.whitelist()
def import_user_preferences(import_data, overwrite=False, user=None):
	"""Import user preferences from backup"""
	try:
		if not user:
			user = frappe.session.user
		
		# Parse import_data if string
		if isinstance(import_data, str):
			import_data = json.loads(import_data)
		
		# Parse overwrite if string
		if isinstance(overwrite, str):
			overwrite = overwrite.lower() in ['true', '1', 'yes']
		
		# Get preference service
		from column_management.column_management.services.preference_service import PreferenceService
		service = PreferenceService()
		
		# Import preferences
		imported_count = service.import_user_preferences(user, import_data, overwrite)
		
		return {
			"success": True,
			"imported_count": imported_count,
			"message": _("Imported {0} preferences successfully").format(imported_count)
		}
		
	except Exception as e:
		frappe.log_error(f"Error importing user preferences: {str(e)}")
		return {
			"success": False,
			"error": str(e)
		}

@frappe.whitelist()
def get_preference_summary(user=None):
	"""Get summary of user's preferences across all doctypes"""
	try:
		if not user:
			user = frappe.session.user
		
		# Get preference service
		from column_management.column_management.services.preference_service import PreferenceService
		service = PreferenceService()
		
		# Get summary
		summary = service.get_preference_summary(user)
		
		return {
			"success": True,
			"summary": summary
		}
		
	except Exception as e:
		frappe.log_error(f"Error getting preference summary: {str(e)}")
		return {
			"success": False,
			"error": str(e)
		}

@frappe.whitelist()
def get_preference_history(doctype_name, limit=10, user=None):
	"""Get preference change history"""
	try:
		if not user:
			user = frappe.session.user
		
		# Check permissions
		if not frappe.has_permission(doctype_name, "read", user=user):
			frappe.throw(_("No permission to access {0}").format(doctype_name))
		
		# Parse limit if string
		if isinstance(limit, str):
			limit = int(limit)
		
		# Get preference service
		from column_management.column_management.services.preference_service import PreferenceService
		service = PreferenceService()
		
		# Get history
		history = service.get_preference_history(user, doctype_name, limit)
		
		return {
			"success": True,
			"history": history
		}
		
	except Exception as e:
		frappe.log_error(f"Error getting preference history: {str(e)}")
		return {
			"success": False,
			"error": str(e)
		}

@frappe.whitelist()
def bulk_update_preferences(updates, user=None):
	"""Bulk update multiple preference types at once"""
	try:
		if not user:
			user = frappe.session.user
		
		# Parse updates if string
		if isinstance(updates, str):
			updates = json.loads(updates)
		
		# Validate updates structure
		if not isinstance(updates, dict) or "doctype_name" not in updates:
			frappe.throw(_("Invalid updates format"))
		
		doctype_name = updates["doctype_name"]
		
		# Check permissions
		if not frappe.has_permission(doctype_name, "read", user=user):
			frappe.throw(_("No permission to access {0}").format(doctype_name))
		
		# Get preference service
		from column_management.column_management.services.preference_service import PreferenceService
		service = PreferenceService()
		
		results = {}
		
		# Process each type of update
		if "columns" in updates:
			results["columns"] = service.update_column_preferences(
				user, doctype_name, updates["columns"]
			)
		
		if "filters" in updates:
			results["filters"] = service.update_filter_preferences(
				user, doctype_name, updates["filters"]
			)
		
		if "pagination" in updates:
			results["pagination"] = service.update_pagination_preferences(
				user, doctype_name, updates["pagination"]
			)
		
		if "sorting" in updates:
			results["sorting"] = service.update_sorting_preferences(
				user, doctype_name, updates["sorting"]
			)
		
		if "view_settings" in updates:
			results["view_settings"] = service.update_view_settings(
				user, doctype_name, updates["view_settings"]
			)
		
		# Check if all updates were successful
		all_success = all(results.values())
		
		# Sync across sessions if successful
		if all_success:
			from column_management.column_management.services.preference_sync_service import PreferenceSyncService
			sync_service = PreferenceSyncService()
			sync_service.sync_preferences_across_sessions(user, doctype_name)
		
		return {
			"success": all_success,
			"results": results,
			"message": _("Bulk update completed") if all_success else _("Some updates failed")
		}
		
	except Exception as e:
		frappe.log_error(f"Error in bulk update preferences: {str(e)}")
		return {
			"success": False,
			"error": str(e)
		}

# Synchronization and Backup APIs

@frappe.whitelist()
def sync_preferences_across_sessions(doctype_name, user=None):
	"""Synchronize preferences across multiple user sessions"""
	try:
		if not user:
			user = frappe.session.user
		
		# Check permissions
		if not frappe.has_permission(doctype_name, "read", user=user):
			frappe.throw(_("No permission to access {0}").format(doctype_name))
		
		# Get sync service
		from column_management.column_management.services.preference_sync_service import PreferenceSyncService
		service = PreferenceSyncService()
		
		# Sync preferences
		success = service.sync_preferences_across_sessions(user, doctype_name)
		
		return {
			"success": success,
			"message": _("Preferences synchronized successfully") if success else _("Failed to synchronize preferences")
		}
		
	except Exception as e:
		frappe.log_error(f"Error synchronizing preferences: {str(e)}")
		return {
			"success": False,
			"error": str(e)
		}

@frappe.whitelist()
def create_preference_backup(doctype_name=None, backup_type="manual", description=None, user=None):
	"""Create a backup of user preferences"""
	try:
		if not user:
			user = frappe.session.user
		
		# Check permissions if specific doctype
		if doctype_name and not frappe.has_permission(doctype_name, "read", user=user):
			frappe.throw(_("No permission to access {0}").format(doctype_name))
		
		# Get sync service
		from column_management.column_management.services.preference_sync_service import PreferenceSyncService
		service = PreferenceSyncService()
		
		# Create backup
		backup_name = service.create_preference_backup(user, doctype_name, backup_type)
		
		if backup_name and description:
			# Update description
			backup_doc = frappe.get_doc("Preference Backup", backup_name)
			backup_doc.description = description
			backup_doc.save(ignore_permissions=True)
		
		return {
			"success": bool(backup_name),
			"backup_name": backup_name,
			"message": _("Backup created successfully") if backup_name else _("Failed to create backup")
		}
		
	except Exception as e:
		frappe.log_error(f"Error creating preference backup: {str(e)}")
		return {
			"success": False,
			"error": str(e)
		}

@frappe.whitelist()
def restore_preference_backup(backup_name, user=None):
	"""Restore preferences from a backup"""
	try:
		if not user:
			user = frappe.session.user
		
		# Get sync service
		from column_management.column_management.services.preference_sync_service import PreferenceSyncService
		service = PreferenceSyncService()
		
		# Restore backup
		restored_count = service.restore_preference_backup(backup_name, user)
		
		return {
			"success": restored_count > 0,
			"restored_count": restored_count,
			"message": _("Restored {0} preferences successfully").format(restored_count) if restored_count > 0 else _("No preferences restored")
		}
		
	except Exception as e:
		frappe.log_error(f"Error restoring preference backup: {str(e)}")
		return {
			"success": False,
			"error": str(e)
		}

@frappe.whitelist()
def get_preference_backups(doctype_name=None, limit=10, user=None):
	"""Get list of preference backups for a user"""
	try:
		if not user:
			user = frappe.session.user
		
		# Parse limit if string
		if isinstance(limit, str):
			limit = int(limit)
		
		# Get sync service
		from column_management.column_management.services.preference_sync_service import PreferenceSyncService
		service = PreferenceSyncService()
		
		# Get backups
		backups = service.get_preference_backups(user, doctype_name, limit)
		
		return {
			"success": True,
			"backups": backups
		}
		
	except Exception as e:
		frappe.log_error(f"Error getting preference backups: {str(e)}")
		return {
			"success": False,
			"error": str(e)
		}

@frappe.whitelist()
def delete_preference_backup(backup_name, user=None):
	"""Delete a preference backup"""
	try:
		if not user:
			user = frappe.session.user
		
		# Get sync service
		from column_management.column_management.services.preference_sync_service import PreferenceSyncService
		service = PreferenceSyncService()
		
		# Delete backup
		success = service.delete_preference_backup(backup_name, user)
		
		return {
			"success": success,
			"message": _("Backup deleted successfully") if success else _("Failed to delete backup")
		}
		
	except Exception as e:
		frappe.log_error(f"Error deleting preference backup: {str(e)}")
		return {
			"success": False,
			"error": str(e)
		}

@frappe.whitelist()
def reset_to_default_configuration(doctype_name, user=None):
	"""Reset user preferences to default configuration with backup"""
	try:
		if not user:
			user = frappe.session.user
		
		# Check permissions
		if not frappe.has_permission(doctype_name, "read", user=user):
			frappe.throw(_("No permission to access {0}").format(doctype_name))
		
		# Get sync service
		from column_management.column_management.services.preference_sync_service import PreferenceSyncService
		service = PreferenceSyncService()
		
		# Reset to defaults
		result = service.reset_to_default_configuration(user, doctype_name)
		
		return {
			"success": result["success"],
			"backup_name": result["backup_name"],
			"default_preferences": result["default_preferences"],
			"message": _("Preferences reset to defaults successfully")
		}
		
	except Exception as e:
		frappe.log_error(f"Error resetting to default configuration: {str(e)}")
		return {
			"success": False,
			"error": str(e)
		}

@frappe.whitelist()
def get_sync_status(doctype_name, user=None):
	"""Get synchronization status for user preferences"""
	try:
		if not user:
			user = frappe.session.user
		
		# Check permissions
		if not frappe.has_permission(doctype_name, "read", user=user):
			frappe.throw(_("No permission to access {0}").format(doctype_name))
		
		# Get sync service
		from column_management.column_management.services.preference_sync_service import PreferenceSyncService
		service = PreferenceSyncService()
		
		# Get sync status
		status = service.get_sync_status(user, doctype_name)
		
		return {
			"success": True,
			"sync_status": status
		}
		
	except Exception as e:
		frappe.log_error(f"Error getting sync status: {str(e)}")
		return {
			"success": False,
			"error": str(e)
		}

@frappe.whitelist()
def force_sync_all_sessions(user=None):
	"""Force synchronization of all preferences across all user sessions"""
	try:
		if not user:
			user = frappe.session.user
		
		# Get sync service
		from column_management.column_management.services.preference_sync_service import PreferenceSyncService
		service = PreferenceSyncService()
		
		# Force sync all sessions
		synced_count = service.force_sync_all_sessions(user)
		
		return {
			"success": synced_count > 0,
			"synced_count": synced_count,
			"message": _("Synchronized {0} preferences across all sessions").format(synced_count)
		}
		
	except Exception as e:
		frappe.log_error(f"Error force syncing all sessions: {str(e)}")
		return {
			"success": False,
			"error": str(e)
		}

@frappe.whitelist()
def get_preference_statistics(user=None):
	"""Get statistics about user's preferences and backups"""
	try:
		if not user:
			user = frappe.session.user
		
		# Get sync service
		from column_management.column_management.services.preference_sync_service import PreferenceSyncService
		service = PreferenceSyncService()
		
		# Get statistics
		statistics = service.get_preference_statistics(user)
		
		return {
			"success": True,
			"statistics": statistics
		}
		
	except Exception as e:
		frappe.log_error(f"Error getting preference statistics: {str(e)}")
		return {
			"success": False,
			"error": str(e)
		}