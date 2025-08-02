# -*- coding: utf-8 -*-
# Copyright (c) 2024, ERPNext Column Management Team and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import json
import math
from frappe import _

class ColumnVirtualizationService:
    """Service for handling column virtualization for large datasets"""
    
    def __init__(self):
        # Use lazy import for CacheService to avoid import issues
        try:
            from column_management.column_management.services.cache_service import CacheService
            self.cache_service = CacheService()
        except ImportError:
            # Fallback to frappe cache if CacheService is not available
            self.cache_service = frappe.cache()
        
        self.default_column_width = 150  # Default column width in pixels
        self.buffer_columns = 5  # Number of columns to buffer on each side
        self.min_visible_columns = 3  # Minimum columns to keep visible
    
    def get_virtual_columns(self, doctype, viewport_left, viewport_width, 
                           total_width, columns=None, user=None):
        """
        Get columns for current viewport
        
        Args:
            doctype: DocType name
            viewport_left: Left position of viewport in pixels
            viewport_width: Width of viewport in pixels
            total_width: Total width of all columns
            columns: Column configuration
            user: User ID
        
        Returns:
            dict: Virtual column data
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
            
            # Get column configuration if not provided
            if not columns:
                from column_management.column_management.services.column_service import ColumnService
                column_service = ColumnService()
                config = column_service.get_user_column_config(doctype, user)
                columns = [col for col in config.get("columns", []) if col.get("visible")]
            
            # Calculate column positions
            column_positions = self._calculate_column_positions(columns)
            
            # Find visible columns
            visible_columns = self._find_visible_columns(
                column_positions, viewport_left, viewport_width
            )
            
            # Add buffer columns
            buffered_columns = self._add_buffer_columns(
                visible_columns, column_positions, columns
            )
            
            # Get column data from cache or generate
            cache_key = self._generate_column_cache_key(
                doctype, buffered_columns, user
            )
            
            cached_data = self.cache_service.get(cache_key)
            if cached_data:
                column_data = cached_data
            else:
                column_data = self._prepare_column_data(buffered_columns, columns)
                # Cache for 10 minutes
                self.cache_service.set(cache_key, column_data, expire=600)
            
            # Calculate rendering info
            rendering_info = self._calculate_rendering_info(
                buffered_columns, column_positions, viewport_left, viewport_width
            )
            
            return {
                "success": True,
                "data": {
                    "columns": column_data,
                    "visible_columns": visible_columns,
                    "buffered_columns": buffered_columns,
                    "column_positions": column_positions,
                    "rendering_info": rendering_info,
                    "viewport_left": viewport_left,
                    "viewport_width": viewport_width,
                    "total_width": total_width
                },
                "message": _("Virtual columns retrieved successfully")
            }
            
        except Exception as e:
            frappe.log_error(f"Error getting virtual columns: {str(e)}")
            return {
                "success": False,
                "data": None,
                "message": str(e)
            }
    
    def preload_columns(self, doctype, column_ranges, columns=None, user=None):
        """
        Preload column data for upcoming viewport positions
        
        Args:
            doctype: DocType name
            column_ranges: List of column index ranges to preload
            columns: Column configuration
            user: User ID
        
        Returns:
            dict: Preload status
        """
        try:
            if not user:
                user = frappe.session.user
            
            if not columns:
                from column_management.column_management.services.column_service import ColumnService
                column_service = ColumnService()
                config = column_service.get_user_column_config(doctype, user)
                columns = [col for col in config.get("columns", []) if col.get("visible")]
            
            preloaded_ranges = []
            
            for range_info in column_ranges:
                start_idx, end_idx = range_info
                
                # Get columns in range
                range_columns = columns[start_idx:end_idx]
                
                cache_key = self._generate_column_cache_key(
                    doctype, list(range(start_idx, end_idx)), user
                )
                
                # Check if already cached
                if not self.cache_service.get(cache_key):
                    column_data = self._prepare_column_data(
                        list(range(start_idx, end_idx)), columns
                    )
                    # Cache for 15 minutes for preloaded data
                    self.cache_service.set(cache_key, column_data, expire=900)
                    preloaded_ranges.append([start_idx, end_idx])
            
            return {
                "success": True,
                "data": {
                    "preloaded_ranges": preloaded_ranges,
                    "cache_hits": len(column_ranges) - len(preloaded_ranges)
                },
                "message": _("Columns preloaded successfully")
            }
            
        except Exception as e:
            frappe.log_error(f"Error preloading columns: {str(e)}")
            return {
                "success": False,
                "data": None,
                "message": str(e)
            }
    
    def get_column_metrics(self, doctype, scroll_history, user=None):
        """
        Analyze horizontal scroll patterns for intelligent column preloading
        
        Args:
            doctype: DocType name
            scroll_history: List of horizontal scroll positions with timestamps
            user: User ID
        
        Returns:
            dict: Column scroll metrics and predictions
        """
        try:
            if not scroll_history or len(scroll_history) < 2:
                return {
                    "success": True,
                    "data": {
                        "scroll_velocity": 0,
                        "scroll_direction": "none",
                        "predicted_column_ranges": [],
                        "preload_priority": "low"
                    }
                }
            
            # Calculate horizontal scroll velocity and direction
            recent_positions = scroll_history[-5:]  # Last 5 positions
            
            total_distance = 0
            total_time = 0
            direction_changes = 0
            last_direction = None
            
            for i in range(1, len(recent_positions)):
                prev_pos = recent_positions[i-1]
                curr_pos = recent_positions[i]
                
                distance = curr_pos["left"] - prev_pos["left"]
                time_diff = curr_pos["timestamp"] - prev_pos["timestamp"]
                
                if time_diff > 0:
                    total_distance += abs(distance)
                    total_time += time_diff
                    
                    # Track direction changes
                    current_direction = "right" if distance > 0 else "left"
                    if last_direction and last_direction != current_direction:
                        direction_changes += 1
                    last_direction = current_direction
            
            # Calculate metrics
            scroll_velocity = total_distance / total_time if total_time > 0 else 0
            scroll_direction = last_direction or "none"
            
            # Predict column ranges based on velocity and direction
            predicted_ranges = self._predict_column_ranges(
                recent_positions[-1]["left"], scroll_velocity, scroll_direction
            )
            
            # Determine preload priority
            preload_priority = "high" if scroll_velocity > 500 else "medium" if scroll_velocity > 200 else "low"
            
            return {
                "success": True,
                "data": {
                    "scroll_velocity": scroll_velocity,
                    "scroll_direction": scroll_direction,
                    "direction_changes": direction_changes,
                    "predicted_column_ranges": predicted_ranges,
                    "preload_priority": preload_priority,
                    "stability_score": max(0, 1 - (direction_changes / len(recent_positions)))
                }
            }
            
        except Exception as e:
            frappe.log_error(f"Error calculating column metrics: {str(e)}")
            return {
                "success": False,
                "data": None,
                "message": str(e)
            }
    
    def invalidate_column_cache(self, doctype, user=None):
        """
        Invalidate column virtualization cache
        
        Args:
            doctype: DocType name
            user: User ID (optional, if None invalidates for all users)
        """
        try:
            cache_pattern = f"column_virtual:{doctype}:*"
            if user:
                cache_pattern = f"column_virtual:{doctype}:*:{user}:*"
            
            self.cache_service.delete_pattern(cache_pattern)
            
            return {
                "success": True,
                "message": _("Column virtualization cache invalidated")
            }
            
        except Exception as e:
            frappe.log_error(f"Error invalidating column cache: {str(e)}")
            return {
                "success": False,
                "message": str(e)
            }
    
    def optimize_column_rendering(self, doctype, columns, viewport_width, user=None):
        """
        Optimize column rendering based on viewport and usage patterns
        
        Args:
            doctype: DocType name
            columns: Column configuration
            viewport_width: Current viewport width
            user: User ID
        
        Returns:
            dict: Optimized column configuration
        """
        try:
            if not user:
                user = frappe.session.user
            
            # Get column usage statistics
            usage_stats = self._get_column_usage_stats(doctype, user)
            
            # Calculate optimal column widths
            optimized_columns = self._optimize_column_widths(
                columns, viewport_width, usage_stats
            )
            
            # Determine column priorities
            column_priorities = self._calculate_column_priorities(
                optimized_columns, usage_stats
            )
            
            # Create rendering strategy
            rendering_strategy = self._create_rendering_strategy(
                optimized_columns, column_priorities, viewport_width
            )
            
            return {
                "success": True,
                "data": {
                    "optimized_columns": optimized_columns,
                    "column_priorities": column_priorities,
                    "rendering_strategy": rendering_strategy,
                    "usage_stats": usage_stats
                },
                "message": _("Column rendering optimized")
            }
            
        except Exception as e:
            frappe.log_error(f"Error optimizing column rendering: {str(e)}")
            return {
                "success": False,
                "data": None,
                "message": str(e)
            }
    
    def _calculate_column_positions(self, columns):
        """Calculate absolute positions for all columns"""
        positions = {}
        current_left = 0
        
        for i, column in enumerate(columns):
            width = column.get("width", self.default_column_width)
            positions[i] = {
                "left": current_left,
                "right": current_left + width,
                "width": width,
                "fieldname": column.get("fieldname"),
                "index": i
            }
            current_left += width
        
        return positions
    
    def _find_visible_columns(self, column_positions, viewport_left, viewport_width):
        """Find columns that are currently visible in viewport"""
        viewport_right = viewport_left + viewport_width
        visible_columns = []
        
        for index, pos in column_positions.items():
            # Check if column intersects with viewport
            if pos["right"] > viewport_left and pos["left"] < viewport_right:
                visible_columns.append(index)
        
        return sorted(visible_columns)
    
    def _add_buffer_columns(self, visible_columns, column_positions, columns):
        """Add buffer columns around visible columns"""
        if not visible_columns:
            return []
        
        min_index = min(visible_columns)
        max_index = max(visible_columns)
        
        # Add buffer columns
        buffer_start = max(0, min_index - self.buffer_columns)
        buffer_end = min(len(columns), max_index + self.buffer_columns + 1)
        
        return list(range(buffer_start, buffer_end))
    
    def _prepare_column_data(self, column_indices, columns):
        """Prepare column data for rendering"""
        column_data = []
        
        for index in column_indices:
            if index < len(columns):
                column = columns[index]
                column_data.append({
                    "index": index,
                    "fieldname": column.get("fieldname"),
                    "label": column.get("label"),
                    "width": column.get("width", self.default_column_width),
                    "fieldtype": column.get("fieldtype", "Data"),
                    "options": column.get("options"),
                    "visible": column.get("visible", True),
                    "frozen": column.get("frozen", False),
                    "sortable": column.get("sortable", True),
                    "filterable": column.get("filterable", True)
                })
        
        return column_data
    
    def _calculate_rendering_info(self, buffered_columns, column_positions, 
                                 viewport_left, viewport_width):
        """Calculate rendering information for columns"""
        rendering_info = {
            "total_buffered_width": 0,
            "visible_width": 0,
            "left_offset": 0,
            "column_offsets": {}
        }
        
        if not buffered_columns:
            return rendering_info
        
        # Calculate total buffered width
        for index in buffered_columns:
            if index in column_positions:
                rendering_info["total_buffered_width"] += column_positions[index]["width"]
        
        # Calculate visible width
        viewport_right = viewport_left + viewport_width
        for index in buffered_columns:
            if index in column_positions:
                pos = column_positions[index]
                # Calculate intersection with viewport
                intersection_left = max(pos["left"], viewport_left)
                intersection_right = min(pos["right"], viewport_right)
                if intersection_right > intersection_left:
                    rendering_info["visible_width"] += intersection_right - intersection_left
        
        # Calculate left offset (how much to shift the container)
        if buffered_columns:
            first_column_index = min(buffered_columns)
            if first_column_index in column_positions:
                rendering_info["left_offset"] = column_positions[first_column_index]["left"]
        
        # Calculate individual column offsets relative to container
        container_left = rendering_info["left_offset"]
        for index in buffered_columns:
            if index in column_positions:
                rendering_info["column_offsets"][index] = (
                    column_positions[index]["left"] - container_left
                )
        
        return rendering_info
    
    def _predict_column_ranges(self, current_left, velocity, direction):
        """Predict column ranges based on current metrics"""
        predicted_ranges = []
        
        if velocity > 0 and direction in ["left", "right"]:
            # Predict where user will scroll in next 2-3 seconds
            predicted_distance = velocity * 2  # 2 seconds ahead
            
            if direction == "right":
                predicted_left = current_left + predicted_distance
            else:
                predicted_left = max(0, current_left - predicted_distance)
            
            # Convert to column indices (approximate)
            avg_column_width = self.default_column_width
            predicted_start_col = int(predicted_left // avg_column_width)
            predicted_end_col = predicted_start_col + int(predicted_distance // avg_column_width) + 5
            
            predicted_ranges.append([predicted_start_col, predicted_end_col])
        
        return predicted_ranges
    
    def _get_column_usage_stats(self, doctype, user):
        """Get column usage statistics for optimization"""
        try:
            # This would typically come from user interaction tracking
            # For now, return default stats
            return {
                "most_viewed_columns": [],
                "least_viewed_columns": [],
                "average_view_time": {},
                "interaction_frequency": {}
            }
        except Exception as e:
            frappe.log_error(f"Error getting column usage stats: {str(e)}")
            return {}
    
    def _optimize_column_widths(self, columns, viewport_width, usage_stats):
        """Optimize column widths based on viewport and usage"""
        optimized_columns = []
        
        for column in columns:
            optimized_column = column.copy()
            
            # Apply width optimizations based on content and usage
            current_width = column.get("width", self.default_column_width)
            
            # Adjust based on field type
            fieldtype = column.get("fieldtype", "Data")
            if fieldtype in ["Check"]:
                optimized_column["width"] = min(current_width, 80)
            elif fieldtype in ["Currency", "Float", "Int"]:
                optimized_column["width"] = max(current_width, 120)
            elif fieldtype in ["Text", "Long Text"]:
                optimized_column["width"] = max(current_width, 200)
            
            optimized_columns.append(optimized_column)
        
        return optimized_columns
    
    def _calculate_column_priorities(self, columns, usage_stats):
        """Calculate rendering priorities for columns"""
        priorities = {}
        
        for i, column in enumerate(columns):
            fieldname = column.get("fieldname")
            
            # Base priority
            priority = 50
            
            # Adjust based on field importance
            if fieldname == "name":
                priority += 30
            elif column.get("frozen"):
                priority += 20
            elif fieldname in ["status", "docstatus"]:
                priority += 15
            
            # Adjust based on usage stats
            if fieldname in usage_stats.get("most_viewed_columns", []):
                priority += 10
            elif fieldname in usage_stats.get("least_viewed_columns", []):
                priority -= 10
            
            priorities[i] = priority
        
        return priorities
    
    def _create_rendering_strategy(self, columns, priorities, viewport_width):
        """Create optimal rendering strategy"""
        strategy = {
            "render_order": [],
            "lazy_load_threshold": viewport_width * 2,
            "preload_columns": 3,
            "cleanup_threshold": viewport_width * 4
        }
        
        # Sort columns by priority for rendering order
        sorted_columns = sorted(
            enumerate(columns), 
            key=lambda x: priorities.get(x[0], 0), 
            reverse=True
        )
        
        strategy["render_order"] = [index for index, _ in sorted_columns]
        
        return strategy
    
    def _generate_column_cache_key(self, doctype, column_indices, user):
        """Generate cache key for column data"""
        indices_str = ",".join(map(str, sorted(column_indices)))
        return f"column_virtual:{doctype}:{frappe.utils.md5(indices_str)[:8]}:{user}"