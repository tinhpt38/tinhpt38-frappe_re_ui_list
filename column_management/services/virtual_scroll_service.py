# -*- coding: utf-8 -*-
# Copyright (c) 2024, ERPNext Column Management Team and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import json
import math
from frappe import _

class VirtualScrollService:
    """Service for handling virtual scrolling and lazy loading"""
    
    def __init__(self):
        # Use lazy import for CacheService to avoid import issues
        try:
            from column_management.column_management.services.cache_service import CacheService
            self.cache_service = CacheService()
        except ImportError:
            # Fallback to frappe cache if CacheService is not available
            self.cache_service = frappe.cache()
        
        self.default_buffer_size = 50  # Number of items to buffer above/below viewport
        self.default_item_height = 40  # Default row height in pixels
        self.preload_threshold = 0.8  # Preload when 80% through current buffer
    
    def get_virtual_data(self, doctype, viewport_start, viewport_end, total_height, 
                        item_height=None, filters=None, sort_by=None, sort_order="asc", 
                        columns=None, user=None):
        """
        Get data for virtual scrolling viewport
        
        Args:
            doctype: DocType name
            viewport_start: Start pixel position of viewport
            viewport_end: End pixel position of viewport
            total_height: Total height of scrollable area
            item_height: Height of each item in pixels
            filters: Filter conditions
            sort_by: Sort field
            sort_order: Sort order (asc/desc)
            columns: Column configuration
            user: User ID
        
        Returns:
            dict: Virtual scroll data with items and metadata
        """
        try:
            # Validate parameters
            if not doctype:
                frappe.throw(_("DocType is required"))
            
            if not user:
                user = frappe.session.user
            
            # Check permissions
            if not frappe.has_permission(doctype, "read", user=user):
                frappe.throw(_("No permission to read {0}").format(doctype))
            
            # Calculate item dimensions
            item_height = item_height or self.default_item_height
            
            # Calculate visible range
            start_index = max(0, int(viewport_start // item_height))
            end_index = min(int(math.ceil(viewport_end / item_height)), 
                          int(total_height // item_height))
            
            # Add buffer for smooth scrolling
            buffer_start = max(0, start_index - self.default_buffer_size)
            buffer_end = end_index + self.default_buffer_size
            
            # Get total count for validation
            total_count = self._get_total_count(doctype, filters, user)
            buffer_end = min(buffer_end, total_count)
            
            # Calculate page parameters
            page_size = buffer_end - buffer_start
            page = (buffer_start // page_size) + 1 if page_size > 0 else 1
            
            # Get data from cache or database
            cache_key = self._generate_cache_key(doctype, filters, sort_by, sort_order, 
                                                buffer_start, buffer_end, user)
            
            cached_data = self.cache_service.get(cache_key)
            if cached_data:
                data = cached_data
            else:
                data = self._fetch_data_range(doctype, buffer_start, buffer_end, 
                                            filters, sort_by, sort_order, columns, user)
                # Cache for 5 minutes
                self.cache_service.set(cache_key, data, expire=300)
            
            # Calculate preload requirements
            preload_info = self._calculate_preload_requirements(
                start_index, end_index, buffer_start, buffer_end, total_count
            )
            
            return {
                "success": True,
                "data": {
                    "items": data,
                    "viewport_start": viewport_start,
                    "viewport_end": viewport_end,
                    "buffer_start": buffer_start,
                    "buffer_end": buffer_end,
                    "visible_start": start_index,
                    "visible_end": end_index,
                    "item_height": item_height,
                    "total_count": total_count,
                    "total_height": total_count * item_height,
                    "preload_info": preload_info
                },
                "message": _("Virtual scroll data retrieved successfully")
            }
            
        except Exception as e:
            frappe.log_error(f"Error getting virtual scroll data: {str(e)}")
            return {
                "success": False,
                "data": None,
                "message": str(e)
            }
    
    def preload_data(self, doctype, preload_ranges, filters=None, sort_by=None, 
                    sort_order="asc", columns=None, user=None):
        """
        Preload data for upcoming scroll positions
        
        Args:
            doctype: DocType name
            preload_ranges: List of [start, end] ranges to preload
            filters: Filter conditions
            sort_by: Sort field
            sort_order: Sort order
            columns: Column configuration
            user: User ID
        
        Returns:
            dict: Preload status
        """
        try:
            if not user:
                user = frappe.session.user
            
            preloaded_ranges = []
            
            for range_info in preload_ranges:
                start_idx, end_idx = range_info
                
                cache_key = self._generate_cache_key(doctype, filters, sort_by, sort_order, 
                                                    start_idx, end_idx, user)
                
                # Check if already cached
                if not self.cache_service.get(cache_key):
                    data = self._fetch_data_range(doctype, start_idx, end_idx, 
                                                filters, sort_by, sort_order, columns, user)
                    # Cache for 10 minutes for preloaded data
                    self.cache_service.set(cache_key, data, expire=600)
                    preloaded_ranges.append([start_idx, end_idx])
            
            return {
                "success": True,
                "data": {
                    "preloaded_ranges": preloaded_ranges,
                    "cache_hits": len(preload_ranges) - len(preloaded_ranges)
                },
                "message": _("Data preloaded successfully")
            }
            
        except Exception as e:
            frappe.log_error(f"Error preloading data: {str(e)}")
            return {
                "success": False,
                "data": None,
                "message": str(e)
            }
    
    def get_scroll_metrics(self, doctype, scroll_history, user=None):
        """
        Analyze scroll patterns for intelligent preloading
        
        Args:
            doctype: DocType name
            scroll_history: List of scroll positions with timestamps
            user: User ID
        
        Returns:
            dict: Scroll metrics and predictions
        """
        try:
            if not scroll_history or len(scroll_history) < 2:
                return {
                    "success": True,
                    "data": {
                        "scroll_velocity": 0,
                        "scroll_direction": "none",
                        "predicted_ranges": [],
                        "preload_priority": "low"
                    }
                }
            
            # Calculate scroll velocity and direction
            recent_positions = scroll_history[-5:]  # Last 5 positions
            
            total_distance = 0
            total_time = 0
            direction_changes = 0
            last_direction = None
            
            for i in range(1, len(recent_positions)):
                prev_pos = recent_positions[i-1]
                curr_pos = recent_positions[i]
                
                distance = curr_pos["position"] - prev_pos["position"]
                time_diff = curr_pos["timestamp"] - prev_pos["timestamp"]
                
                if time_diff > 0:
                    total_distance += abs(distance)
                    total_time += time_diff
                    
                    # Track direction changes
                    current_direction = "down" if distance > 0 else "up"
                    if last_direction and last_direction != current_direction:
                        direction_changes += 1
                    last_direction = current_direction
            
            # Calculate metrics
            scroll_velocity = total_distance / total_time if total_time > 0 else 0
            scroll_direction = last_direction or "none"
            
            # Predict preload ranges based on velocity and direction
            predicted_ranges = self._predict_scroll_ranges(
                recent_positions[-1]["position"], scroll_velocity, scroll_direction
            )
            
            # Determine preload priority
            preload_priority = "high" if scroll_velocity > 1000 else "medium" if scroll_velocity > 500 else "low"
            
            return {
                "success": True,
                "data": {
                    "scroll_velocity": scroll_velocity,
                    "scroll_direction": scroll_direction,
                    "direction_changes": direction_changes,
                    "predicted_ranges": predicted_ranges,
                    "preload_priority": preload_priority,
                    "stability_score": max(0, 1 - (direction_changes / len(recent_positions)))
                }
            }
            
        except Exception as e:
            frappe.log_error(f"Error calculating scroll metrics: {str(e)}")
            return {
                "success": False,
                "data": None,
                "message": str(e)
            }
    
    def invalidate_virtual_cache(self, doctype, user=None):
        """
        Invalidate virtual scroll cache for a doctype
        
        Args:
            doctype: DocType name
            user: User ID (optional, if None invalidates for all users)
        """
        try:
            cache_pattern = f"virtual_scroll:{doctype}:*"
            if user:
                cache_pattern = f"virtual_scroll:{doctype}:*:{user}:*"
            
            self.cache_service.delete_pattern(cache_pattern)
            
            return {
                "success": True,
                "message": _("Virtual scroll cache invalidated")
            }
            
        except Exception as e:
            frappe.log_error(f"Error invalidating virtual cache: {str(e)}")
            return {
                "success": False,
                "message": str(e)
            }
    
    def _get_total_count(self, doctype, filters, user):
        """Get total count of records"""
        try:
            # Build filter conditions
            filter_conditions = []
            if filters:
                filter_conditions = self._build_filter_conditions(filters)
            
            return frappe.db.count(doctype, filters=filter_conditions)
            
        except Exception as e:
            frappe.log_error(f"Error getting total count: {str(e)}")
            return 0
    
    def _fetch_data_range(self, doctype, start_idx, end_idx, filters, sort_by, 
                         sort_order, columns, user):
        """Fetch data for a specific range"""
        try:
            # Get column configuration
            from column_management.column_management.services.column_service import ColumnService
            column_service = ColumnService()
            
            if not columns:
                config = column_service.get_user_column_config(doctype, user)
                columns = [col for col in config.get("columns", []) if col.get("visible")]
            
            # Build field list
            fields = []
            for column in columns:
                fieldname = column.get("fieldname")
                if fieldname:
                    fields.append(fieldname)
            
            # Ensure 'name' field is always included
            if "name" not in fields:
                fields.insert(0, "name")
            
            # Build filters
            filter_conditions = []
            if filters:
                filter_conditions = self._build_filter_conditions(filters)
            
            # Build order by
            order_by = None
            if sort_by:
                sort_order = "desc" if sort_order.lower() == "desc" else "asc"
                order_by = f"{sort_by} {sort_order}"
            else:
                order_by = "modified desc"
            
            # Calculate page parameters
            page_size = end_idx - start_idx
            
            # Get data
            data = frappe.get_all(
                doctype,
                fields=fields,
                filters=filter_conditions,
                order_by=order_by,
                start=start_idx,
                page_length=page_size,
                as_list=False
            )
            
            # Format data
            formatted_data = self._format_virtual_data(data, columns, doctype, start_idx)
            
            return formatted_data
            
        except Exception as e:
            frappe.log_error(f"Error fetching data range: {str(e)}")
            return []
    
    def _format_virtual_data(self, data, columns, doctype, start_idx):
        """Format data for virtual scrolling"""
        try:
            # Get field types for formatting
            from column_management.column_management.services.metadata_service import MetadataService
            metadata_service = MetadataService()
            doctype_metadata = metadata_service.get_doctype_metadata(doctype)
            field_types = {field["fieldname"]: field["fieldtype"] 
                          for field in doctype_metadata.get("fields", [])}
            
            formatted_data = []
            
            for idx, row in enumerate(data):
                formatted_row = {
                    "_virtual_index": start_idx + idx,  # Virtual index for positioning
                    "_row_id": row.get("name"),  # Unique row identifier
                }
                
                for column in columns:
                    fieldname = column.get("fieldname")
                    if fieldname and fieldname in row:
                        value = row[fieldname]
                        fieldtype = field_types.get(fieldname, "Data")
                        
                        # Format value based on field type
                        formatted_value = self._format_field_value(value, fieldtype)
                        formatted_row[fieldname] = formatted_value
                
                formatted_data.append(formatted_row)
            
            return formatted_data
            
        except Exception as e:
            frappe.log_error(f"Error formatting virtual data: {str(e)}")
            return data
    
    def _format_field_value(self, value, fieldtype):
        """Format field value based on field type"""
        if value is None:
            return ""
        
        try:
            if fieldtype == "Currency":
                return frappe.utils.fmt_money(value)
            elif fieldtype == "Date":
                return frappe.utils.formatdate(value)
            elif fieldtype == "Datetime":
                return frappe.utils.format_datetime(value)
            elif fieldtype == "Time":
                return frappe.utils.format_time(value)
            elif fieldtype == "Percent":
                return f"{float(value):.2f}%"
            elif fieldtype == "Float":
                return f"{float(value):.2f}"
            elif fieldtype == "Check":
                return "Yes" if value else "No"
            else:
                return str(value)
        except:
            return str(value)
    
    def _build_filter_conditions(self, filters):
        """Build filter conditions from filter array"""
        conditions = []
        
        for filter_item in filters:
            if not isinstance(filter_item, dict):
                continue
            
            fieldname = filter_item.get("fieldname")
            operator = filter_item.get("operator")
            value = filter_item.get("value")
            
            if not fieldname or not operator:
                continue
            
            # Build condition based on operator
            if operator == "=":
                conditions.append([fieldname, "=", value])
            elif operator == "!=":
                conditions.append([fieldname, "!=", value])
            elif operator == ">":
                conditions.append([fieldname, ">", value])
            elif operator == "<":
                conditions.append([fieldname, "<", value])
            elif operator == ">=":
                conditions.append([fieldname, ">=", value])
            elif operator == "<=":
                conditions.append([fieldname, "<=", value])
            elif operator == "like":
                conditions.append([fieldname, "like", f"%{value}%"])
            elif operator == "not like":
                conditions.append([fieldname, "not like", f"%{value}%"])
            elif operator == "in":
                if isinstance(value, list):
                    conditions.append([fieldname, "in", value])
                else:
                    conditions.append([fieldname, "=", value])
            elif operator == "not in":
                if isinstance(value, list):
                    conditions.append([fieldname, "not in", value])
                else:
                    conditions.append([fieldname, "!=", value])
        
        return conditions
    
    def _calculate_preload_requirements(self, visible_start, visible_end, 
                                      buffer_start, buffer_end, total_count):
        """Calculate what ranges should be preloaded"""
        preload_ranges = []
        
        # Calculate how much of the buffer is being used
        visible_range = visible_end - visible_start
        buffer_usage = (visible_end - buffer_start) / (buffer_end - buffer_start) if buffer_end > buffer_start else 0
        
        # If we're using more than threshold of buffer, preload next ranges
        if buffer_usage > self.preload_threshold:
            # Preload next range
            next_start = buffer_end
            next_end = min(next_start + visible_range + self.default_buffer_size, total_count)
            
            if next_start < total_count:
                preload_ranges.append([next_start, next_end])
            
            # If scrolling fast, preload even further
            if buffer_usage > 0.9:
                far_start = next_end
                far_end = min(far_start + visible_range, total_count)
                
                if far_start < total_count:
                    preload_ranges.append([far_start, far_end])
        
        return {
            "ranges": preload_ranges,
            "buffer_usage": buffer_usage,
            "should_preload": len(preload_ranges) > 0
        }
    
    def _predict_scroll_ranges(self, current_position, velocity, direction):
        """Predict scroll ranges based on current metrics"""
        predicted_ranges = []
        
        if velocity > 0 and direction in ["up", "down"]:
            # Predict where user will scroll in next 2-3 seconds
            predicted_distance = velocity * 2  # 2 seconds ahead
            
            if direction == "down":
                predicted_position = current_position + predicted_distance
            else:
                predicted_position = max(0, current_position - predicted_distance)
            
            # Convert to item indices
            item_height = self.default_item_height
            predicted_start = int(predicted_position // item_height)
            predicted_end = predicted_start + (int(predicted_distance // item_height) or 50)
            
            predicted_ranges.append([predicted_start, predicted_end])
        
        return predicted_ranges
    
    def _generate_cache_key(self, doctype, filters, sort_by, sort_order, 
                           start_idx, end_idx, user):
        """Generate cache key for virtual scroll data"""
        # Create a hash of filters for cache key
        filter_hash = ""
        if filters:
            filter_str = json.dumps(filters, sort_keys=True)
            filter_hash = frappe.utils.md5(filter_str)[:8]
        
        sort_key = f"{sort_by}_{sort_order}" if sort_by else "default"
        
        return f"virtual_scroll:{doctype}:{filter_hash}:{sort_key}:{start_idx}:{end_idx}:{user}"