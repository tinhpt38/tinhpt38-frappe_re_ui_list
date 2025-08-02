/**
 * Virtual Scrolling Implementation for Large Datasets
 * Copyright (c) 2024, ERPNext Column Management Team
 */

frappe.provide('column_management.virtual_scroll');

column_management.virtual_scroll = {
    
    /**
     * Virtual scroll manager class
     */
    VirtualScrollManager: class {
        constructor(options) {
            this.container = options.container;
            this.doctype = options.doctype;
            this.item_height = options.item_height || 40;
            this.buffer_size = options.buffer_size || 50;
            this.viewport_height = options.viewport_height || 600;
            this.filters = options.filters || [];
            this.sort_by = options.sort_by;
            this.sort_order = options.sort_order || 'asc';
            this.columns = options.columns || [];
            
            // State management
            this.total_count = 0;
            this.total_height = 0;
            this.scroll_top = 0;
            this.visible_start = 0;
            this.visible_end = 0;
            this.rendered_items = new Map();
            this.scroll_history = [];
            this.preload_queue = [];
            
            // Performance tracking
            this.last_scroll_time = 0;
            this.scroll_velocity = 0;
            this.is_scrolling = false;
            this.scroll_timeout = null;
            
            // Cache for rendered elements
            this.element_cache = new Map();
            this.recycled_elements = [];
            
            this.init();
        }
        
        init() {
            this.setup_container();
            this.setup_scroll_listener();
            this.load_initial_data();
        }
        
        setup_container() {
            // Create virtual scroll structure
            this.$container = $(this.container);
            this.$container.addClass('virtual-scroll-container');
            
            // Create viewport
            this.$viewport = $('<div class="virtual-scroll-viewport"></div>');
            this.$viewport.css({
                'height': this.viewport_height + 'px',
                'overflow-y': 'auto',
                'position': 'relative'
            });
            
            // Create content area
            this.$content = $('<div class="virtual-scroll-content"></div>');
            this.$content.css({
                'position': 'relative',
                'height': '0px'  // Will be updated based on total count
            });
            
            // Create visible area for rendered items
            this.$visible_area = $('<div class="virtual-scroll-visible"></div>');
            this.$visible_area.css({
                'position': 'absolute',
                'top': '0px',
                'left': '0px',
                'right': '0px'
            });
            
            this.$content.append(this.$visible_area);
            this.$viewport.append(this.$content);
            this.$container.append(this.$viewport);
        }
        
        setup_scroll_listener() {
            const self = this;
            
            this.$viewport.on('scroll', function(e) {
                const current_time = Date.now();
                const scroll_top = this.scrollTop;
                
                // Calculate scroll velocity
                if (self.last_scroll_time > 0) {
                    const time_diff = current_time - self.last_scroll_time;
                    const scroll_diff = Math.abs(scroll_top - self.scroll_top);
                    self.scroll_velocity = time_diff > 0 ? scroll_diff / time_diff : 0;
                }
                
                self.scroll_top = scroll_top;
                self.last_scroll_time = current_time;
                self.is_scrolling = true;
                
                // Add to scroll history for pattern analysis
                self.scroll_history.push({
                    position: scroll_top,
                    timestamp: current_time
                });
                
                // Keep only recent history
                if (self.scroll_history.length > 20) {
                    self.scroll_history.shift();
                }
                
                // Handle scroll
                self.handle_scroll();
                
                // Set scroll end timeout
                clearTimeout(self.scroll_timeout);
                self.scroll_timeout = setTimeout(() => {
                    self.is_scrolling = false;
                    self.on_scroll_end();
                }, 150);
            });
        }
        
        async load_initial_data() {
            try {
                // Get total count first
                const count_response = await this.get_total_count();
                if (count_response.success) {
                    this.total_count = count_response.data.total_count;
                    this.total_height = this.total_count * this.item_height;
                    
                    // Update content height
                    this.$content.css('height', this.total_height + 'px');
                }
                
                // Load initial viewport data
                await this.load_viewport_data();
                
            } catch (error) {
                console.error('Error loading initial data:', error);
                frappe.msgprint(__('Error loading data: {0}', [error.message]));
            }
        }
        
        async load_viewport_data() {
            const viewport_start = this.scroll_top;
            const viewport_end = this.scroll_top + this.viewport_height;
            
            try {
                const response = await frappe.call({
                    method: 'column_management.column_management.services.virtual_scroll_service.VirtualScrollService.get_virtual_data',
                    args: {
                        doctype: this.doctype,
                        viewport_start: viewport_start,
                        viewport_end: viewport_end,
                        total_height: this.total_height,
                        item_height: this.item_height,
                        filters: this.filters,
                        sort_by: this.sort_by,
                        sort_order: this.sort_order,
                        columns: this.columns
                    }
                });
                
                if (response.message && response.message.success) {
                    const data = response.message.data;
                    this.render_items(data.items, data.buffer_start);
                    
                    // Handle preloading
                    if (data.preload_info && data.preload_info.should_preload) {
                        this.schedule_preload(data.preload_info.ranges);
                    }
                }
                
            } catch (error) {
                console.error('Error loading viewport data:', error);
            }
        }
        
        handle_scroll() {
            // Throttle scroll handling
            if (this.scroll_handle_timeout) {
                return;
            }
            
            this.scroll_handle_timeout = setTimeout(() => {
                this.update_visible_range();
                this.load_viewport_data();
                this.scroll_handle_timeout = null;
            }, 16); // ~60fps
        }
        
        update_visible_range() {
            const viewport_start = this.scroll_top;
            const viewport_end = this.scroll_top + this.viewport_height;
            
            this.visible_start = Math.floor(viewport_start / this.item_height);
            this.visible_end = Math.ceil(viewport_end / this.item_height);
        }
        
        render_items(items, start_index) {
            // Clear existing items that are out of range
            this.cleanup_out_of_range_items(start_index, start_index + items.length);
            
            // Render new items
            items.forEach((item, index) => {
                const virtual_index = start_index + index;
                this.render_item(item, virtual_index);
            });
        }
        
        render_item(item, virtual_index) {
            // Check if item is already rendered
            if (this.rendered_items.has(virtual_index)) {
                return;
            }
            
            // Get or create element
            const $element = this.get_or_create_element(item, virtual_index);
            
            // Position element
            const top_position = virtual_index * this.item_height;
            $element.css({
                'position': 'absolute',
                'top': top_position + 'px',
                'left': '0px',
                'right': '0px',
                'height': this.item_height + 'px'
            });
            
            // Add to visible area
            this.$visible_area.append($element);
            this.rendered_items.set(virtual_index, $element);
        }
        
        get_or_create_element(item, virtual_index) {
            // Try to recycle an element
            if (this.recycled_elements.length > 0) {
                const $element = this.recycled_elements.pop();
                this.update_element_content($element, item, virtual_index);
                return $element;
            }
            
            // Create new element
            return this.create_element(item, virtual_index);
        }
        
        create_element(item, virtual_index) {
            const $element = $('<div class="virtual-scroll-item list-row"></div>');
            $element.attr('data-virtual-index', virtual_index);
            $element.attr('data-row-id', item._row_id);
            
            // Create columns
            this.columns.forEach(column => {
                const fieldname = column.fieldname;
                const value = item[fieldname] || '';
                const width = column.width || 'auto';
                
                const $col = $('<div class="list-row-col"></div>');
                $col.attr('data-fieldname', fieldname);
                $col.css('width', width);
                $col.text(value);
                
                $element.append($col);
            });
            
            return $element;
        }
        
        update_element_content($element, item, virtual_index) {
            $element.attr('data-virtual-index', virtual_index);
            $element.attr('data-row-id', item._row_id);
            
            // Update column values
            this.columns.forEach(column => {
                const fieldname = column.fieldname;
                const value = item[fieldname] || '';
                
                const $col = $element.find(`[data-fieldname="${fieldname}"]`);
                if ($col.length) {
                    $col.text(value);
                }
            });
        }
        
        cleanup_out_of_range_items(new_start, new_end) {
            const items_to_remove = [];
            
            this.rendered_items.forEach(($element, virtual_index) => {
                if (virtual_index < new_start - this.buffer_size || 
                    virtual_index > new_end + this.buffer_size) {
                    items_to_remove.push(virtual_index);
                }
            });
            
            items_to_remove.forEach(virtual_index => {
                const $element = this.rendered_items.get(virtual_index);
                if ($element) {
                    $element.detach();
                    this.recycled_elements.push($element);
                    this.rendered_items.delete(virtual_index);
                }
            });
        }
        
        async schedule_preload(ranges) {
            // Add ranges to preload queue
            ranges.forEach(range => {
                if (!this.preload_queue.some(existing => 
                    existing[0] === range[0] && existing[1] === range[1])) {
                    this.preload_queue.push(range);
                }
            });
            
            // Process preload queue
            this.process_preload_queue();
        }
        
        async process_preload_queue() {
            if (this.preload_queue.length === 0 || this.is_preloading) {
                return;
            }
            
            this.is_preloading = true;
            
            try {
                const ranges_to_preload = this.preload_queue.splice(0, 3); // Process 3 at a time
                
                await frappe.call({
                    method: 'column_management.column_management.services.virtual_scroll_service.VirtualScrollService.preload_data',
                    args: {
                        doctype: this.doctype,
                        preload_ranges: ranges_to_preload,
                        filters: this.filters,
                        sort_by: this.sort_by,
                        sort_order: this.sort_order,
                        columns: this.columns
                    }
                });
                
            } catch (error) {
                console.error('Error preloading data:', error);
            } finally {
                this.is_preloading = false;
                
                // Continue processing queue if items remain
                if (this.preload_queue.length > 0) {
                    setTimeout(() => this.process_preload_queue(), 100);
                }
            }
        }
        
        on_scroll_end() {
            // Analyze scroll patterns for intelligent preloading
            this.analyze_scroll_patterns();
        }
        
        async analyze_scroll_patterns() {
            if (this.scroll_history.length < 5) {
                return;
            }
            
            try {
                const response = await frappe.call({
                    method: 'column_management.column_management.services.virtual_scroll_service.VirtualScrollService.get_scroll_metrics',
                    args: {
                        doctype: this.doctype,
                        scroll_history: this.scroll_history
                    }
                });
                
                if (response.message && response.message.success) {
                    const metrics = response.message.data;
                    
                    // Schedule intelligent preloading based on patterns
                    if (metrics.predicted_ranges && metrics.predicted_ranges.length > 0) {
                        this.schedule_preload(metrics.predicted_ranges);
                    }
                }
                
            } catch (error) {
                console.error('Error analyzing scroll patterns:', error);
            }
        }
        
        async get_total_count() {
            try {
                const response = await frappe.call({
                    method: 'column_management.column_management.api.enhanced_list.get_filter_statistics',
                    args: {
                        doctype: this.doctype,
                        filters: this.filters
                    }
                });
                
                return response.message || { success: false };
                
            } catch (error) {
                console.error('Error getting total count:', error);
                return { success: false };
            }
        }
        
        // Public API methods
        
        update_filters(new_filters) {
            this.filters = new_filters;
            this.invalidate_cache();
            this.load_initial_data();
        }
        
        update_sort(sort_by, sort_order) {
            this.sort_by = sort_by;
            this.sort_order = sort_order;
            this.invalidate_cache();
            this.load_initial_data();
        }
        
        update_columns(new_columns) {
            this.columns = new_columns;
            this.invalidate_cache();
            this.load_initial_data();
        }
        
        scroll_to_index(index) {
            const target_position = index * this.item_height;
            this.$viewport.scrollTop(target_position);
        }
        
        scroll_to_top() {
            this.$viewport.scrollTop(0);
        }
        
        scroll_to_bottom() {
            this.$viewport.scrollTop(this.total_height);
        }
        
        refresh() {
            this.invalidate_cache();
            this.load_initial_data();
        }
        
        async invalidate_cache() {
            try {
                await frappe.call({
                    method: 'column_management.column_management.services.virtual_scroll_service.VirtualScrollService.invalidate_virtual_cache',
                    args: {
                        doctype: this.doctype
                    }
                });
            } catch (error) {
                console.error('Error invalidating cache:', error);
            }
        }
        
        destroy() {
            // Clean up event listeners
            this.$viewport.off('scroll');
            clearTimeout(this.scroll_timeout);
            clearTimeout(this.scroll_handle_timeout);
            
            // Clear caches
            this.rendered_items.clear();
            this.element_cache.clear();
            this.recycled_elements = [];
            this.preload_queue = [];
            this.scroll_history = [];
            
            // Remove DOM elements
            this.$container.empty();
        }
    },
    
    /**
     * Create virtual scroll manager for a list view
     */
    create_for_list_view: function(list_view, options = {}) {
        const container = list_view.$result.get(0);
        
        const manager = new this.VirtualScrollManager({
            container: container,
            doctype: list_view.doctype,
            item_height: options.item_height || 40,
            buffer_size: options.buffer_size || 50,
            viewport_height: options.viewport_height || 600,
            filters: list_view.get_filters_for_args(),
            sort_by: list_view.sort_by,
            sort_order: list_view.sort_order,
            columns: options.columns || []
        });
        
        // Store reference on list view
        list_view.virtual_scroll_manager = manager;
        
        return manager;
    },
    
    /**
     * Check if virtual scrolling should be enabled for a doctype
     */
    should_enable_virtual_scroll: function(doctype, record_count) {
        // Enable virtual scrolling for large datasets
        const threshold = frappe.boot.virtual_scroll_threshold || 1000;
        return record_count > threshold;
    }
};

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = column_management.virtual_scroll;
}