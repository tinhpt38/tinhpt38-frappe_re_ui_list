/**
 * Column Manager Component
 * Handles column selection, ordering, and configuration
 * Enhanced with drag-and-drop, validation, and responsive design
 */

class ColumnManager {
    constructor(options) {
        this.doctype = options.doctype;
        this.listview = options.listview;
        this.columns = [];
        this.user_preferences = {};
        this.dialog = null;
        this.sortable = null;
        this.search_term = '';
        this.is_loading = false;
        
        // Validation rules
        this.validation_rules = {
            min_width: 50,
            max_width: 1000,
            max_columns: 50,
            required_columns: ['name'] // Always keep name column
        };
        
        this.init();
    }
    
    init() {
        this.load_column_config();
        this.setup_ui();
    }
    
    async load_column_config() {
        try {
            const response = await frappe.call({
                method: 'column_management.api.column_manager.get_column_config',
                args: {
                    doctype: this.doctype
                }
            });
            
            if (response.message) {
                this.columns = response.message.columns || [];
                this.user_preferences = response.message.preferences || {};
            }
        } catch (error) {
            console.error('Error loading column config:', error);
            this.load_default_columns();
        }
    }
    
    load_default_columns() {
        // Get default columns from DocType meta
        const meta = frappe.get_meta(this.doctype);
        this.columns = meta.fields
            .filter(field => field.in_list_view)
            .map((field, index) => ({
                fieldname: field.fieldname,
                label: field.label,
                fieldtype: field.fieldtype,
                width: 120,
                visible: true,
                order: index,
                pinned: null
            }));
    }
    
    setup_ui() {
        this.add_manage_columns_button();
    }
    
    add_manage_columns_button() {
        if (!this.listview || !this.listview.page) return;
        
        // Add button to list view toolbar
        this.listview.page.add_action_item(__('Manage Columns'), () => {
            this.show_column_manager_dialog();
        }, false, 'fa fa-columns');
    } 
   
    show_column_manager_dialog() {
        if (this.dialog) {
            this.dialog.show();
            return;
        }
        
        this.dialog = new frappe.ui.Dialog({
            title: __('Manage Columns'),
            size: 'large',
            fields: [
                {
                    fieldtype: 'HTML',
                    fieldname: 'column_manager_html',
                    options: this.get_column_manager_html()
                }
            ],
            primary_action_label: __('Save'),
            primary_action: () => {
                this.save_column_config();
            },
            secondary_action_label: __('Reset'),
            secondary_action: () => {
                this.reset_to_default();
            }
        });
        
        this.dialog.show();
        this.setup_column_manager_events();
    }
    
    get_column_manager_html() {
        const visible_count = this.columns.filter(col => col.visible).length;
        const total_count = this.columns.length;
        
        return `
            <div class="column-manager ${this.is_loading ? 'loading' : ''}">
                <div class="column-manager-header">
                    <h5>${__('Select and arrange columns')}</h5>
                    <p class="text-muted">${__('Drag and drop to reorder columns. Use search to find specific columns.')}</p>
                </div>
                
                <div class="column-search">
                    <input type="text" 
                           class="form-control" 
                           placeholder="${__('Search columns...')}"
                           id="column-search-input"
                           value="${this.search_term}">
                </div>
                
                <div class="column-stats">
                    <span>${__('Visible')}: ${visible_count}</span>
                    <span>${__('Total')}: ${total_count}</span>
                    <span>${__('Hidden')}: ${total_count - visible_count}</span>
                </div>
                
                <div class="column-list" id="column-list">
                    ${this.get_column_items_html()}
                </div>
                
                <div class="column-manager-footer">
                    <button class="btn btn-sm btn-default" onclick="column_manager.select_all()">
                        <i class="fa fa-check-square"></i> ${__('Select All')}
                    </button>
                    <button class="btn btn-sm btn-default" onclick="column_manager.deselect_all()">
                        <i class="fa fa-square-o"></i> ${__('Deselect All')}
                    </button>
                    <button class="btn btn-sm btn-default" onclick="column_manager.auto_resize_columns()">
                        <i class="fa fa-arrows-h"></i> ${__('Auto Resize')}
                    </button>
                </div>
            </div>
        `;
    }
    
