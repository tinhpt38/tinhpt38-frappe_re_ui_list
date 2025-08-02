/**
 * Column Virtualization Implementation for Large Column Sets
 * Copyright (c) 2024, ERPNext Column Management Team
 */

frappe.provide('column_management.column_virtualization');

column_management.column_virtualization = {
    
    /**
     * Column virtualization manager class
     */
    ColumnVirtualizationManager: class {
        constructor(options) {
            this.container = options.container;
            this.doctype = options.doctype;
            this.columns = options.columns || [];
            this.viewport_width = options.viewport_width || 1200;
            this.default_column_width = options.default_column_width || 150;
            this.buffer_columns = options.buffer_columns || 5;
            
            // State management
            this.scroll_left = 0;
            this.total_width = 0;
            this.visible_columns = [];
            this.rendered_columns = new Map();
            this.column_positions = new Map();
            this.scroll_history = [];
            
            // Performance tracking
            this.last_scroll_time = 0;
            this.scroll_velocity = 0;
            this.is_scrolling = false;
            this.scroll_timeout = null;
            
            // Cache for rendered elements
            this.column_cache = new Map();
            this.recycled_elements = [];
            
            this.init();
        }
        
        init() {
            this.calculate_column_positions();
            this.setup_container();
            this.setup_scroll_listener();
            this.render_initial_columns();
        }
        
        calculate_column_positions() {
            let current_left = 0;
            this.total_width = 0;
            
            this.columns.forEach((column, index) => {
                const width = column.width || this.default_column_width;
                
                this.column_positions.set(index, {
                    left: current_left,
                    right: current_left + width,
                    width: width,
                    fieldname: column.fieldname,
                    index: index
                });
                
                current_left += width;
                this.total_width += width;
            });
        }
        
        setup_container() {
            this.$container = $(this.container);
            this.$container.addClass('column-virtualization-container');
            
            // Create horizontal scroll viewport
            this.$viewport = $('<div class="column-viewport"></div>');
            this.$viewport.css({
                'width': this.viewport_width + 'px',
                'overflow-x': 'auto',
                'overflow-y': 'hidden',
                'position': 'relative'
            });
            
            // Create content area with full width
            this.$content = $('<div class="column-content"></div>');
            this.$content.css({
                'width': this.total_width + 'px',
                'height': '100%',
                'position': 'relative'
            });
            
            // Create visible area for rendered columns
            this.$visible_area = $('<div class="column-visible-area"></div>');
            this.$visible_area.css({
                'position': 'absolute',
                'top': '0px',
                'left': '0px',
                'height': '100%'
            });
            
            this.$content.append(this.$visible_area);
            this.$viewport.append(this.$content);
            this.$container.append(this.$viewport);
        }
        
        setup_scroll_listener() {
            const self = this;
            
            this.$viewport.on('scroll', function(e) {
                const current_time = Date.now();
                const scroll_left = this.scrollLeft;
                
                // Calculate horizontal scroll velocity
                if (self.last_scroll_time > 0) {
                    const time_diff = current_time - self.last_scroll_time;
                    const scroll_diff = Math.abs(scroll_left - self.scroll_left);
                    self.scroll_velocity = time_diff > 0 ? scroll_diff / time_diff : 0;
                }
                
                self.scroll_left = scroll_left;
                self.last_scroll_time = current_time;
                self.is_scrolling = true;
                
                // Add to scroll history for pattern analysis
                self.scroll_history.push({
                    left: scroll_left,
                    timestamp: current_time
                });
                
                // Keep only recent history
                if (self.scroll_history.length > 20) {
                    self.scroll_history.shift();
                }
                
                // Handle scroll
                self.handle_horizontal_scroll();
                
                // Set scroll end timeout
                clearTimeout(self.scroll_timeout);
                self.scroll_timeout = setTimeout(() => {
                    self.is_scrolling = false;
                    self.on_scroll_end();
                }, 150);
            });
        }
        
        render_initial_columns() {
            this.update_visible_columns();
            this.render_visible_columns();
        }
        
        handle_horizontal_scroll() {
            // Throttle scroll handling
            if (this.scroll_handle_timeout) {
                return;
            }
            
            this.scroll_handle_timeout = setTimeout(() => {
                this.update_visible_columns();
                this.render_visible_columns();
                this.scroll_handle_timeout = null;
            }, 16); // ~60fps
        }
        
        update_visible_columns() {
            const viewport_left = this.scroll_left;
            const viewport_right = this.scroll_left + this.viewport_width;
            
            this.visible_columns = [];
            
            this.column_positions.forEach((pos, index) => {
                // Check if column intersects with viewport
                if (pos.right > viewport_left && pos.left < viewport_right) {
                    this.visible_columns.push(index);
                }
            });
            
            // Add buffer columns
            if (this.visible_columns.length > 0) {
                const min_index = Math.min(...this.visible_columns);
                const max_index = Math.max(...this.visible_columns);
                
                const buffer_start = Math.max(0, min_index - this.buffer_columns);
                const buffer_end = Math.min(this.columns.length, max_index + this.buffer_columns + 1);
                
                this.visible_columns = [];
                for (let i = buffer_start; i < buffer_end; i++) {
                    this.visible_columns.push(i);
                }
            }
        }
        
        render_visible_columns() {
            // Clean up out-of-range columns
            this.cleanup_out_of_range_columns();
            
            // Render visible columns
            this.visible_columns.forEach(index => {
                if (!this.rendered_columns.has(index)) {
                    this.render_column(index);
                }
            });
            
            // Update container positioning
            this.update_container_position();
        }
        
        render_column(column_index) {
            const column = this.columns[column_index];
            const position = this.column_positions.get(column_index);
            
            if (!column || !position) {
                return;
            }
            
            // Get or create column element
            const $column_element = this.get_or_create_column_element(column, column_index);
            
            // Position column
            $column_element.css({
                'position': 'absolute',
                'left': position.left + 'px',
                'top': '0px',
                'width': position.width + 'px',
                'height': '100%'
            });
            
            // Add to visible area
            this.$visible_area.append($column_element);
            this.rendered_columns.set(column_index, $column_element);
        }
        
        get_or_create_column_element(column, column_index) {
            // Try to recycle an element
            if (this.recycled_elements.length > 0) {
                const $element = this.recycled_elements.pop();
                this.update_column_element($element, column, column_index);
                return $element;
            }
            
            // Create new element
            return this.create_column_element(column, column_index);
        }
        
        create_column_element(column, column_index) {
            const $element = $('<div class="virtual-column"></div>');
            $element.attr('data-column-index', column_index);
            $element.attr('data-fieldname', column.fieldname);
            $element.addClass('list-row-col');
            
            // Create header
            const $header = $('<div class="column-header"></div>');
            $header.text(column.label || column.fieldname);
            $header.css({
                'font-weight': 'bold',
                'padding': '8px',
                'border-bottom': '1px solid #ddd',
                'background': '#f8f9fa'
            });
            
            // Create content area for data
            const $content = $('<div class="column-content"></div>');
            $content.css({
                'height': 'calc(100% - 40px)',
                'overflow-y': 'auto'
            });
            
            $element.append($header);
            $element.append($content);
            
            // Add resize handle if resizable
            if (column.resizable !== false) {
                const $resize_handle = $('<div class="column-resize-handle"></div>');
                $resize_handle.css({
                    'position': 'absolute',
                    'right': '0px',
                    'top': '0px',
                    'width': '4px',
                    'height': '100%',
                    'cursor': 'col-resize',
                    'background': 'transparent'
                });
                
                this.setup_column_resize($resize_handle, column_index);
                $element.append($resize_handle);
            }
            
            return $element;
        }
        
        update_column_element($element, column, column_index) {
            $element.attr('data-column-index', column_index);
            $element.attr('data-fieldname', column.fieldname);
            
            // Update header
            const $header = $element.find('.column-header');
            if ($header.length) {
                $header.text(column.label || column.fieldname);
            }
        }
        
        setup_column_resize($resize_handle, column_index) {
            const self = this;
            let is_resizing = false;
            let start_x = 0;
            let start_width = 0;
            
            $resize_handle.on('mousedown', function(e) {
                is_resizing = true;
                start_x = e.pageX;
                
                const position = self.column_positions.get(column_index);
                start_width = position ? position.width : self.default_column_width;
                
                $(document).on('mousemove.column-resize', function(e) {
                    if (!is_resizing) return;
                    
                    const diff = e.pageX - start_x;
                    const new_width = Math.max(50, start_width + diff);
                    
                    self.resize_column(column_index, new_width);
                });
                
                $(document).on('mouseup.column-resize', function() {
                    is_resizing = false;
                    $(document).off('.column-resize');
                    
                    // Save new width
                    self.save_column_width(column_index);
                });
                
                e.preventDefault();
            });
        }
        
        resize_column(column_index, new_width) {
            // Update column width
            this.columns[column_index].width = new_width;
            
            // Recalculate positions
            this.calculate_column_positions();
            
            // Update rendered elements
            this.update_all_column_positions();
            
            // Update container
            this.$content.css('width', this.total_width + 'px');
        }
        
        update_all_column_positions() {
            this.rendered_columns.forEach(($element, column_index) => {
                const position = this.column_positions.get(column_index);
                if (position) {
                    $element.css({
                        'left': position.left + 'px',
                        'width': position.width + 'px'
                    });
                }
            });
        }
        
        save_column_width(column_index) {
            const column = this.columns[column_index];
            if (!column) return;
            
            // Trigger column width change event
            $(document).trigger('column-width-changed', {
                doctype_name: this.doctype,
                fieldname: column.fieldname,
                width: column.width
            });
        }
        
        cleanup_out_of_range_columns() {
            const columns_to_remove = [];
            
            this.rendered_columns.forEach(($element, column_index) => {
                if (!this.visible_columns.includes(column_index)) {
                    columns_to_remove.push(column_index);
                }
            });
            
            columns_to_remove.forEach(column_index => {
                const $element = this.rendered_columns.get(column_index);
                if ($element) {
                    $element.detach();
                    this.recycled_elements.push($element);
                    this.rendered_columns.delete(column_index);
                }
            });
        }
        
        update_container_position() {
            // Calculate the leftmost rendered column position
            if (this.visible_columns.length > 0) {
                const leftmost_index = Math.min(...this.visible_columns);
                const position = this.column_positions.get(leftmost_index);
                
                if (position) {
                    this.$visible_area.css('left', position.left + 'px');
                }
            }
        }
        
        on_scroll_end() {
            // Analyze scroll patterns for intelligent preloading
            this.analyze_column_scroll_patterns();
        }
        
        async analyze_column_scroll_patterns() {
            if (this.scroll_history.length < 5) {
                return;
            }
            
            try {
                const response = await frappe.call({
                    method: 'column_management.column_management.services.column_virtualization_service.ColumnVirtualizationService.get_column_metrics',
                    args: {
                        doctype: this.doctype,
                        scroll_history: this.scroll_history
                    }
                });
                
                if (response.message && response.message.success) {
                    const metrics = response.message.data;
                    
                    // Schedule intelligent preloading based on patterns
                    if (metrics.predicted_column_ranges && metrics.predicted_column_ranges.length > 0) {
                        this.schedule_column_preload(metrics.predicted_column_ranges);
                    }
                }
                
            } catch (error) {
                console.error('Error analyzing column scroll patterns:', error);
            }
        }
        
        async schedule_column_preload(ranges) {
            try {
                await frappe.call({
                    method: 'column_management.column_management.services.column_virtualization_service.ColumnVirtualizationService.preload_columns',
                    args: {
                        doctype: this.doctype,
                        column_ranges: ranges,
                        columns: this.columns
                    }
                });
                
            } catch (error) {
                console.error('Error preloading columns:', error);
            }
        }
        
        // Public API methods
        
        update_columns(new_columns) {
            this.columns = new_columns;
            this.calculate_column_positions();
            this.invalidate_cache();
            this.render_initial_columns();
        }
        
        scroll_to_column(column_index) {
            const position = this.column_positions.get(column_index);
            if (position) {
                this.$viewport.scrollLeft(position.left);
            }
        }
        
        scroll_to_field(fieldname) {
            const column_index = this.columns.findIndex(col => col.fieldname === fieldname);
            if (column_index >= 0) {
                this.scroll_to_column(column_index);
            }
        }
        
        get_visible_column_fields() {
            return this.visible_columns.map(index => {
                const column = this.columns[index];
                return column ? column.fieldname : null;
            }).filter(Boolean);
        }
        
        refresh() {
            this.invalidate_cache();
            this.render_initial_columns();
        }
        
        async invalidate_cache() {
            try {
                await frappe.call({
                    method: 'column_management.column_management.services.column_virtualization_service.ColumnVirtualizationService.invalidate_column_cache',
                    args: {
                        doctype: this.doctype
                    }
                });
            } catch (error) {
                console.error('Error invalidating column cache:', error);
            }
        }
        
        destroy() {
            // Clean up event listeners
            this.$viewport.off('scroll');
            $(document).off('.column-resize');
            clearTimeout(this.scroll_timeout);
            clearTimeout(this.scroll_handle_timeout);
            
            // Clear caches
            this.rendered_columns.clear();
            this.column_cache.clear();
            this.column_positions.clear();
            this.recycled_elements = [];
            this.scroll_history = [];
            
            // Remove DOM elements
            this.$container.empty();
        }
    },
    
    /**
     * Create column virtualization manager for a list view
     */
    create_for_list_view: function(list_view, options = {}) {
        const container = list_view.$result.get(0);
        
        // Get columns from list view
        const columns = this.extract_columns_from_list_view(list_view);
        
        const manager = new this.ColumnVirtualizationManager({
            container: container,
            doctype: list_view.doctype,
            columns: columns,
            viewport_width: options.viewport_width || 1200,
            default_column_width: options.default_column_width || 150,
            buffer_columns: options.buffer_columns || 5
        });
        
        // Store reference on list view
        list_view.column_virtualization_manager = manager;
        
        return manager;
    },
    
    /**
     * Extract column configuration from list view
     */
    extract_columns_from_list_view: function(list_view) {
        const columns = [];
        
        // Get columns from list view configuration
        if (list_view.columns) {
            list_view.columns.forEach(column => {
                columns.push({
                    fieldname: column.fieldname,
                    label: column.label || column.fieldname,
                    fieldtype: column.fieldtype || 'Data',
                    width: column.width || 150,
                    visible: column.visible !== false,
                    resizable: column.resizable !== false,
                    sortable: column.sortable !== false,
                    filterable: column.filterable !== false
                });
            });
        }
        
        return columns;
    },
    
    /**
     * Check if column virtualization should be enabled
     */
    should_enable_column_virtualization: function(columns, viewport_width) {
        // Calculate total width of all columns
        const total_width = columns.reduce((sum, col) => sum + (col.width || 150), 0);
        
        // Enable if total width exceeds viewport by significant margin
        return total_width > viewport_width * 1.5;
    }
};

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = column_management.column_virtualization;
}