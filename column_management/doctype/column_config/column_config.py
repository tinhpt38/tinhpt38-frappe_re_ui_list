# -*- coding: utf-8 -*-
# Copyright (c) 2024, ERPNext Column Management Team and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe import _

class ColumnConfig(Document):
	def validate(self):
		"""Validate column configuration data"""
		self.validate_width()
		self.validate_doctype_exists()
		self.validate_field_exists()
		self.validate_unique_config()
		self.set_timestamps()
	
	def validate_width(self):
		"""Validate column width constraints"""
		if self.width < 50:
			frappe.throw(_("Column width cannot be less than 50 pixels"))
		
		if self.width > 1000:
			frappe.throw(_("Column width cannot be more than 1000 pixels"))
	
	def validate_doctype_exists(self):
		"""Validate that the DocType exists"""
		if not frappe.db.exists("DocType", self.doctype_name):
			frappe.throw(_("DocType {0} does not exist").format(self.doctype_name))
	
	def validate_field_exists(self):
		"""Validate that the field exists in the DocType"""
		if self.doctype_name and self.fieldname:
			# Get DocType meta
			meta = frappe.get_meta(self.doctype_name)
			
			# Check if field exists
			if not meta.get_field(self.fieldname):
				frappe.throw(_("Field {0} does not exist in DocType {1}").format(
					self.fieldname, self.doctype_name))
	
	def validate_unique_config(self):
		"""Ensure unique configuration per user, doctype, and field"""
		existing = frappe.db.get_value("Column Config", {
			"doctype_name": self.doctype_name,
			"user": self.user,
			"fieldname": self.fieldname,
			"name": ["!=", self.name]
		})
		
		if existing:
			frappe.throw(_("Column configuration already exists for {0} - {1} - {2}").format(
				self.doctype_name, self.user, self.fieldname))
	
	def set_timestamps(self):
		"""Set created_at and modified_at timestamps"""
		now = frappe.utils.now()
		
		if self.is_new():
			self.created_at = now
		
		self.modified_at = now
	
	def before_save(self):
		"""Actions before saving the document"""
		# Set default label if not provided
		if not self.label and self.doctype_name and self.fieldname:
			try:
				meta = frappe.get_meta(self.doctype_name)
				field = meta.get_field(self.fieldname)
				if field:
					self.label = field.label or self.fieldname.replace("_", " ").title()
			except:
				self.label = self.fieldname.replace("_", " ").title()
	
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
			service.clear_user_cache(self.doctype_name, self.user)
		except ImportError:
			pass
	
	@staticmethod
	def get_user_columns(doctype_name, user):
		"""Get column configuration for a user and doctype"""
		return frappe.get_all("Column Config", 
			filters={
				"doctype_name": doctype_name,
				"user": user
			},
			fields=["fieldname", "label", "width", "pinned", "visible", "order"],
			order_by="order asc, fieldname asc"
		)
	
	@staticmethod
	def create_default_config(doctype_name, user, fieldname, label=None, width=100, visible=1, order=0):
		"""Create default column configuration"""
		if not frappe.db.exists("Column Config", {
			"doctype_name": doctype_name,
			"user": user,
			"fieldname": fieldname
		}):
			doc = frappe.get_doc({
				"doctype": "Column Config",
				"doctype_name": doctype_name,
				"user": user,
				"fieldname": fieldname,
				"label": label or fieldname.replace("_", " ").title(),
				"width": width,
				"visible": visible,
				"order": order
			})
			doc.insert(ignore_permissions=True)
			return doc
		return None