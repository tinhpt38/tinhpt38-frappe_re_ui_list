# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from . import __version__ as app_version

app_name = "column_management"
app_title = "Column Management"
app_publisher = "P. Tính"
app_description = "Advanced column management system for ERPNext List Views"
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "tinhpt.38@gmail.com"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# Temporarily disabled until build issues are resolved
# app_include_css = "/assets/column_management/css/column_management.css"
# app_include_js = "/assets/column_management/js/column_management.js"

# include js, css files in header of web template
# web_include_css = "/assets/column_management/css/column_management.css"
# web_include_js = "/assets/column_management/js/column_management.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "column_management/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "column_management.install.before_install"
after_install = "column_management.column_management.install.after_install"

# Uninstallation
# ------------

before_uninstall = "column_management.column_management.install.before_uninstall"
# after_uninstall = "column_management.uninstall.after_uninstall"

# Desk Notifications
# -------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "column_management.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
#	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
#	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
#	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"*": {
		"on_update": "column_management.hooks.on_doc_update",
		"on_submit": "column_management.hooks.on_doc_submit",
		"on_cancel": "column_management.hooks.on_doc_cancel"
	}
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
#	"all": [
#		"column_management.tasks.all"
#	],
#	"daily": [
#		"column_management.tasks.daily"
#	],
#	"hourly": [
#		"column_management.tasks.hourly"
#	],
#	"weekly": [
#		"column_management.tasks.weekly"
#	]
#	"monthly": [
#		"column_management.tasks.monthly"
#	]
# }

# Testing
# -------

# before_tests = "column_management.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
#	"frappe.desk.doctype.event.event.get_events": "column_management.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
#	"Task": "column_management.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]


# User Data Protection
# --------------------

user_data_fields = [
	{
		"doctype": "{doctype_1}",
		"filter_by": "{filter_by}",
		"redact_fields": ["{field_1}", "{field_2}"],
		"partial": 1,
	},
	{
		"doctype": "{doctype_2}",
		"filter_by": "{filter_by}",
		"partial": 1,
	},
	{
		"doctype": "{doctype_3}",
		"strict": False,
	},
	{
		"doctype": "{doctype_4}"
	}
]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
#	"column_management.auth.validate"
# ]

# Translation
# --------------------------------

# Make link fields searchable
# Each item of the list has the following schema:
# 1. doctype: DocType the rule applies to
# 2. searchfield: the fieldname that searches should see for a match
# 3. search_fields: a list of fields that should be searched. SQL OR semantics apply
# 4. search_operators: a list of operators that will be used as default in AutoComplete
# 5. search_queries: a list of Query that will be used as default in AutoComplete
# 6. search_filters: a list of filters to be applied on link search
# 7. search_reference_method: Use this method on the DocType class for the reference data. The format is "{method_name}"

# search_fields = [
#	{
#		"doctype": "Address",
#		"searchfield": "name",
#		"search_fields": ["address_title", "address_line1", "address_line2", "city", "state"],
#		"search_operators": ["like", "lwildcard", "rwildcard"],
#		"search_queries": [],
#		"search_filters": []
#	}
# ]

# Website context
# ----------------
# Values to be rendered in Website context

# website_context = {
#	"favicon": 	"/assets/column_management/images/favicon.png",
#	"splash_image": "/assets/column_management/images/splash.png"
# }

# Custom hooks for column management events
def on_doc_update(doc, method):
	"""Update statistics cache when document changes"""
	try:
		from column_management.column_management.services.statistics_service import StatisticsService
		if hasattr(doc, 'doctype') and doc.doctype:
			service = StatisticsService()
			service.invalidate_statistics_cache(doc.doctype)
	except (ImportError, AttributeError, Exception):
		# Silently handle errors during hooks to prevent breaking other functionality
		pass

def on_doc_submit(doc, method):
	"""Handle document submission events"""
	try:
		from column_management.column_management.services.statistics_service import StatisticsService
		if hasattr(doc, 'doctype') and doc.doctype:
			service = StatisticsService()
			service.invalidate_statistics_cache(doc.doctype)
	except (ImportError, AttributeError, Exception):
		# Silently handle errors during hooks to prevent breaking other functionality
		pass

def on_doc_cancel(doc, method):
	"""Handle document cancellation events"""
	try:
		from column_management.column_management.services.statistics_service import StatisticsService
		if hasattr(doc, 'doctype') and doc.doctype:
			service = StatisticsService()
			service.invalidate_statistics_cache(doc.doctype)
	except (ImportError, AttributeError, Exception):
		# Silently handle errors during hooks to prevent breaking other functionality
		pass