    get_column_items_html() {
        const filtered_columns = this.get_filtered_columns();
        
        if (filtered_columns.length === 0) {
            return `
                <div class="column-item disabled">
                    <div class="column-item-content">
                        <span class="text-muted">${__('No columns found matching search criteria')}</span>
                    </div>
                </div>
            `;
        }
        
        return filtered_columns
            .sort((a, b) => a.order - b.order)
            .map(column => {
                const is_required = this.validation_rules.required_columns.includes(column.fieldname);
                const validation_class = this.get_column_validation_class(column);
                
                return `
                    <div class="column-item ${validation_class}" 
                         data-fieldname="${column.fieldname}"
                         data-pinned="${column.pinned || ''}">
                        <div class="column-item-content">
                            <span class="drag-handle" title="${__('Drag to reorder')}">⋮⋮</span>
                            <input type="checkbox" 
                                   class="column-checkbox" 
                                   ${column.visible ? 'checked' : ''}
                                   ${is_required ? 'disabled' : ''}
                                   title="${is_required ? __('This column is required') : ''}">
                            <span class="column-label" title="${column.fieldname}">
                                ${column.label}
                                ${is_required ? ' <span class="text-danger">*</span>' : ''}
                            </span>
                            <span class="column-type">${column.fieldtype}</span>
                            <div class="column-controls">
                                <select class="pin-select form-control input-sm" 
                                        title="${__('Pin column position')}">
                                    <option value="">${__('No Pin')}</option>
                                    <option value="left" ${column.pinned === 'left' ? 'selected' : ''}>
                                        ${__('Pin Left')}
                                    </option>
                                    <option value="right" ${column.pinned === 'right' ? 'selected' : ''}>
                                        ${__('Pin Right')}
                                    </option>
                                </select>
                                <input type="number" 
                                       class="width-input form-control input-sm" 
                                       value="${column.width}" 
                                       min="${this.validation_rules.min_width}" 
                                       max="${this.validation_rules.max_width}"
                                       title="${__('Column width in pixels')}"
                                       placeholder="Width">
                            </div>
                        </div>
                    </div>
                `;
            }).join('');
    }
    
    get_filtered_columns() {
        if (!this.search_term) {
            return this.columns;
        }
        
        const term = this.search_term.toLowerCase();
        return this.columns.filter(column => 
            column.label.toLowerCase().includes(term) ||
            column.fieldname.toLowerCase().includes(term) ||
            column.fieldtype.toLowerCase().includes(term)
        );
    }
    
    get_column_validation_class(column) {
        const classes = [];
        
        if (column.width < this.validation_rules.min_width || 
            column.width > this.validation_rules.max_width) {
            classes.push('error');
        }
        
        return classes.join(' ');
    } 
   
    setup_column_manager_events() {
        const container = this.dialog.$wrapper.find('#column-list');
        const search_input = this.dialog.$wrapper.find('#column-search-input');
        
        // Setup search functionality
        search_input.on('input', frappe.utils.debounce((e) => {
            this.search_term = $(e.target).val();
            this.refresh_column_list();
        }, 300));
        
        // Clear search on Escape
        search_input.on('keydown', (e) => {
            if (e.key === 'Escape') {
                $(e.target).val('');
                this.search_term = '';
                this.refresh_column_list();
            }
        });
        
        // Make list sortable with enhanced options
        this.setup_sortable(container);
        
        // Column checkbox events with validation
        container.on('change', '.column-checkbox', (e) => {
            const fieldname = $(e.target).closest('.column-item').data('fieldname');
            const visible = $(e.target).is(':checked');
            
            if (this.validate_column_visibility(fieldname, visible)) {
                this.update_column_visibility(fieldname, visible);
                this.update_column_stats();
            } else {
                // Revert checkbox state
                $(e.target).prop('checked', !visible);
            }
        });
        
        // Pin select events with conflict resolution
        container.on('change', '.pin-select', (e) => {
            const fieldname = $(e.target).closest('.column-item').data('fieldname');
            const pinned = $(e.target).val() || null;
            
            if (this.validate_column_pin(fieldname, pinned)) {
                this.update_column_pin(fieldname, pinned);
                this.refresh_column_list();
            } else {
                // Revert select state
                const column = this.columns.find(col => col.fieldname === fieldname);
                $(e.target).val(column.pinned || '');
            }
        });
        
        // Width input events with real-time validation
        container.on('input', '.width-input', frappe.utils.debounce((e) => {
            const fieldname = $(e.target).closest('.column-item').data('fieldname');
            const width = parseInt($(e.target).val()) || 120;
            
            if (this.validate_column_width(fieldname, width)) {
                this.update_column_width(fieldname, width);
                this.update_column_validation_display(fieldname);
            }
        }, 300));
        
        // Width input blur event for final validation
        container.on('blur', '.width-input', (e) => {
            const fieldname = $(e.target).closest('.column-item').data('fieldname');
            const width = parseInt($(e.target).val()) || 120;
            const corrected_width = this.correct_column_width(width);
            
            if (width !== corrected_width) {
                $(e.target).val(corrected_width);
                this.update_column_width(fieldname, corrected_width);
            }
        });
        
        // Keyboard shortcuts
        this.setup_keyboard_shortcuts();
    }
    
