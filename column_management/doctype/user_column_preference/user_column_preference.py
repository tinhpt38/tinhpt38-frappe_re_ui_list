# -*- coding: utf-8 -*-
# Copyright (c) 2024, ERPNext Column Management Team and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import json
from frappe.model.document import Document
from frappe import _

class UserColumnPreference(Document):
	def validate(self):
		"""Validate user column preference data"""
		self.validate_doctype_exists()
		self.validate_unique_preference()
		self.validate_preference_data()
		self.set_timestamps()
	
	def validate_doctype_exists(self):
		"""Validate that the DocType exists"""
		if not frappe.db.exists("DocType", self.doctype_name):
			frappe.throw(_("DocType {0} does not exist").format(self.doctype_name))
	
	def validate_unique_preference(self):
		"""Ensure unique preference per user and doctype"""
		existing = frappe.db.get_value("User Column Preference", {
			"user": self.user,
			"doctype_name": self.doctype_name,
			"name": ["!=", self.name]
		})
		
		if existing:
			frappe.throw(_("Column preference already exists for {0} - {1}").format(
				self.user, self.doctype_name))
	
	def validate_preference_data(self):
		"""Validate preference data structure"""
		if self.preference_data:
			try:
				if isinstance(self.preference_data, str):
					data = json.loads(self.preference_data)
				else:
					data = self.preference_data
				
				# Validate required structure
				if not isinstance(data, dict):
					frappe.throw(_("Preference data must be a valid JSON object"))
				
				# Validate columns structure if present
				if 'columns' in data:
					if not isinstance(data['columns'], list):
						frappe.throw(_("Columns data must be a list"))
					
					for column in data['columns']:
						if not isinstance(column, dict):
							frappe.throw(_("Each column must be a dictionary"))
						
						required_fields = ['fieldname', 'visible', 'width']
						for field in required_fields:
							if field not in column:
								frappe.throw(_("Column data missing required field: {0}").format(field))
			
			except json.JSONDecodeError:
				frappe.throw(_("Invalid JSON format in preference data"))
	
	def set_timestamps(self):
		"""Set created_at and modified_at timestamps"""
		now = frappe.utils.now()
		
		if self.is_new():
			self.created_at = now
		
		self.modified_at = now
	
	def before_save(self):
		"""Actions before saving the document"""
		# Serialize preference data if it's a dict
		if isinstance(self.preference_data, dict):
			self.preference_data = json.dumps(self.preference_data, indent=2)
	
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
	
	def get_preference_data(self):
		"""Get deserialized preference data"""
		if not self.preference_data:
			return {}
		
		try:
			if isinstance(self.preference_data, str):
				return json.loads(self.preference_data)
			else:
				return self.preference_data
		except json.JSONDecodeError:
			return {}
	
	def set_preference_data(self, data):
		"""Set preference data with validation"""
		if not isinstance(data, dict):
			frappe.throw(_("Preference data must be a dictionary"))
		
		self.preference_data = data
		self.validate_preference_data()
	
	def update_column_preferences(self, columns):
		"""Update column preferences"""
		data = self.get_preference_data()
		data['columns'] = columns
		self.set_preference_data(data)
	
	def update_filter_preferences(self, filters):
		"""Update filter preferences"""
		data = self.get_preference_data()
		data['filters'] = filters
		self.set_preference_data(data)
	
	def update_pagination_preferences(self, pagination):
		"""Update pagination preferences"""
		data = self.get_preference_data()
		data['pagination'] = pagination
		self.set_preference_data(data)
	
	@staticmethod
	def get_user_preference(user, doctype_name):
		"""Get user preference for a doctype"""
		doc = frappe.db.get_value("User Column Preference", {
			"user": user,
			"doctype_name": doctype_name
		}, ["name", "preference_data"], as_dict=True)
		
		if doc:
			preference = frappe.get_doc("User Column Preference", doc.name)
			return preference.get_preference_data()
		
		return {}
	
	@staticmethod
	def create_or_update_preference(user, doctype_name, preference_data, is_default=False):
		"""Create or update user preference"""
		existing = frappe.db.get_value("User Column Preference", {
			"user": user,
			"doctype_name": doctype_name
		})
		
		if existing:
			doc = frappe.get_doc("User Column Preference", existing)
			doc.set_preference_data(preference_data)
			doc.is_default = is_default
			doc.save(ignore_permissions=True)
		else:
			doc = frappe.get_doc({
				"doctype": "User Column Preference",
				"user": user,
				"doctype_name": doctype_name,
				"preference_data": preference_data,
				"is_default": is_default
			})
			doc.insert(ignore_permissions=True)
		
		return doc