# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in column_management/__init__.py
import os
import re

def get_version():
	"""Get version from __init__.py file"""
	here = os.path.abspath(os.path.dirname(__file__))
	init_file = os.path.join(here, "column_management", "__init__.py")
	
	if os.path.exists(init_file):
		with open(init_file, 'r', encoding='utf-8') as f:
			content = f.read()
			version_match = re.search(r"__version__\s*=\s*['\"]([^'\"]*)['\"]", content)
			if version_match:
				return version_match.group(1)
	return "1.0.0"

version = get_version()

setup(
	name="column_management",
	version=version,
	description="Advanced column management system for ERPNext List Views",
	author="P. Tính",
	author_email="tinhpt.38@gmail.com",
	url="https://github.com/tinhpt38/tinhpt38-frappe_re_ui_list",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires,
	python_requires=">=3.7",
	classifiers=[
		"Development Status :: 4 - Beta",
		"Environment :: Web Environment",
		"Framework :: Frappe",
		"Intended Audience :: Developers",
		"License :: OSI Approved :: MIT License",
		"Operating System :: OS Independent",
		"Programming Language :: Python :: 3",
		"Programming Language :: Python :: 3.7",
		"Programming Language :: Python :: 3.8",
		"Programming Language :: Python :: 3.9",
		"Programming Language :: Python :: 3.10",
		"Topic :: Internet :: WWW/HTTP",
		"Topic :: Software Development :: Libraries :: Application Frameworks",
	],
)