    setup_sortable(container) {
        if (typeof Sortable !== 'undefined') {
            this.sortable = new Sortable(container[0], {
                handle: '.drag-handle',
                animation: 150,
                ghostClass: 'sortable-ghost',
                chosenClass: 'sortable-chosen',
                dragClass: 'sortable-drag',
                onStart: (evt) => {
                    container.addClass('sorting');
                },
                onEnd: (evt) => {
                    container.removeClass('sorting');
                    this.update_column_order();
                    this.show_reorder_feedback();
                }
            });
        } else {
            console.warn('Sortable.js not loaded. Drag and drop functionality disabled.');
        }
    }
    
    setup_keyboard_shortcuts() {
        this.dialog.$wrapper.on('keydown', (e) => {
            if (e.ctrlKey || e.metaKey) {
                switch(e.key) {
                    case 'a':
                        e.preventDefault();
                        this.select_all();
                        break;
                    case 'd':
                        e.preventDefault();
                        this.deselect_all();
                        break;
                    case 's':
                        e.preventDefault();
                        this.save_column_config();
                        break;
                    case 'r':
                        e.preventDefault();
                        this.reset_to_default();
                        break;
                }
            }
        });
    }
    
    refresh_column_list() {
        const container = this.dialog.$wrapper.find('#column-list');
        container.html(this.get_column_items_html());
        this.setup_sortable(container);
        this.update_column_stats();
    }
    
    update_column_stats() {
        const visible_count = this.columns.filter(col => col.visible).length;
        const total_count = this.columns.length;
        const stats_html = `
            <span>${__('Visible')}: ${visible_count}</span>
            <span>${__('Total')}: ${total_count}</span>
            <span>${__('Hidden')}: ${total_count - visible_count}</span>
        `;
        this.dialog.$wrapper.find('.column-stats').html(stats_html);
    }
    
    update_column_order() {
        const items = this.dialog.$wrapper.find('.column-item');
        items.each((index, item) => {
            const fieldname = $(item).data('fieldname');
            const column = this.columns.find(col => col.fieldname === fieldname);
            if (column) {
                column.order = index;
            }
        });
    }
    
    update_column_visibility(fieldname, visible) {
        const column = this.columns.find(col => col.fieldname === fieldname);
        if (column) {
            column.visible = visible;
        }
    }
    
    update_column_pin(fieldname, pinned) {
        const column = this.columns.find(col => col.fieldname === fieldname);
        if (column) {
            column.pinned = pinned;
        }
    }
    
    update_column_width(fieldname, width) {
        const column = this.columns.find(col => col.fieldname === fieldname);
        if (column) {
            column.width = Math.max(50, Math.min(1000, width));
        }
    } 
   
    // Validation methods
    validate_column_visibility(fieldname, visible) {
        if (!visible && this.validation_rules.required_columns.includes(fieldname)) {
            frappe.show_alert({
                message: __('This column is required and cannot be hidden'),
                indicator: 'red'
            });
            return false;
        }
        
        const visible_count = this.columns.filter(col => col.visible).length;
        if (!visible && visible_count <= 1) {
            frappe.show_alert({
                message: __('At least one column must be visible'),
                indicator: 'red'
            });
            return false;
        }
        
        return true;
    }
    
    validate_column_pin(fieldname, pinned) {
        if (!pinned) return true;
        
        const pinned_count = this.columns.filter(col => col.pinned === pinned).length;
        if (pinned_count >= 5) {
            frappe.show_alert({
                message: __('Maximum 5 columns can be pinned to each side'),
                indicator: 'orange'
            });
            return false;
        }
        
        return true;
    }
    
    validate_column_width(fieldname, width) {
        return width >= this.validation_rules.min_width && 
               width <= this.validation_rules.max_width;
    }
    
