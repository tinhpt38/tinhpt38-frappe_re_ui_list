# -*- coding: utf-8 -*-
"""
Column Management App for ERPNext/Frappe

Advanced column management system for ERPNext List Views with features like:
- Dynamic column configuration
- Column width management and persistence
- Column pinning (left/right)
- Unlimited column display with virtual scrolling
- Enhanced pagination
- Dynamic filtering system
- Real-time statistics dashboard
- User preference persistence
- Mobile responsiveness
"""

__version__ = '1.0.0'

import frappe

def get_version():
    """Return the version of the app"""
    return __version__

def is_frappe_app():
    """Marker function to identify this as a Frappe app"""
    return True