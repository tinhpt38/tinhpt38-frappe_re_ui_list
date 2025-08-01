# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import frappe
from frappe.utils import cint

def after_install():
	"""Setup after app installation"""
	try:
		# Wait for all DocTypes to be created first
		frappe.db.commit()
		
		# Setup in order of dependency
		setup_permissions()
		create_default_statistics_config()
		create_custom_fields()
		
		frappe.db.commit()
		frappe.msgprint("Column Management app installed successfully!", alert=True)
		print("Column Management app installed successfully!")
		
	except Exception as e:
		error_msg = f"Error during Column Management installation: {str(e)}"
		frappe.log_error(error_msg, "Column Management Installation Error")
		print(f"Installation completed with warnings: {str(e)}")
		# Don't fail the installation, just log the error

def create_default_statistics_config():
	"""Create default statistics configurations for common DocTypes"""
	# Only create if Statistics Config DocType exists
	if not frappe.db.exists("DocType", "Statistics Config"):
		print("Statistics Config DocType not found, skipping default config creation")
		return
		
	default_configs = [
		{
			'doctype_name': 'Sales Invoice',
			'statistic_name': 'Total Amount',
			'field_name': 'grand_total',
			'calculation_type': 'Sum',
			'format_string': 'Currency',
			'is_active': 1
		},
		{
			'doctype_name': 'Sales Invoice',
			'statistic_name': 'Count',
			'field_name': 'name',
			'calculation_type': 'Count',
			'format_string': 'Int',
			'is_active': 1
		},
		{
			'doctype_name': 'Purchase Invoice',
			'statistic_name': 'Total Amount',
			'field_name': 'grand_total',
			'calculation_type': 'Sum',
			'format_string': 'Currency',
			'is_active': 1
		},
		{
			'doctype_name': 'Purchase Invoice',
			'statistic_name': 'Count',
			'field_name': 'name',
			'calculation_type': 'Count',
			'format_string': 'Int',
			'is_active': 1
		}
	]
	
	try:
		for config in default_configs:
			# Check if ERPNext DocTypes exist before creating configs
			if frappe.db.exists("DocType", config['doctype_name']):
				if not frappe.db.exists('Statistics Config', {
					'doctype_name': config['doctype_name'],
					'statistic_name': config['statistic_name']
				}):
					doc = frappe.get_doc({
						'doctype': 'Statistics Config',
						**config
					})
					doc.insert(ignore_permissions=True)
					print(f"Created default statistics config for {config['doctype_name']}")
	except Exception as e:
		frappe.log_error(f"Error creating default statistics config: {str(e)}")

def setup_permissions():
	"""Setup default permissions for column management"""
	try:
		# Define the DocTypes and their required permissions
		doctype_permissions = {
			'Column Config': ['System Manager', 'System User'],
			'User Column Preference': ['System Manager', 'System User'],
			'Saved Filter': ['System Manager', 'System User'],
			'Statistics Config': ['System Manager']
		}
		
		for doctype_name, roles in doctype_permissions.items():
			# Only setup permissions if DocType exists
			if not frappe.db.exists("DocType", doctype_name):
				continue
				
			for role in roles:
				if not frappe.db.exists("DocPerm", {
					"parent": doctype_name,
					"role": role
				}):
					# Create permission record
					perm_doc = frappe.get_doc({
						"doctype": "DocPerm",
						"parent": doctype_name,
						"parenttype": "DocType",
						"parentfield": "permissions",
						"role": role,
						"read": 1,
						"write": 1 if role == "System Manager" else 0,
						"create": 1 if role == "System Manager" else 0,
						"delete": 1 if role == "System Manager" else 0,
						"submit": 0,
						"cancel": 0,
						"amend": 0,
						"report": 1,
						"export": 1,
						"import": 1 if role == "System Manager" else 0,
						"share": 1,
						"print": 1,
						"email": 1
					})
					perm_doc.insert(ignore_permissions=True)
					print(f"Created permissions for {doctype_name} - {role}")
					
	except Exception as e:
		frappe.log_error(f"Error setting up permissions: {str(e)}")

def create_custom_fields():
	"""Create custom fields if needed"""
	try:
		# Add column_management_enabled field to User DocType
		if not frappe.db.exists("Custom Field", {"dt": "User", "fieldname": "column_management_enabled"}):
			custom_field = frappe.get_doc({
				"doctype": "Custom Field",
				"dt": "User",
				"label": "Column Management Enabled",
				"fieldname": "column_management_enabled",
				"fieldtype": "Check",
				"default": "1",
				"insert_after": "enabled",
				"description": "Enable column management features for this user"
			})
			custom_field.insert(ignore_permissions=True)
			print("Created column_management_enabled field in User DocType")
			
	except Exception as e:
		frappe.log_error(f"Error creating custom fields: {str(e)}")

def before_uninstall():
	"""Cleanup before app uninstallation"""
	try:
		print("Starting Column Management app cleanup...")
		
		# Remove custom fields
		custom_fields = frappe.get_all("Custom Field", 
			filters={"fieldname": ["like", "%column_management%"]},
			fields=["name"])
		
		for field in custom_fields:
			frappe.delete_doc("Custom Field", field.name, ignore_permissions=True)
			
		# Clean up data from our DocTypes (only if they exist)
		cleanup_tables = [
			"Column Config",
			"User Column Preference", 
			"Saved Filter",
			"Statistics Config"
		]
		
		for table in cleanup_tables:
			if frappe.db.exists("DocType", table):
				frappe.db.sql(f"DELETE FROM `tab{table}`")
				print(f"Cleaned up data from {table}")
		
		# Remove permissions
		for table in cleanup_tables:
			frappe.db.sql("""
				DELETE FROM `tabDocPerm` 
				WHERE parent = %s AND parenttype = 'DocType'
			""", (table,))
			
		frappe.db.commit()
		print("Column Management app data cleaned up successfully!")
		
	except Exception as e:
		error_msg = f"Error during Column Management cleanup: {str(e)}"
		frappe.log_error(error_msg, "Column Management Cleanup Error")
		print(f"Cleanup completed with warnings: {str(e)}")

def validate_installation():
	"""Validate that the app is properly installed"""
	try:
		required_doctypes = [
			"Column Config",
			"User Column Preference",
			"Saved Filter", 
			"Statistics Config"
		]
		
		missing_doctypes = []
		for doctype in required_doctypes:
			if not frappe.db.exists("DocType", doctype):
				missing_doctypes.append(doctype)
		
		if missing_doctypes:
			frappe.throw(f"Installation incomplete. Missing DocTypes: {', '.join(missing_doctypes)}")
		
		print("Column Management installation validation passed!")
		return True
		
	except Exception as e:
		frappe.log_error(f"Installation validation failed: {str(e)}")
		return False