    correct_column_width(width) {
        return Math.max(
            this.validation_rules.min_width,
            Math.min(this.validation_rules.max_width, width)
        );
    }
    
    update_column_validation_display(fieldname) {
        const column = this.columns.find(col => col.fieldname === fieldname);
        const item = this.dialog.$wrapper.find(`[data-fieldname="${fieldname}"]`);
        
        item.removeClass('error warning');
        
        if (column.width < this.validation_rules.min_width || 
            column.width > this.validation_rules.max_width) {
            item.addClass('error');
        }
    }
    
    show_reorder_feedback() {
        frappe.show_alert({
            message: __('Column order updated'),
            indicator: 'blue'
        });
    }
    
    // Utility methods
    select_all() {
        let changed = false;
        this.columns.forEach(column => {
            if (!this.validation_rules.required_columns.includes(column.fieldname) || !column.visible) {
                column.visible = true;
                changed = true;
            }
        });
        
        if (changed) {
            this.refresh_column_list();
            frappe.show_alert({
                message: __('All columns selected'),
                indicator: 'green'
            });
        }
    }
    
    deselect_all() {
        let changed = false;
        this.columns.forEach(column => {
            if (!this.validation_rules.required_columns.includes(column.fieldname) && column.visible) {
                column.visible = false;
                changed = true;
            }
        });
        
        if (changed) {
            this.refresh_column_list();
            frappe.show_alert({
                message: __('All non-required columns deselected'),
                indicator: 'blue'
            });
        }
    }
    
    auto_resize_columns() {
        frappe.confirm(
            __('Auto-resize all columns to optimal width?'),
            () => {
                this.columns.forEach(column => {
                    // Calculate optimal width based on field type and label length
                    let optimal_width = Math.max(
                        column.label.length * 8 + 40,
                        this.get_field_type_width(column.fieldtype)
                    );
                    
                    column.width = this.correct_column_width(optimal_width);
                });
                
                this.refresh_column_list();
                frappe.show_alert({
                    message: __('Columns auto-resized'),
                    indicator: 'green'
                });
            }
        );
    }
    
    get_field_type_width(fieldtype) {
        const width_map = {
            'Check': 80,
            'Int': 100,
            'Float': 120,
            'Currency': 140,
            'Date': 120,
            'Datetime': 160,
            'Time': 100,
            'Link': 150,
            'Select': 120,
            'Data': 150,
            'Text': 200,
            'Small Text': 250,
            'Long Text': 300,
            'Code': 200,
            'Text Editor': 300,
            'HTML Editor': 300,
            'Attach': 120,
            'Attach Image': 120,
            'Signature': 150,
            'Color': 100,
            'Barcode': 150,
            'Geolocation': 150
        };
        
        return width_map[fieldtype] || 150;
    }
    
    async save_column_config() {
        // Validate configuration before saving
        if (!this.validate_configuration()) {
            return;
        }
        
        try {
            this.set_loading_state(true);
            frappe.show_progress(__('Saving'), 30, 100, __('Validating configuration...'));
            
            // Prepare configuration data
            const config_data = this.prepare_config_data();
            
            frappe.show_progress(__('Saving'), 60, 100, __('Saving to server...'));
            
            const response = await frappe.call({
                method: 'column_management.api.column_manager.save_column_config',
                args: {
                    doctype: this.doctype,
                    config: config_data
                },
                freeze: true,
                freeze_message: __('Saving column configuration...')
            });
            
            frappe.show_progress(__('Saving'), 90, 100, __('Applying changes...'));
            
            if (response.message && response.message.success) {
                // Update local state
                this.user_preferences = response.message.preferences || this.user_preferences;
                
                frappe.show_alert({
                    message: __('Column configuration saved successfully'),
                    indicator: 'green'
                });
                
                this.dialog.hide();
                await this.apply_column_config();
                
                // Trigger custom event for other components
                $(document).trigger('column_config_saved', {
                    doctype: this.doctype,
                    config: config_data
                });
                
            } else {
                throw new Error(response.message?.error || __('Save operation failed'));
            }
        } catch (error) {
            console.error('Save column config error:', error);
            frappe.show_alert({
                message: __('Error saving configuration: ') + (error.message || error),
                indicator: 'red'
            });
        } finally {
            frappe.hide_progress();
            this.set_loading_state(false);
        }
    }
    
