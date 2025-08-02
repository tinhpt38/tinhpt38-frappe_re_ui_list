# -*- coding: utf-8 -*-
# Copyright (c) 2024, ERPNext Column Management Team and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import json
from frappe import _

class MetadataService:
	def __init__(self):
		self.cache = frappe.cache()
		self.cache_prefix = "column_management_metadata"
		self.cache_ttl = 7200  # 2 hours - metadata changes less frequently
	
	def get_doctype_metadata(self, doctype):
		"""Get comprehensive metadata for a DocType"""
		cache_key = f"{self.cache_prefix}:doctype:{doctype}"
		
		# Try to get from cache first
		cached_metadata = self.cache.get(cache_key)
		if cached_metadata:
			return json.loads(cached_metadata)
		
		# Get from database
		metadata = self._fetch_doctype_metadata(doctype)
		
		# Cache the result
		self.cache.set(cache_key, json.dumps(metadata), self.cache_ttl)
		
		return metadata
	
	def _fetch_doctype_metadata(self, doctype):
		"""Fetch DocType metadata from database"""
		try:
			# Check if DocType exists
			if not frappe.db.exists("DocType", doctype):
				frappe.throw(_("DocType {0} does not exist").format(doctype))
			
			meta = frappe.get_meta(doctype)
			
			metadata = {
				"name": doctype,
				"module": meta.module,
				"title_field": meta.title_field,
				"search_fields": meta.search_fields,
				"sort_field": meta.sort_field,
				"sort_order": meta.sort_order,
				"is_submittable": meta.is_submittable,
				"is_tree": meta.is_tree,
				"has_web_view": meta.has_web_view,
				"allow_rename": meta.allow_rename,
				"fields": [],
				"links": [],
				"permissions": []
			}
			
			# Process fields
			for field in meta.fields:
				field_metadata = self._get_field_metadata_dict(field)
				metadata["fields"].append(field_metadata)
			
			# Add standard fields
			standard_fields = self._get_standard_fields()
			metadata["fields"].extend(standard_fields)
			
			# Process links (child tables, etc.)
			for link in meta.links:
				link_metadata = {
					"link_doctype": link.link_doctype,
					"link_fieldname": link.link_fieldname,
					"table_fieldname": link.table_fieldname,
					"group": link.group
				}
				metadata["links"].append(link_metadata)
			
			# Process permissions
			for perm in meta.permissions:
				perm_metadata = {
					"role": perm.role,
					"read": perm.read,
					"write": perm.write,
					"create": perm.create,
					"delete": perm.delete,
					"submit": perm.submit,
					"cancel": perm.cancel,
					"amend": perm.amend
				}
				metadata["permissions"].append(perm_metadata)
			
			return metadata
			
		except Exception as e:
			frappe.log_error(f"Error fetching DocType metadata: {str(e)}")
			frappe.throw(_("Failed to get DocType metadata: {0}").format(str(e)))
	
	def get_field_metadata(self, doctype, fieldname):
		"""Get metadata for a specific field"""
		cache_key = f"{self.cache_prefix}:field:{doctype}:{fieldname}"
		
		# Try to get from cache first
		cached_field = self.cache.get(cache_key)
		if cached_field:
			return json.loads(cached_field)
		
		# Get from DocType metadata
		doctype_metadata = self.get_doctype_metadata(doctype)
		
		# Find the field
		field_metadata = None
		for field in doctype_metadata["fields"]:
			if field["fieldname"] == fieldname:
				field_metadata = field
				break
		
		if not field_metadata:
			frappe.throw(_("Field {0} does not exist in DocType {1}").format(fieldname, doctype))
		
		# Cache the result
		self.cache.set(cache_key, json.dumps(field_metadata), self.cache_ttl)
		
		return field_metadata
	
	def _get_field_metadata_dict(self, field):
		"""Convert field object to metadata dictionary"""
		return {
			"fieldname": field.fieldname,
			"label": field.label or field.fieldname.replace("_", " ").title(),
			"fieldtype": field.fieldtype,
			"options": field.options,
			"reqd": field.reqd,
			"unique": field.unique,
			"read_only": field.read_only,
			"hidden": field.hidden,
			"in_list_view": field.in_list_view,
			"in_standard_filter": field.in_standard_filter,
			"in_global_search": field.in_global_search,
			"search_index": field.search_index,
			"default": field.default,
			"description": field.description,
			"width": field.width,
			"precision": field.precision,
			"length": field.length,
			"depends_on": field.depends_on,
			"mandatory_depends_on": field.mandatory_depends_on,
			"read_only_depends_on": field.read_only_depends_on,
			"idx": field.idx,
			"is_virtual": 0,
			"sortable": 1 if field.fieldtype not in ["Text", "Long Text", "HTML Editor", "Attach", "Attach Image"] else 0,
			"filterable": 1 if field.fieldtype not in ["HTML Editor", "Text Editor"] else 0
		}
	
	def _get_standard_fields(self):
		"""Get standard fields that exist in all DocTypes"""
		return [
			{
				"fieldname": "name",
				"label": "ID",
				"fieldtype": "Data",
				"options": None,
				"reqd": 1,
				"unique": 1,
				"read_only": 1,
				"hidden": 0,
				"in_list_view": 1,
				"in_standard_filter": 1,
				"in_global_search": 1,
				"search_index": 1,
				"default": None,
				"description": "Unique identifier for the document",
				"width": None,
				"precision": None,
				"length": 140,
				"depends_on": None,
				"mandatory_depends_on": None,
				"read_only_depends_on": None,
				"idx": 0,
				"is_virtual": 0,
				"sortable": 1,
				"filterable": 1
			},
			{
				"fieldname": "owner",
				"label": "Created By",
				"fieldtype": "Link",
				"options": "User",
				"reqd": 0,
				"unique": 0,
				"read_only": 1,
				"hidden": 0,
				"in_list_view": 0,
				"in_standard_filter": 1,
				"in_global_search": 0,
				"search_index": 1,
				"default": None,
				"description": "User who created this document",
				"width": None,
				"precision": None,
				"length": 140,
				"depends_on": None,
				"mandatory_depends_on": None,
				"read_only_depends_on": None,
				"idx": 9997,
				"is_virtual": 0,
				"sortable": 1,
				"filterable": 1
			},
			{
				"fieldname": "creation",
				"label": "Created On",
				"fieldtype": "Datetime",
				"options": None,
				"reqd": 0,
				"unique": 0,
				"read_only": 1,
				"hidden": 0,
				"in_list_view": 0,
				"in_standard_filter": 1,
				"in_global_search": 0,
				"search_index": 1,
				"default": None,
				"description": "Date and time when document was created",
				"width": None,
				"precision": None,
				"length": None,
				"depends_on": None,
				"mandatory_depends_on": None,
				"read_only_depends_on": None,
				"idx": 9998,
				"is_virtual": 0,
				"sortable": 1,
				"filterable": 1
			},
			{
				"fieldname": "modified",
				"label": "Last Modified",
				"fieldtype": "Datetime",
				"options": None,
				"reqd": 0,
				"unique": 0,
				"read_only": 1,
				"hidden": 0,
				"in_list_view": 0,
				"in_standard_filter": 1,
				"in_global_search": 0,
				"search_index": 1,
				"default": None,
				"description": "Date and time when document was last modified",
				"width": None,
				"precision": None,
				"length": None,
				"depends_on": None,
				"mandatory_depends_on": None,
				"read_only_depends_on": None,
				"idx": 9999,
				"is_virtual": 0,
				"sortable": 1,
				"filterable": 1
			},
			{
				"fieldname": "modified_by",
				"label": "Last Modified By",
				"fieldtype": "Link",
				"options": "User",
				"reqd": 0,
				"unique": 0,
				"read_only": 1,
				"hidden": 0,
				"in_list_view": 0,
				"in_standard_filter": 1,
				"in_global_search": 0,
				"search_index": 1,
				"default": None,
				"description": "User who last modified this document",
				"width": None,
				"precision": None,
				"length": 140,
				"depends_on": None,
				"mandatory_depends_on": None,
				"read_only_depends_on": None,
				"idx": 10000,
				"is_virtual": 0,
				"sortable": 1,
				"filterable": 1
			}
		]
	
	def get_link_field_options(self, doctype, fieldname):
		"""Get options for link fields"""
		cache_key = f"{self.cache_prefix}:link_options:{doctype}:{fieldname}"
		
		# Try to get from cache first
		cached_options = self.cache.get(cache_key)
		if cached_options:
			return json.loads(cached_options)
		
		# Get field metadata
		field_metadata = self.get_field_metadata(doctype, fieldname)
		
		if field_metadata["fieldtype"] not in ["Link", "Dynamic Link"]:
			return []
		
		options = []
		
		try:
			if field_metadata["fieldtype"] == "Link":
				# Get options from linked DocType
				link_doctype = field_metadata["options"]
				if link_doctype:
					# Get first 100 records for performance
					link_options = frappe.get_all(link_doctype,
						fields=["name", "title"],
						limit=100,
						order_by="name asc"
					)
					
					for option in link_options:
						options.append({
							"value": option["name"],
							"label": option.get("title") or option["name"]
						})
			
			elif field_metadata["fieldtype"] == "Select":
				# Get select options
				if field_metadata["options"]:
					select_options = field_metadata["options"].split("\n")
					for option in select_options:
						option = option.strip()
						if option:
							options.append({
								"value": option,
								"label": option
							})
			
			# Cache the result
			self.cache.set(cache_key, json.dumps(options), self.cache_ttl)
			
			return options
			
		except Exception as e:
			frappe.log_error(f"Error getting link field options: {str(e)}")
			return []
	
	def get_filterable_fields(self, doctype):
		"""Get fields that can be used for filtering"""
		doctype_metadata = self.get_doctype_metadata(doctype)
		
		filterable_fields = []
		for field in doctype_metadata["fields"]:
			if field["filterable"] and not field["hidden"]:
				# Add filter operators based on field type
				operators = self._get_field_operators(field["fieldtype"])
				
				filterable_fields.append({
					"fieldname": field["fieldname"],
					"label": field["label"],
					"fieldtype": field["fieldtype"],
					"options": field["options"],
					"operators": operators
				})
		
		return filterable_fields
	
	def _get_field_operators(self, fieldtype):
		"""Get available operators for a field type"""
		operators = {
			"Data": ["=", "!=", "like", "not like", "in", "not in"],
			"Link": ["=", "!=", "in", "not in"],
			"Select": ["=", "!=", "in", "not in"],
			"Int": ["=", "!=", ">", "<", ">=", "<=", "in", "not in"],
			"Float": ["=", "!=", ">", "<", ">=", "<=", "in", "not in"],
			"Currency": ["=", "!=", ">", "<", ">=", "<=", "in", "not in"],
			"Percent": ["=", "!=", ">", "<", ">=", "<=", "in", "not in"],
			"Date": ["=", "!=", ">", "<", ">=", "<=", "between"],
			"Datetime": ["=", "!=", ">", "<", ">=", "<=", "between"],
			"Time": ["=", "!=", ">", "<", ">=", "<="],
			"Check": ["=", "!="],
			"Text": ["like", "not like"],
			"Small Text": ["like", "not like"],
			"Long Text": ["like", "not like"]
		}
		
		return operators.get(fieldtype, ["=", "!="])
	
	def get_sortable_fields(self, doctype):
		"""Get fields that can be used for sorting"""
		doctype_metadata = self.get_doctype_metadata(doctype)
		
		sortable_fields = []
		for field in doctype_metadata["fields"]:
			if field["sortable"] and not field["hidden"]:
				sortable_fields.append({
					"fieldname": field["fieldname"],
					"label": field["label"],
					"fieldtype": field["fieldtype"]
				})
		
		return sortable_fields
	
	def invalidate_doctype_cache(self, doctype):
		"""Invalidate cache for a specific DocType"""
		cache_keys = [
			f"{self.cache_prefix}:doctype:{doctype}",
		]
		
		for key in cache_keys:
			self.cache.delete(key)
		
		# Also clear field-specific caches
		# Note: This is a simplified approach - in production you might want to use cache tags
		pass
	
	def get_doctype_list(self):
		"""Get list of all DocTypes"""
		cache_key = f"{self.cache_prefix}:doctype_list"
		
		# Try to get from cache first
		cached_list = self.cache.get(cache_key)
		if cached_list:
			return json.loads(cached_list)
		
		# Get from database
		doctypes = frappe.get_all("DocType",
			filters={"istable": 0, "issingle": 0},
			fields=["name", "module", "description"],
			order_by="name asc"
		)
		
		# Cache the result
		self.cache.set(cache_key, json.dumps(doctypes), self.cache_ttl)
		
		return doctypes
	
	def validate_field_access(self, doctype, fieldname, user=None):
		"""Validate if user has access to a specific field"""
		if not user:
			user = frappe.session.user
		
		# Check if user has read permission for the DocType
		if not frappe.has_permission(doctype, "read", user=user):
			return False
		
		# Get field metadata
		try:
			field_metadata = self.get_field_metadata(doctype, fieldname)
			
			# Check if field is hidden
			if field_metadata["hidden"]:
				return False
			
			# Additional permission checks can be added here
			# For example, role-based field permissions
			
			return True
			
		except:
			return False
	
	def get_doctype_fields(self, doctype):
		"""Get all fields for a DocType - simplified version for column management"""
		try:
			# Get DocType metadata
			metadata = self.get_doctype_metadata(doctype)
			
			# Return only fields that are suitable for list view
			list_view_fields = []
			for field in metadata["fields"]:
				# Skip system fields and hidden fields
				if field["fieldname"] in ["name", "owner", "creation", "modified", "modified_by"]:
					continue
				
				# Skip fields that are not suitable for list view
				if field["fieldtype"] in ["HTML Editor", "Text Editor", "Attach", "Attach Image"]:
					continue
				
				# Add field to list
				list_view_fields.append({
					"fieldname": field["fieldname"],
					"label": field["label"],
					"fieldtype": field["fieldtype"],
					"options": field["options"],
					"in_list_view": field["in_list_view"],
					"width": field["width"] or 150,
					"sortable": field["sortable"],
					"filterable": field["filterable"]
				})
			
			return list_view_fields
			
		except Exception as e:
			frappe.log_error(f"Error getting DocType fields: {str(e)}")
			return []