    validate_configuration() {
        const visible_columns = this.columns.filter(col => col.visible);
        
        if (visible_columns.length === 0) {
            frappe.msgprint({
                title: __('Validation Error'),
                message: __('At least one column must be visible'),
                indicator: 'red'
            });
            return false;
        }
        
        if (visible_columns.length > this.validation_rules.max_columns) {
            frappe.msgprint({
                title: __('Validation Error'),
                message: __('Maximum {0} columns can be displayed', [this.validation_rules.max_columns]),
                indicator: 'red'
            });
            return false;
        }
        
        // Check for invalid widths
        const invalid_widths = this.columns.filter(col => 
            col.width < this.validation_rules.min_width || 
            col.width > this.validation_rules.max_width
        );
        
        if (invalid_widths.length > 0) {
            frappe.msgprint({
                title: __('Validation Error'),
                message: __('Some columns have invalid widths. Please check and correct them.'),
                indicator: 'red'
            });
            return false;
        }
        
        return true;
    }
    
    prepare_config_data() {
        return {
            columns: this.columns.map(col => ({
                fieldname: col.fieldname,
                label: col.label,
                fieldtype: col.fieldtype,
                width: col.width,
                visible: col.visible,
                order: col.order,
                pinned: col.pinned
            })),
            preferences: {
                ...this.user_preferences,
                last_modified: frappe.datetime.now_datetime(),
                version: '1.0'
            },
            metadata: {
                doctype: this.doctype,
                user: frappe.session.user,
                timestamp: frappe.datetime.now_datetime()
            }
        };
    }
    
    set_loading_state(loading) {
        this.is_loading = loading;
        const manager_div = this.dialog.$wrapper.find('.column-manager');
        
        if (loading) {
            manager_div.addClass('loading');
        } else {
            manager_div.removeClass('loading');
        }
    }
    
    async reset_to_default() {
        frappe.confirm(
            __('Are you sure you want to reset to default column configuration?'),
            () => {
                this.load_default_columns();
                this.dialog.fields_dict.column_manager_html.$wrapper.html(
                    this.get_column_manager_html()
                );
                this.setup_column_manager_events();
                
                frappe.show_alert({
                    message: __('Reset to default configuration'),
                    indicator: 'blue'
                });
            }
        );
    }
    
    async apply_column_config() {
        try {
            if (!this.listview) {
                console.warn('No listview instance available for applying column config');
                return;
            }
            
            // Update listview columns configuration
            if (this.listview.columns) {
                this.listview.columns = this.get_visible_columns_config();
            }
            
            // Refresh the list view with new configuration
            if (this.listview.refresh) {
                await this.listview.refresh();
            } else if (this.listview.reload) {
                await this.listview.reload();
            }
            
            // Apply column widths and pinning if supported
            this.apply_column_styling();
            
        } catch (error) {
            console.error('Error applying column configuration:', error);
            frappe.show_alert({
                message: __('Error applying column configuration'),
                indicator: 'orange'
            });
        }
    }
    
    get_visible_columns_config() {
        return this.columns
            .filter(col => col.visible)
            .sort((a, b) => a.order - b.order)
            .map(col => ({
                fieldname: col.fieldname,
                label: col.label,
                fieldtype: col.fieldtype,
                width: col.width,
                pinned: col.pinned
            }));
    }
    
    apply_column_styling() {
        // This method would apply CSS styling for column widths and pinning
        // Implementation depends on the specific list view structure
        setTimeout(() => {
            const list_container = $('.list-view-container, .frappe-list');
            if (list_container.length) {
                this.columns.forEach(col => {
                    if (col.visible) {
                        const column_element = list_container.find(`[data-fieldname="${col.fieldname}"]`);
                        if (column_element.length) {
                            column_element.css('width', col.width + 'px');
                            
                            if (col.pinned) {
                                column_element.addClass(`pinned-${col.pinned}`);
                            }
                        }
                    }
                });
            }
        }, 100);
    }
    
    // Cleanup method
    destroy() {
        if (this.sortable) {
            this.sortable.destroy();
        }
        
        if (this.dialog) {
            this.dialog.hide();
        }
        
        // Remove event listeners
        $(document).off('column_config_saved');
    }
}

// Global reference for dialog callbacks
window.column_manager = null;

// Auto-initialize when list view is ready
frappe.listview_settings = frappe.listview_settings || {};

// Hook into list view initialization
$(document).on('list_view_loaded', function(e, listview) {
    if (listview && listview.doctype) {
        window.column_manager = new ColumnManager({
            doctype: listview.doctype,
            listview: listview
        });
    }
});