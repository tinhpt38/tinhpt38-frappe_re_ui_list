// Column Management JavaScript - Clean Version
frappe.provide('column_management');
frappe.provide('column_management.components');

// Initialize column management when page loads
$(document).ready(function () {
    // Check if we're on a list view
    if (cur_list && cur_list.doctype) {
        column_management.init_list_view(cur_list);
    }

    // Initialize components
    column_management.init_components();

    // Initialize enhanced list view integration
    column_management.init_enhanced_list_integration();

    // Initialize unlimited column display system
    column_management.init_unlimited_column_display();

    // Initialize enhanced pagination system
    column_management.init_enhanced_pagination();

    // Initialize dynamic filtering system
    column_management.init_dynamic_filtering();
});

column_management.init_list_view = function (list_view) {
    // Add column management button to list view
    if (!list_view.$page.find('.column-management-btn').length) {
        const btn = $(`
            <button class="btn btn-default btn-sm column-management-btn" 
                    style="margin-left: 10px;">
                <i class="fa fa-columns"></i> Manage Columns
            </button>
        `);

        btn.on('click', function () {
            column_management.show_column_manager(list_view.doctype);
        });

        list_view.$page.find('.page-actions').append(btn);
    }
};

column_management.show_column_manager = function (doctype) {
    // Show column management dialog
    const dialog = new frappe.ui.Dialog({
        title: __('Manage Columns for {0}', [doctype]),
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'column_manager_html',
                options: '<div id="column-manager-container">Loading...</div>'
            }
        ],
        size: 'large'
    });

    dialog.show();

    // Load column configuration
    frappe.call({
        method: 'column_management.api.column_manager.get_column_config',
        args: {
            doctype: doctype
        },
        callback: function (r) {
            if (r.message && r.message.success) {
                const container = dialog.$wrapper.find('#column-manager-container');

                // Initialize ColumnManagerComponent
                const columnManager = new column_management.components.ColumnManager({
                    doctype: doctype,
                    container: container,
                    config: r.message.data,
                    callbacks: {
                        onSave: function (config) {
                            column_management.save_column_config_new(doctype, config, dialog);
                        },
                        onReset: function () {
                            column_management.reset_column_config_new(doctype, dialog);
                        },
                        onPreview: function (config) {
                            column_management.preview_column_config(doctype, config);
                        }
                    }
                });
            } else {
                // Fallback to old method
                column_management.render_column_manager(r.message, dialog);
            }
        }
    });
};

// Initialize components
column_management.init_components = function () {
    // Initialize ColumnManagerComponent
    column_management.components.ColumnManager = class ColumnManager {
        constructor(options) {
            this.doctype = options.doctype;
            this.container = options.container;
            this.config = options.config || {};
            this.callbacks = options.callbacks || {};

            this.init();
        }

        init() {
            this.render();
            this.bind_events();
        }

        render() {
            const columns = this.config.columns || [];
            const available_fields = this.config.available_fields || [];

            let html = `
                <div class="column-manager-component">
                    <div class="row">
                        <div class="col-md-6">
                            <div class="column-section">
                                <h5>${__('Available Columns')}</h5>
                                <div class="search-box">
                                    <input type="text" class="form-control column-search" 
                                           placeholder="${__('Search columns...')}" />
                                </div>
                                <div class="available-columns-list">
                                    ${this.render_available_columns(available_fields, columns)}
                                </div>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="column-section">
                                <h5>${__('Selected Columns')} <span class="selected-count">(${columns.filter(c => c.visible).length})</span></h5>
                                <div class="selected-columns-list sortable-list">
                                    ${this.render_selected_columns(columns)}
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="column-actions">
                        <button class="btn btn-primary save-config">${__('Save Configuration')}</button>
                        <button class="btn btn-default reset-config">${__('Reset to Default')}</button>
                        <button class="btn btn-secondary preview-config">${__('Preview')}</button>
                    </div>
                </div>
            `;

            this.container.html(html);
        }

        render_available_columns(available_fields, selected_columns) {
            let html = '';
            const selected_map = {};

            selected_columns.forEach(col => {
                selected_map[col.fieldname] = col;
            });

            available_fields.forEach(field => {
                const is_selected = selected_map[field.fieldname];
                const checked = is_selected && is_selected.visible ? 'checked' : '';
                const pinned = is_selected ? is_selected.pinned : null;

                // Pin control buttons
                let pinControls = '';
                if (is_selected && is_selected.visible) {
                    if (pinned === 'left') {
                        pinControls = `
                            <button class="btn btn-xs btn-success pin-left" disabled title="${__('Pinned Left')}">
                                <i class="fa fa-thumb-tack"></i> L
                            </button>
                            <button class="btn btn-xs btn-default unpin" title="${__('Unpin')}">
                                <i class="fa fa-times"></i>
                            </button>
                        `;
                    } else if (pinned === 'right') {
                        pinControls = `
                            <button class="btn btn-xs btn-info pin-right" disabled title="${__('Pinned Right')}">
                                <i class="fa fa-thumb-tack"></i> R
                            </button>
                            <button class="btn btn-xs btn-default unpin" title="${__('Unpin')}">
                                <i class="fa fa-times"></i>
                            </button>
                        `;
                    } else {
                        pinControls = `
                            <button class="btn btn-xs btn-default pin-left" title="${__('Pin Left')}">
                                <i class="fa fa-thumb-tack"></i> L
                            </button>
                            <button class="btn btn-xs btn-default pin-right" title="${__('Pin Right')}">
                                <i class="fa fa-thumb-tack"></i> R
                            </button>
                        `;
                    }
                }

                html += `
                    <div class="available-column-item ${pinned ? 'pinned-' + pinned : ''}" data-fieldname="${field.fieldname}">
                        <div class="column-checkbox-wrapper">
                            <label class="checkbox-label">
                                <input type="checkbox" class="column-checkbox" ${checked} />
                                <span class="field-label">${field.label}</span>
                                <small class="field-type">${field.fieldtype}</small>
                            </label>
                        </div>
                        <div class="column-controls">
                            <input type="number" class="form-control column-width" 
                                   value="${is_selected ? is_selected.width : field.width || 100}" 
                                   min="50" max="1000" step="10" />
                            <div class="pin-controls">
                                ${pinControls}
                            </div>
                        </div>
                    </div>
                `;
            });

            return html;
        }

        render_selected_columns(columns) {
            let html = '';
            const visible_columns = columns.filter(col => col.visible).sort((a, b) => (a.order || 0) - (b.order || 0));

            visible_columns.forEach((column, index) => {
                const pinned = column.pinned;
                let pinIndicator = '';
                let pinControls = '';

                // Pin indicator and controls
                if (pinned === 'left') {
                    pinIndicator = '<i class="fa fa-thumb-tack text-success" title="Pinned Left"></i>';
                    pinControls = `
                        <button class="btn btn-xs btn-default unpin" title="${__('Unpin')}">
                            <i class="fa fa-times"></i>
                        </button>
                    `;
                } else if (pinned === 'right') {
                    pinIndicator = '<i class="fa fa-thumb-tack text-info" title="Pinned Right"></i>';
                    pinControls = `
                        <button class="btn btn-xs btn-default unpin" title="${__('Unpin')}">
                            <i class="fa fa-times"></i>
                        </button>
                    `;
                } else {
                    pinControls = `
                        <button class="btn btn-xs btn-default pin-left" title="${__('Pin Left')}">
                            <i class="fa fa-thumb-tack"></i> L
                        </button>
                        <button class="btn btn-xs btn-default pin-right" title="${__('Pin Right')}">
                            <i class="fa fa-thumb-tack"></i> R
                        </button>
                    `;
                }

                html += `
                    <div class="selected-column-item ${pinned ? 'pinned-' + pinned : ''}" 
                         data-fieldname="${column.fieldname}" 
                         data-order="${column.order || index}"
                         oncontextmenu="return false;">
                        <div class="drag-handle">
                            <i class="fa fa-bars"></i>
                        </div>
                        <div class="column-info">
                            <span class="column-label">
                                ${pinIndicator} ${column.label}
                            </span>
                            <small class="column-width-display">${column.width}px</small>
                        </div>
                        <div class="column-actions">
                            ${pinControls}
                            <button class="btn btn-xs remove-column" title="${__('Remove')}">
                                <i class="fa fa-times"></i>
                            </button>
                        </div>
                    </div>
                `;
            });

            if (visible_columns.length === 0) {
                html = `<div class="empty-state">${__('No columns selected. Check columns from the left panel.')}</div>`;
            }

            return html;
        }

        bind_events() {
            const self = this;

            // Column checkbox changes
            this.container.on('change', '.column-checkbox', function () {
                self.toggle_column($(this));
            });

            // Width changes
            this.container.on('change', '.column-width', function () {
                self.update_column_width($(this));
            });

            // Remove column
            this.container.on('click', '.remove-column', function () {
                self.remove_column($(this));
            });

            // Pin controls
            this.container.on('click', '.pin-left', function () {
                self.pin_column($(this), 'left');
            });

            this.container.on('click', '.pin-right', function () {
                self.pin_column($(this), 'right');
            });

            this.container.on('click', '.unpin', function () {
                self.unpin_column($(this));
            });

            // Right-click context menu for column headers
            this.container.on('contextmenu', '.selected-column-item', function (e) {
                e.preventDefault();
                self.show_column_context_menu(e, $(this));
                return false;
            });

            // Hide context menu when clicking elsewhere
            $(document).on('click', function () {
                $('.column-context-menu').remove();
            });

            // Action buttons
            this.container.find('.save-config').on('click', function () {
                self.save_configuration();
            });

            this.container.find('.reset-config').on('click', function () {
                self.reset_configuration();
            });

            this.container.find('.preview-config').on('click', function () {
                self.preview_configuration();
            });
        }

        toggle_column($checkbox) {
            const $item = $checkbox.closest('.available-column-item');
            const fieldname = $item.data('fieldname');
            const is_checked = $checkbox.is(':checked');

            // Update config
            let column = this.config.columns.find(c => c.fieldname === fieldname);
            if (!column) {
                const field = this.config.available_fields.find(f => f.fieldname === fieldname);
                column = {
                    fieldname: fieldname,
                    label: field.label,
                    fieldtype: field.fieldtype,
                    width: field.width || 100,
                    visible: false,
                    order: this.config.columns.length
                };
                this.config.columns.push(column);
            }

            column.visible = is_checked;

            // Re-render selected columns
            this.container.find('.selected-columns-list').html(this.render_selected_columns(this.config.columns));
            this.update_selected_count();
        }

        update_column_width($input) {
            const $item = $input.closest('.available-column-item');
            const fieldname = $item.data('fieldname');
            const width = parseInt($input.val()) || 100;

            // Update config
            let column = this.config.columns.find(c => c.fieldname === fieldname);
            if (column) {
                column.width = width;
            }

            // Update display in selected columns
            const $selected_item = this.container.find(`.selected-column-item[data-fieldname="${fieldname}"]`);
            $selected_item.find('.column-width-display').text(`${width}px`);
        }

        remove_column($btn) {
            const $item = $btn.closest('.selected-column-item');
            const fieldname = $item.data('fieldname');

            // Update config
            const column = this.config.columns.find(c => c.fieldname === fieldname);
            if (column) {
                column.visible = false;
            }

            // Update checkbox in available columns
            this.container.find(`.available-column-item[data-fieldname="${fieldname}"] .column-checkbox`).prop('checked', false);

            // Re-render selected columns
            this.container.find('.selected-columns-list').html(this.render_selected_columns(this.config.columns));
            this.update_selected_count();
        }

        pin_column($btn, position) {
            const $item = $btn.closest('.available-column-item, .selected-column-item');
            const fieldname = $item.data('fieldname');

            // Update config
            const column = this.config.columns.find(c => c.fieldname === fieldname);
            if (column) {
                column.pinned = position;

                // Re-render both available and selected columns to update pin indicators
                this.container.find('.available-columns-list').html(
                    this.render_available_columns(this.config.available_fields, this.config.columns)
                );
                this.container.find('.selected-columns-list').html(
                    this.render_selected_columns(this.config.columns)
                );

                frappe.show_alert({
                    message: __('Column "{0}" pinned to {1}', [column.label, position]),
                    indicator: 'green'
                });
            }
        }

        unpin_column($btn) {
            const $item = $btn.closest('.available-column-item, .selected-column-item');
            const fieldname = $item.data('fieldname');

            // Update config
            const column = this.config.columns.find(c => c.fieldname === fieldname);
            if (column) {
                column.pinned = null;

                // Re-render both available and selected columns to update pin indicators
                this.container.find('.available-columns-list').html(
                    this.render_available_columns(this.config.available_fields, this.config.columns)
                );
                this.container.find('.selected-columns-list').html(
                    this.render_selected_columns(this.config.columns)
                );

                frappe.show_alert({
                    message: __('Column "{0}" unpinned', [column.label]),
                    indicator: 'blue'
                });
            }
        }

        show_column_context_menu(event, $item) {
            const fieldname = $item.data('fieldname');
            const column = this.config.columns.find(c => c.fieldname === fieldname);

            if (!column) return;

            // Remove any existing context menu
            $('.column-context-menu').remove();

            const pinned = column.pinned;
            let menuItems = '';

            // Pin options
            if (pinned === 'left') {
                menuItems += `
                    <button class="dropdown-item unpin-context" data-fieldname="${fieldname}">
                        <i class="fa fa-times"></i> ${__('Unpin')}
                    </button>
                    <button class="dropdown-item pin-right-context" data-fieldname="${fieldname}">
                        <i class="fa fa-thumb-tack"></i> ${__('Pin Right')}
                    </button>
                `;
            } else if (pinned === 'right') {
                menuItems += `
                    <button class="dropdown-item unpin-context" data-fieldname="${fieldname}">
                        <i class="fa fa-times"></i> ${__('Unpin')}
                    </button>
                    <button class="dropdown-item pin-left-context" data-fieldname="${fieldname}">
                        <i class="fa fa-thumb-tack"></i> ${__('Pin Left')}
                    </button>
                `;
            } else {
                menuItems += `
                    <button class="dropdown-item pin-left-context" data-fieldname="${fieldname}">
                        <i class="fa fa-thumb-tack"></i> ${__('Pin Left')}
                    </button>
                    <button class="dropdown-item pin-right-context" data-fieldname="${fieldname}">
                        <i class="fa fa-thumb-tack"></i> ${__('Pin Right')}
                    </button>
                `;
            }

            menuItems += `
                <div class="divider"></div>
                <button class="dropdown-item remove-context" data-fieldname="${fieldname}">
                    <i class="fa fa-trash"></i> ${__('Remove Column')}
                </button>
            `;

            const contextMenu = $(`
                <div class="column-context-menu" style="position: absolute; z-index: 1000;">
                    ${menuItems}
                </div>
            `);

            // Position the menu
            const menuWidth = 150;
            const menuHeight = 120;
            let left = event.pageX;
            let top = event.pageY;

            // Adjust position if menu would go off screen
            if (left + menuWidth > $(window).width()) {
                left = event.pageX - menuWidth;
            }
            if (top + menuHeight > $(window).height()) {
                top = event.pageY - menuHeight;
            }

            contextMenu.css({
                left: left + 'px',
                top: top + 'px'
            });

            $('body').append(contextMenu);

            // Bind context menu events
            const self = this;
            contextMenu.on('click', '.pin-left-context', function () {
                const fieldname = $(this).data('fieldname');
                self.pin_column_by_fieldname(fieldname, 'left');
                $('.column-context-menu').remove();
            });

            contextMenu.on('click', '.pin-right-context', function () {
                const fieldname = $(this).data('fieldname');
                self.pin_column_by_fieldname(fieldname, 'right');
                $('.column-context-menu').remove();
            });

            contextMenu.on('click', '.unpin-context', function () {
                const fieldname = $(this).data('fieldname');
                self.unpin_column_by_fieldname(fieldname);
                $('.column-context-menu').remove();
            });

            contextMenu.on('click', '.remove-context', function () {
                const fieldname = $(this).data('fieldname');
                self.remove_column_by_fieldname(fieldname);
                $('.column-context-menu').remove();
            });
        }

        pin_column_by_fieldname(fieldname, position) {
            const column = this.config.columns.find(c => c.fieldname === fieldname);
            if (column) {
                column.pinned = position;

                // Re-render both available and selected columns to update pin indicators
                this.container.find('.available-columns-list').html(
                    this.render_available_columns(this.config.available_fields, this.config.columns)
                );
                this.container.find('.selected-columns-list').html(
                    this.render_selected_columns(this.config.columns)
                );

                frappe.show_alert({
                    message: __('Column "{0}" pinned to {1}', [column.label, position]),
                    indicator: 'green'
                });
            }
        }

        unpin_column_by_fieldname(fieldname) {
            const column = this.config.columns.find(c => c.fieldname === fieldname);
            if (column) {
                column.pinned = null;

                // Re-render both available and selected columns to update pin indicators
                this.container.find('.available-columns-list').html(
                    this.render_available_columns(this.config.available_fields, this.config.columns)
                );
                this.container.find('.selected-columns-list').html(
                    this.render_selected_columns(this.config.columns)
                );

                frappe.show_alert({
                    message: __('Column "{0}" unpinned', [column.label]),
                    indicator: 'blue'
                });
            }
        }

        remove_column_by_fieldname(fieldname) {
            const column = this.config.columns.find(c => c.fieldname === fieldname);
            if (column) {
                column.visible = false;
                column.pinned = null; // Also unpin when removing

                // Update checkbox in available columns
                this.container.find(`.available-column-item[data-fieldname="${fieldname}"] .column-checkbox`).prop('checked', false);

                // Re-render both lists
                this.container.find('.available-columns-list').html(
                    this.render_available_columns(this.config.available_fields, this.config.columns)
                );
                this.container.find('.selected-columns-list').html(
                    this.render_selected_columns(this.config.columns)
                );
                this.update_selected_count();

                frappe.show_alert({
                    message: __('Column "{0}" removed', [column.label]),
                    indicator: 'orange'
                });
            }
        }

        update_selected_count() {
            const count = this.config.columns.filter(c => c.visible).length;
            this.container.find('.selected-count').text(`(${count})`);
        }

        save_configuration() {
            if (this.callbacks.onSave) {
                this.callbacks.onSave(this.config);
            }
        }

        reset_configuration() {
            if (this.callbacks.onReset) {
                this.callbacks.onReset();
            }
        }

        preview_configuration() {
            if (this.callbacks.onPreview) {
                this.callbacks.onPreview(this.config);
            }
        }
    };
};

// Enhanced Pagination Component - Task 9.1
column_management.components.EnhancedPagination = class EnhancedPagination {
    constructor(options) {
        this.container = options.container;
        this.doctype = options.doctype;
        this.callbacks = options.callbacks || {};

        // Pagination state
        this.currentPage = options.currentPage || 1;
        this.pageSize = options.pageSize || 20;
        this.totalRecords = options.totalRecords || 0;
        this.totalPages = Math.ceil(this.totalRecords / this.pageSize);

        // Configuration
        this.pageSizeOptions = options.pageSizeOptions || [10, 20, 50, 100, 200];
        this.maxVisiblePages = options.maxVisiblePages || 7;
        this.showPageSizeSelector = options.showPageSizeSelector !== false;
        this.showPageInfo = options.showPageInfo !== false;
        this.showJumpToPage = options.showJumpToPage !== false;

        // State persistence
        this.persistState = options.persistState !== false;
        this.storageKey = `pagination_${this.doctype}`;

        // Keyboard shortcuts
        this.enableKeyboardShortcuts = options.enableKeyboardShortcuts !== false;

        this.init();
    }

    init() {
        this.load_persisted_state();
        this.render();
        this.bind_events();
        this.setup_keyboard_shortcuts();
    }

    load_persisted_state() {
        if (!this.persistState) return;

        try {
            const saved = localStorage.getItem(this.storageKey);
            if (saved) {
                const state = JSON.parse(saved);
                this.pageSize = state.pageSize || this.pageSize;
                this.currentPage = Math.min(state.currentPage || 1, this.totalPages || 1);
            }
        } catch (e) {
            console.warn('Failed to load pagination state:', e);
        }
    }

    save_state() {
        if (!this.persistState) return;

        try {
            const state = {
                pageSize: this.pageSize,
                currentPage: this.currentPage,
                timestamp: Date.now()
            };
            localStorage.setItem(this.storageKey, JSON.stringify(state));
        } catch (e) {
            console.warn('Failed to save pagination state:', e);
        }
    }

    render() {
        this.totalPages = Math.ceil(this.totalRecords / this.pageSize);
        this.currentPage = Math.min(this.currentPage, this.totalPages || 1);

        let html = `
            <div class="enhanced-pagination">
                <div class="pagination-info">
                    ${this.render_page_info()}
                </div>
                <div class="pagination-controls">
                    ${this.render_navigation_controls()}
                    ${this.render_page_numbers()}
                    ${this.render_page_size_selector()}
                    ${this.render_jump_to_page()}
                </div>
            </div>
        `;

        this.container.html(html);
    }

    render_page_info() {
        if (!this.showPageInfo) return '';

        const startRecord = Math.max(1, (this.currentPage - 1) * this.pageSize + 1);
        const endRecord = Math.min(this.totalRecords, this.currentPage * this.pageSize);

        return `
            <div class="page-info">
                <span class="records-info">
                    ${__('Showing {0} to {1} of {2} entries', [
            frappe.format(startRecord, { fieldtype: 'Int' }),
            frappe.format(endRecord, { fieldtype: 'Int' }),
            frappe.format(this.totalRecords, { fieldtype: 'Int' })
        ])}
                </span>
                ${this.totalPages > 1 ? `
                    <span class="page-info-detail">
                        (${__('Page {0} of {1}', [this.currentPage, this.totalPages])})
                    </span>
                ` : ''}
            </div>
        `;
    }

    render_navigation_controls() {
        const isFirstPage = this.currentPage <= 1;
        const isLastPage = this.currentPage >= this.totalPages;

        return `
            <div class="nav-controls">
                <button class="btn btn-sm btn-default first-page" 
                        ${isFirstPage ? 'disabled' : ''} 
                        title="${__('First Page')} (Ctrl+Home)">
                    <i class="fa fa-angle-double-left"></i>
                </button>
                <button class="btn btn-sm btn-default prev-page" 
                        ${isFirstPage ? 'disabled' : ''} 
                        title="${__('Previous Page')} (Ctrl+Left)">
                    <i class="fa fa-angle-left"></i>
                </button>
                <button class="btn btn-sm btn-default next-page" 
                        ${isLastPage ? 'disabled' : ''} 
                        title="${__('Next Page')} (Ctrl+Right)">
                    <i class="fa fa-angle-right"></i>
                </button>
                <button class="btn btn-sm btn-default last-page" 
                        ${isLastPage ? 'disabled' : ''} 
                        title="${__('Last Page')} (Ctrl+End)">
                    <i class="fa fa-angle-double-right"></i>
                </button>
            </div>
        `;
    }

    render_page_numbers() {
        if (this.totalPages <= 1) return '';

        const pages = this.calculate_visible_pages();
        let html = '<div class="page-numbers">';

        pages.forEach(page => {
            if (page === '...') {
                html += '<span class="page-ellipsis">...</span>';
            } else {
                const isActive = page === this.currentPage;
                html += `
                    <button class="btn btn-sm ${isActive ? 'btn-primary' : 'btn-default'} page-number" 
                            data-page="${page}" 
                            ${isActive ? 'disabled' : ''}>
                        ${page}
                    </button>
                `;
            }
        });

        html += '</div>';
        return html;
    }

    calculate_visible_pages() {
        const pages = [];
        const totalPages = this.totalPages;
        const current = this.currentPage;
        const maxVisible = this.maxVisiblePages;

        if (totalPages <= maxVisible) {
            // Show all pages
            for (let i = 1; i <= totalPages; i++) {
                pages.push(i);
            }
        } else {
            // Always show first page
            pages.push(1);

            // Calculate range around current page
            const rangeStart = Math.max(2, current - Math.floor((maxVisible - 3) / 2));
            const rangeEnd = Math.min(totalPages - 1, rangeStart + maxVisible - 4);

            // Add ellipsis if needed
            if (rangeStart > 2) {
                pages.push('...');
            }

            // Add pages in range
            for (let i = rangeStart; i <= rangeEnd; i++) {
                pages.push(i);
            }

            // Add ellipsis if needed
            if (rangeEnd < totalPages - 1) {
                pages.push('...');
            }

            // Always show last page
            if (totalPages > 1) {
                pages.push(totalPages);
            }
        }

        return pages;
    }

    render_page_size_selector() {
        if (!this.showPageSizeSelector) return '';

        let options = '';
        this.pageSizeOptions.forEach(size => {
            const selected = size === this.pageSize ? 'selected' : '';
            options += `<option value="${size}" ${selected}>${size}</option>`;
        });

        return `
            <div class="page-size-selector">
                <label class="page-size-label">${__('Show')}:</label>
                <select class="form-control page-size-select">
                    ${options}
                </select>
                <span class="page-size-suffix">${__('entries')}</span>
            </div>
        `;
    }

    render_jump_to_page() {
        if (!this.showJumpToPage || this.totalPages <= 1) return '';

        return `
            <div class="jump-to-page">
                <label class="jump-label">${__('Go to')}:</label>
                <input type="number" class="form-control jump-input" 
                       min="1" max="${this.totalPages}" 
                       value="${this.currentPage}"
                       placeholder="${__('Page')}"
                       title="${__('Jump to page')}">
                <button class="btn btn-sm btn-default jump-button" title="${__('Go')}">
                    <i class="fa fa-arrow-right"></i>
                </button>
            </div>
        `;
    }

    bind_events() {
        const self = this;

        // Navigation controls
        this.container.on('click', '.first-page', () => this.go_to_page(1));
        this.container.on('click', '.prev-page', () => this.go_to_page(this.currentPage - 1));
        this.container.on('click', '.next-page', () => this.go_to_page(this.currentPage + 1));
        this.container.on('click', '.last-page', () => this.go_to_page(this.totalPages));

        // Page numbers
        this.container.on('click', '.page-number', function () {
            const page = parseInt($(this).data('page'));
            self.go_to_page(page);
        });

        // Page size selector
        this.container.on('change', '.page-size-select', function () {
            const newPageSize = parseInt($(this).val());
            self.change_page_size(newPageSize);
        });

        // Jump to page
        this.container.on('click', '.jump-button', function () {
            const page = parseInt(self.container.find('.jump-input').val());
            if (page >= 1 && page <= self.totalPages) {
                self.go_to_page(page);
            }
        });

        this.container.on('keypress', '.jump-input', function (e) {
            if (e.which === 13) { // Enter key
                const page = parseInt($(this).val());
                if (page >= 1 && page <= self.totalPages) {
                    self.go_to_page(page);
                }
            }
        });

        // Input validation for jump to page
        this.container.on('input', '.jump-input', function () {
            const value = parseInt($(this).val());
            const $button = self.container.find('.jump-button');

            if (isNaN(value) || value < 1 || value > self.totalPages) {
                $button.prop('disabled', true);
                $(this).addClass('has-error');
            } else {
                $button.prop('disabled', false);
                $(this).removeClass('has-error');
            }
        });
    }

    setup_keyboard_shortcuts() {
        if (!this.enableKeyboardShortcuts) return;

        const self = this;

        $(document).on('keydown.pagination', function (e) {
            // Only handle shortcuts when pagination container is visible
            if (!self.container.is(':visible')) return;

            // Check if user is typing in an input field
            if ($(e.target).is('input, textarea, select')) return;

            if (e.ctrlKey) {
                switch (e.which) {
                    case 36: // Ctrl+Home - First page
                        e.preventDefault();
                        self.go_to_page(1);
                        break;
                    case 35: // Ctrl+End - Last page
                        e.preventDefault();
                        self.go_to_page(self.totalPages);
                        break;
                    case 37: // Ctrl+Left - Previous page
                        e.preventDefault();
                        if (self.currentPage > 1) {
                            self.go_to_page(self.currentPage - 1);
                        }
                        break;
                    case 39: // Ctrl+Right - Next page
                        e.preventDefault();
                        if (self.currentPage < self.totalPages) {
                            self.go_to_page(self.currentPage + 1);
                        }
                        break;
                }
            }
        });
    }

    go_to_page(page) {
        if (page < 1 || page > this.totalPages || page === this.currentPage) {
            return;
        }

        this.currentPage = page;
        this.save_state();
        this.render();

        // Trigger callback
        if (this.callbacks.onPageChange) {
            this.callbacks.onPageChange({
                page: this.currentPage,
                pageSize: this.pageSize,
                totalPages: this.totalPages,
                totalRecords: this.totalRecords
            });
        }

        // Show loading indicator
        this.show_loading();
    }

    change_page_size(newPageSize) {
        if (newPageSize === this.pageSize) return;

        // Calculate new current page to maintain position
        const currentRecord = (this.currentPage - 1) * this.pageSize + 1;
        const newCurrentPage = Math.ceil(currentRecord / newPageSize);

        this.pageSize = newPageSize;
        this.currentPage = newCurrentPage;
        this.totalPages = Math.ceil(this.totalRecords / this.pageSize);

        this.save_state();
        this.render();

        // Trigger callback
        if (this.callbacks.onPageSizeChange) {
            this.callbacks.onPageSizeChange({
                page: this.currentPage,
                pageSize: this.pageSize,
                totalPages: this.totalPages,
                totalRecords: this.totalRecords
            });
        }

        // Show loading indicator
        this.show_loading();
    }

    update_total_records(totalRecords) {
        this.totalRecords = totalRecords;
        this.totalPages = Math.ceil(this.totalRecords / this.pageSize);

        // Adjust current page if necessary
        if (this.currentPage > this.totalPages && this.totalPages > 0) {
            this.currentPage = this.totalPages;
        }

        this.render();
    }

    show_loading() {
        this.container.find('.pagination-controls').addClass('loading');

        // Add loading overlay
        if (!this.container.find('.pagination-loading').length) {
            this.container.append(`
                <div class="pagination-loading">
                    <i class="fa fa-spinner fa-spin"></i>
                    ${__('Loading...')}
                </div>
            `);
        }
    }

    hide_loading() {
        this.container.find('.pagination-controls').removeClass('loading');
        this.container.find('.pagination-loading').remove();
    }

    reset_to_first_page() {
        if (this.currentPage !== 1) {
            this.go_to_page(1);
        }
    }

    get_current_state() {
        return {
            page: this.currentPage,
            pageSize: this.pageSize,
            totalPages: this.totalPages,
            totalRecords: this.totalRecords
        };
    }

    destroy() {
        // Remove keyboard shortcuts
        $(document).off('keydown.pagination');

        // Clear container
        this.container.empty();
    }
};

// StatisticsDashboard Component - Clean Implementation
column_management.components.StatisticsDashboard = class StatisticsDashboard {
    constructor(options) {
        this.doctype = options.doctype;
        this.container = options.container;
        this.data = options.data || [];
        this.activeFilters = options.activeFilters || [];
        this.statisticsConfig = options.statisticsConfig || [];
        this.callbacks = options.callbacks || {};
        this.refreshInterval = options.refreshInterval || 30000; // 30 seconds
        this.autoRefresh = options.autoRefresh !== false;

        // State
        this.statistics = {};
        this.isLoading = false;
        this.refreshTimer = null;
        this.tooltip = null;

        this.init();
    }

    init() {
        this.render();
        this.bind_events();
        this.load_statistics();

        if (this.autoRefresh) {
            this.start_auto_refresh();
        }
    }

    render() {
        let html = `
            <div class="statistics-dashboard">
                <div class="dashboard-header">
                    <h5 class="dashboard-title">
                        <i class="fa fa-bar-chart"></i> ${__('Statistics')}
                    </h5>
                    <div class="dashboard-controls">
                        <button class="btn btn-xs btn-default refresh-stats" title="${__('Refresh Statistics')}">
                            <i class="fa fa-refresh"></i>
                        </button>
                        <button class="btn btn-xs btn-default toggle-auto-refresh ${this.autoRefresh ? 'active' : ''}" 
                                title="${__('Toggle Auto Refresh')}">
                            <i class="fa fa-clock-o"></i>
                        </button>
                        <button class="btn btn-xs btn-default configure-stats" title="${__('Configure Statistics')}">
                            <i class="fa fa-cog"></i>
                        </button>
                    </div>
                </div>
                <div class="dashboard-content">
                    <div class="statistics-grid">
                        ${this.render_statistics()}
                    </div>
                </div>
            </div>
        `;

        this.container.html(html);
        this.create_tooltip();
    }

    render_statistics() {
        if (this.isLoading) {
            return `
                <div class="loading-overlay">
                    <i class="fa fa-spinner fa-spin"></i>
                    ${__('Loading statistics...')}
                </div>
            `;
        }

        if (Object.keys(this.statistics).length === 0) {
            return `
                <div class="empty-statistics">
                    <i class="fa fa-bar-chart"></i>
                    <p>${__('No statistics available')}</p>
                    <small>${__('Configure statistics to see data insights')}</small>
                </div>
            `;
        }

        let html = '';
        Object.keys(this.statistics).forEach(key => {
            const stat = this.statistics[key];
            html += this.render_statistic_card(stat);
        });

        return html;
    }

    render_statistic_card(stat) {
        const trend = this.calculate_trend(stat);
        const trendClass = trend > 0 ? 'text-success' : trend < 0 ? 'text-danger' : 'text-muted';
        const trendIcon = trend > 0 ? 'fa-arrow-up' : trend < 0 ? 'fa-arrow-down' : 'fa-minus';

        return `
            <div class="statistic-card" data-statistic="${stat.name}" data-field="${stat.field}">
                <div class="statistic-header">
                    <div class="statistic-label">${stat.label || stat.name}</div>
                    ${trend !== null ? `
                        <div class="trend-indicator ${trendClass}">
                            <i class="fa ${trendIcon}"></i>
                            ${Math.abs(trend).toFixed(1)}%
                        </div>
                    ` : ''}
                </div>
                <div class="statistic-value ${this.get_value_class(stat.type)}">
                    ${this.format_statistic_value(stat.value, stat.format, stat.type)}
                </div>
                ${stat.subtitle ? `<div class="statistic-subtitle">${stat.subtitle}</div>` : ''}
                <div class="statistic-breakdown-indicator">
                    <i class="fa fa-info-circle"></i>
                    ${__('Click for details')}
                </div>
            </div>
        `;
    }

    get_value_class(type) {
        const classMap = {
            'count': 'count',
            'sum': 'currency',
            'avg': 'number',
            'min': 'number',
            'max': 'number',
            'percentage': 'percentage'
        };
        return classMap[type] || 'number';
    }

    format_statistic_value(value, format, type) {
        if (value === null || value === undefined) {
            return '-';
        }

        // Apply custom format if provided
        if (format) {
            try {
                return format.replace('{value}', this.format_number(value, type));
            } catch (e) {
                console.warn('Invalid format string:', format);
            }
        }

        return this.format_number(value, type);
    }

    format_number(value, type) {
        if (typeof value !== 'number') {
            return value;
        }

        switch (type) {
            case 'count':
                return value.toLocaleString();
            case 'sum':
                return frappe.format(value, { fieldtype: 'Currency' });
            case 'avg':
            case 'min':
            case 'max':
                return value.toFixed(2);
            case 'percentage':
                return (value * 100).toFixed(1) + '%';
            default:
                return value.toLocaleString();
        }
    }

    calculate_trend(stat) {
        if (!stat.previous_value || stat.previous_value === 0) {
            return null;
        }

        const current = parseFloat(stat.value) || 0;
        const previous = parseFloat(stat.previous_value) || 0;

        if (previous === 0) return null;

        return ((current - previous) / previous) * 100;
    }

    bind_events() {
        const self = this;

        // Refresh button
        this.container.on('click', '.refresh-stats', function () {
            self.refresh_statistics();
        });

        // Auto refresh toggle
        this.container.on('click', '.toggle-auto-refresh', function () {
            self.toggle_auto_refresh();
        });

        // Configure statistics
        this.container.on('click', '.configure-stats', function () {
            self.show_configuration_dialog();
        });

        // Statistic card click for drill-down
        this.container.on('click', '.statistic-card', function () {
            const statisticName = $(this).data('statistic');
            const field = $(this).data('field');
            self.show_statistic_details(statisticName, field);
        });

        // Hover events for tooltips
        this.container.on('mouseenter', '.statistic-card', function (e) {
            self.show_tooltip(e, $(this));
        });

        this.container.on('mouseleave', '.statistic-card', function () {
            self.hide_tooltip();
        });

        this.container.on('mousemove', '.statistic-card', function (e) {
            self.update_tooltip_position(e);
        });
    }

    load_statistics() {
        this.isLoading = true;
        this.render();

        frappe.call({
            method: 'column_management.api.statistics.get_statistics',
            args: {
                doctype: this.doctype,
                filters: this.activeFilters,
                statistics_config: this.statisticsConfig
            },
            callback: (r) => {
                this.isLoading = false;

                if (r.message && r.message.success) {
                    this.statistics = r.message.data;
                    this.render();

                    if (this.callbacks.onStatisticsLoaded) {
                        this.callbacks.onStatisticsLoaded(this.statistics);
                    }
                } else {
                    this.show_error(r.message?.message || __('Failed to load statistics'));
                }
            },
            error: () => {
                this.isLoading = false;
                this.show_error(__('Network error while loading statistics'));
            }
        });
    }

    refresh_statistics() {
        const $btn = this.container.find('.refresh-stats');
        $btn.addClass('loading');

        this.load_statistics();

        // Remove loading state after a minimum time for visual feedback
        setTimeout(() => {
            $btn.removeClass('loading');
        }, 1000);
    }

    toggle_auto_refresh() {
        this.autoRefresh = !this.autoRefresh;

        const $btn = this.container.find('.toggle-auto-refresh');
        $btn.toggleClass('active', this.autoRefresh);

        if (this.autoRefresh) {
            this.start_auto_refresh();
        } else {
            this.stop_auto_refresh();
        }
    }

    start_auto_refresh() {
        this.stop_auto_refresh(); // Clear any existing timer

        this.refreshTimer = setInterval(() => {
            this.load_statistics();
        }, this.refreshInterval);
    }

    stop_auto_refresh() {
        if (this.refreshTimer) {
            clearInterval(this.refreshTimer);
            this.refreshTimer = null;
        }
    }

    show_error(message) {
        const html = `
            <div class="statistics-error">
                <i class="fa fa-exclamation-triangle"></i>
                <p>${message}</p>
                <button class="btn btn-sm btn-default retry-load">
                    ${__('Retry')}
                </button>
            </div>
        `;

        this.container.find('.statistics-grid').html(html);

        // Bind retry button
        this.container.find('.retry-load').on('click', () => {
            this.load_statistics();
        });
    }

    create_tooltip() {
        if (this.tooltip) {
            this.tooltip.remove();
        }

        this.tooltip = $(`
            <div class="statistics-tooltip">
                <div class="tooltip-content">
                    <h6 class="tooltip-title"></h6>
                    <div class="tooltip-details"></div>
                </div>
            </div>
        `).appendTo('body');
    }

    show_tooltip(event, $card) {
        const statisticName = $card.data('statistic');
        const stat = this.statistics[statisticName];

        if (!stat) return;

        const title = stat.label || stat.name;
        const details = this.get_tooltip_details(stat);

        this.tooltip.find('.tooltip-title').text(title);
        this.tooltip.find('.tooltip-details').html(details);

        this.update_tooltip_position(event);
        this.tooltip.show();
    }

    hide_tooltip() {
        if (this.tooltip) {
            this.tooltip.hide();
        }
    }

    update_tooltip_position(event) {
        if (!this.tooltip || !this.tooltip.is(':visible')) return;

        const tooltipWidth = this.tooltip.outerWidth();
        const tooltipHeight = this.tooltip.outerHeight();
        const windowWidth = $(window).width();

        let left = event.pageX + 10;
        let top = event.pageY - tooltipHeight - 10;

        // Adjust if tooltip goes off screen
        if (left + tooltipWidth > windowWidth) {
            left = event.pageX - tooltipWidth - 10;
        }

        if (top < $(window).scrollTop()) {
            top = event.pageY + 10;
        }

        this.tooltip.css({
            left: left + 'px',
            top: top + 'px'
        });
    }

    get_tooltip_details(stat) {
        let details = `
            <p><small>${__('Type')}:</small> ${stat.type.toUpperCase()}</p>
            <p><small>${__('Field')}:</small> ${stat.field}</p>
            <p><small>${__('Current Value')}:</small> ${this.format_statistic_value(stat.value, stat.format, stat.type)}</p>
        `;

        if (stat.previous_value !== null && stat.previous_value !== undefined) {
            details += `<p><small>${__('Previous Value')}:</small> ${this.format_statistic_value(stat.previous_value, stat.format, stat.type)}</p>`;
        }

        if (stat.condition) {
            details += `<p><small>${__('Condition')}:</small> ${stat.condition}</p>`;
        }

        if (this.activeFilters.length > 0) {
            details += `<p><small>${__('Active Filters')}:</small> ${this.activeFilters.length}</p>`;
        }

        details += `<p><small>${__('Last Updated')}:</small> ${frappe.datetime.now_datetime()}</p>`;

        return details;
    }

    show_statistic_details(statisticName, field) {
        const stat = this.statistics[statisticName];
        if (!stat) return;

        const dialog = new frappe.ui.Dialog({
            title: __('Statistics Details: {0}', [stat.label || stat.name]),
            fields: [
                {
                    fieldtype: 'HTML',
                    fieldname: 'details_html',
                    options: '<div id="statistic-details-container">Loading...</div>'
                }
            ],
            size: 'large'
        });

        dialog.show();

        // Load detailed breakdown
        frappe.call({
            method: 'column_management.api.statistics.get_statistic_details',
            args: {
                doctype: this.doctype,
                statistic_name: statisticName,
                field: field,
                filters: this.activeFilters
            },
            callback: (r) => {
                if (r.message && r.message.success) {
                    this.render_statistic_details(r.message.data, dialog);
                } else {
                    dialog.$wrapper.find('#statistic-details-container').html(
                        '<div class="text-muted">Unable to load detailed statistics</div>'
                    );
                }
            }
        });

        if (this.callbacks.onStatisticClick) {
            this.callbacks.onStatisticClick(statisticName, field, stat);
        }
    }

    render_statistic_details(details, dialog) {
        const container = dialog.$wrapper.find('#statistic-details-container');

        let html = `
            <div class="statistic-details">
                <div class="detail-summary">
                    <div class="row">
                        <div class="col-md-6">
                            <h6>${__('Current Period')}</h6>
                            <div class="current-value">${this.format_statistic_value(details.current_value, details.format, details.type)}</div>
                        </div>
                        <div class="col-md-6">
                            <h6>${__('Previous Period')}</h6>
                            <div class="previous-value">${this.format_statistic_value(details.previous_value, details.format, details.type)}</div>
                        </div>
                    </div>
                </div>
        `;

        if (details.breakdown && details.breakdown.length > 0) {
            html += `
                <div class="detail-breakdown">
                    <h6>${__('Breakdown')}</h6>
                    <div class="breakdown-table">
                        <table class="table table-bordered">
                            <thead>
                                <tr>
                                    <th>${__('Category')}</th>
                                    <th>${__('Value')}</th>
                                    <th>${__('Percentage')}</th>
                                </tr>
                            </thead>
                            <tbody>
            `;

            details.breakdown.forEach(item => {
                const percentage = details.total > 0 ? ((item.value / details.total) * 100).toFixed(1) : 0;
                html += `
                    <tr>
                        <td>${item.category}</td>
                        <td>${this.format_statistic_value(item.value, details.format, details.type)}</td>
                        <td>${percentage}%</td>
                    </tr>
                `;
            });

            html += `
                            </tbody>
                        </table>
                    </div>
                </div>
            `;
        }

        html += '</div>';
        container.html(html);
    }

    show_configuration_dialog() {
        const dialog = new frappe.ui.Dialog({
            title: __('Configure Statistics'),
            fields: [
                {
                    fieldtype: 'HTML',
                    fieldname: 'config_html',
                    options: '<div id="statistics-config-container">Loading...</div>'
                }
            ],
            size: 'large',
            primary_action_label: __('Save Configuration'),
            primary_action: (values) => {
                this.save_statistics_configuration(dialog);
            }
        });

        dialog.show();

        // Load current configuration
        frappe.call({
            method: 'column_management.api.statistics.get_statistics_config',
            args: {
                doctype: this.doctype
            },
            callback: (r) => {
                if (r.message && r.message.success) {
                    this.render_statistics_configuration(r.message.data, dialog);
                } else {
                    dialog.$wrapper.find('#statistics-config-container').html(
                        '<div class="text-muted">Unable to load configuration</div>'
                    );
                }
            }
        });
    }

    render_statistics_configuration(config, dialog) {
        const container = dialog.$wrapper.find('#statistics-config-container');

        let html = `
            <div class="statistics-configuration">
                <div class="config-header">
                    <h6>${__('Statistics Configuration')}</h6>
                    <button class="btn btn-sm btn-primary add-statistic">
                        <i class="fa fa-plus"></i> ${__('Add Statistic')}
                    </button>
                </div>
                <div class="config-list">
        `;

        if (config.length === 0) {
            html += `
                <div class="empty-config">
                    <p>${__('No statistics configured')}</p>
                    <small>${__('Click "Add Statistic" to create your first statistic')}</small>
                </div>
            `;
        } else {
            config.forEach((stat, index) => {
                html += this.render_config_item(stat, index);
            });
        }

        html += `
                </div>
            </div>
        `;

        container.html(html);

        // Bind events for configuration
        this.bind_configuration_events(container, dialog);
    }

    render_config_item(stat, index) {
        return `
            <div class="config-item" data-index="${index}">
                <div class="config-item-header">
                    <div class="config-name">
                        <input type="text" class="form-control stat-name" value="${stat.name}" placeholder="${__('Statistic Name')}" />
                    </div>
                    <div class="config-actions">
                        <button class="btn btn-xs btn-danger remove-config">
                            <i class="fa fa-trash"></i>
                        </button>
                    </div>
                </div>
                <div class="config-item-body">
                    <div class="row">
                        <div class="col-md-4">
                            <label>${__('Field')}</label>
                            <select class="form-control stat-field">
                                <option value="">${__('Select Field')}</option>
                                ${this.get_field_options(stat.field)}
                            </select>
                        </div>
                        <div class="col-md-4">
                            <label>${__('Type')}</label>
                            <select class="form-control stat-type">
                                <option value="count" ${stat.type === 'count' ? 'selected' : ''}>${__('Count')}</option>
                                <option value="sum" ${stat.type === 'sum' ? 'selected' : ''}>${__('Sum')}</option>
                                <option value="avg" ${stat.type === 'avg' ? 'selected' : ''}>${__('Average')}</option>
                                <option value="min" ${stat.type === 'min' ? 'selected' : ''}>${__('Minimum')}</option>
                                <option value="max" ${stat.type === 'max' ? 'selected' : ''}>${__('Maximum')}</option>
                            </select>
                        </div>
                        <div class="col-md-4">
                            <label>${__('Format')}</label>
                            <input type="text" class="form-control stat-format" value="${stat.format || ''}" 
                                   placeholder="${__('e.g., {value} items')}" />
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    get_field_options(selectedField) {
        // This would typically come from the doctype metadata
        // For now, return common field types
        const commonFields = [
            'name', 'creation', 'modified', 'owner', 'modified_by',
            'status', 'docstatus', 'idx'
        ];

        return commonFields.map(field =>
            `<option value="${field}" ${field === selectedField ? 'selected' : ''}>${field}</option>`
        ).join('');
    }

    bind_configuration_events(container, dialog) {
        const self = this;

        // Add new statistic
        container.find('.add-statistic').on('click', function () {
            const newStat = {
                name: '',
                field: '',
                type: 'count',
                format: ''
            };

            const newIndex = container.find('.config-item').length;
            const newItemHtml = self.render_config_item(newStat, newIndex);

            container.find('.config-list').append(newItemHtml);
        });

        // Remove statistic
        container.on('click', '.remove-config', function () {
            $(this).closest('.config-item').remove();
        });
    }

    save_statistics_configuration(dialog) {
        const config = [];

        dialog.$wrapper.find('.config-item').each(function () {
            const $item = $(this);

            const stat = {
                name: $item.find('.stat-name').val(),
                field: $item.find('.stat-field').val(),
                type: $item.find('.stat-type').val(),
                format: $item.find('.stat-format').val()
            };

            if (stat.name && stat.field) {
                config.push(stat);
            }
        });

        frappe.call({
            method: 'column_management.api.statistics.save_statistics_config',
            args: {
                doctype: this.doctype,
                config: config
            },
            callback: (r) => {
                if (r.message && r.message.success) {
                    frappe.show_alert(__('Statistics configuration saved'));
                    this.statisticsConfig = config;
                    this.load_statistics();
                    dialog.hide();
                } else {
                    frappe.msgprint(__('Error saving configuration: {0}', [r.message?.message || 'Unknown error']));
                }
            }
        });
    }

    update_data(newData) {
        this.data = newData;
        this.load_statistics();
    }

    update_filters(newFilters) {
        this.activeFilters = newFilters;
        this.load_statistics();
    }

    destroy() {
        this.stop_auto_refresh();

        if (this.tooltip) {
            this.tooltip.remove();
        }

        this.container.empty();
    }
};

// Initialize enhanced list view integration
column_management.init_enhanced_list_integration = function () {
    // Add statistics dashboard to list views
    if (cur_list && cur_list.doctype) {
        column_management.add_statistics_dashboard(cur_list);
    }

    // Listen for list view changes
    $(document).on('list_view_loaded', function (e, list_view) {
        column_management.add_statistics_dashboard(list_view);
    });
};

column_management.add_statistics_dashboard = function (list_view) {
    // Check if statistics dashboard already exists
    if (list_view.$page.find('.statistics-dashboard').length) {
        return;
    }

    // Create container for statistics dashboard
    const dashboard_container = $('<div class="statistics-dashboard-container"></div>');

    // Insert before the list container
    const list_container = list_view.$page.find('.layout-main-section');
    if (list_container.length) {
        dashboard_container.insertBefore(list_container);
    } else {
        list_view.$page.find('.page-content').prepend(dashboard_container);
    }

    // Initialize StatisticsDashboard component
    const statisticsDashboard = new column_management.components.StatisticsDashboard({
        doctype: list_view.doctype,
        container: dashboard_container,
        data: list_view.data || [],
        activeFilters: list_view.filter_area ? list_view.filter_area.get() : [],
        callbacks: {
            onStatisticsLoaded: function (statistics) {
                console.log('Statistics loaded:', statistics);
            },
            onStatisticClick: function (statisticName, field, stat) {
                // Handle drill-down functionality
                column_management.handle_statistic_drill_down(list_view, statisticName, field, stat);
            }
        }
    });

    // Store reference for later use
    list_view.statistics_dashboard = statisticsDashboard;

    // Update statistics when filters change
    if (list_view.filter_area) {
        list_view.filter_area.on('change', function () {
            const filters = list_view.filter_area.get();
            statisticsDashboard.update_filters(filters);
        });
    }

    // Update statistics when data changes
    const original_refresh = list_view.refresh;
    list_view.refresh = function () {
        original_refresh.call(this);
        if (this.statistics_dashboard) {
            this.statistics_dashboard.update_data(this.data || []);
        }
    };
};

column_management.handle_statistic_drill_down = function (list_view, statisticName, field, stat) {
    // Apply filter based on the statistic clicked
    if (field && list_view.filter_area) {
        // If we have a condition in the statistic, apply it as a filter
        if (stat.condition) {
            try {
                // Parse the condition and apply as filter
                // This is a simplified implementation
                const condition_parts = stat.condition.split('=');
                if (condition_parts.length === 2) {
                    const filter_field = condition_parts[0].trim();
                    const filter_val = condition_parts[1].trim().replace(/['"]/g, '');

                    list_view.filter_area.add(list_view.doctype, filter_field, '=', filter_val);
                }
            } catch (e) {
                console.warn('Could not parse condition:', stat.condition);
            }
        }
    }
};

// Utility function to show statistics dashboard in any container
column_management.show_statistics_dashboard = function (options) {
    const dashboard = new column_management.components.StatisticsDashboard(options);
    return dashboard;
};

// Callback functions for ColumnManagerComponent
column_management.save_column_config_new = function (doctype, config, dialog) {
    frappe.call({
        method: 'column_management.api.column_manager.save_column_config',
        args: {
            doctype: doctype,
            config: config
        },
        callback: function (r) {
            if (r.message && r.message.success) {
                frappe.show_alert(__('Column configuration saved'));
                dialog.hide();
                // Refresh list view
                if (cur_list) {
                    cur_list.refresh();
                }
            } else {
                frappe.msgprint(__('Error saving configuration: {0}', [r.message.message || 'Unknown error']));
            }
        }
    });
};

column_management.reset_column_config_new = function (doctype, dialog) {
    frappe.confirm(__('Reset column configuration to default?'), function () {
        frappe.call({
            method: 'column_management.api.column_manager.reset_column_config',
            args: {
                doctype: doctype
            },
            callback: function (r) {
                if (r.message && r.message.success) {
                    frappe.show_alert(__('Column configuration reset'));

                    // Update the component with new config
                    const container = dialog.$wrapper.find('#column-manager-container');
                    const columnManager = new column_management.components.ColumnManager({
                        doctype: doctype,
                        container: container,
                        config: r.message.data,
                        callbacks: {
                            onSave: function (config) {
                                column_management.save_column_config_new(doctype, config, dialog);
                            },
                            onReset: function () {
                                column_management.reset_column_config_new(doctype, dialog);
                            },
                            onPreview: function (config) {
                                column_management.preview_column_config(doctype, config);
                            }
                        }
                    });
                } else {
                    frappe.msgprint(__('Error resetting configuration: {0}', [r.message.message || 'Unknown error']));
                }
            }
        });
    });
};

column_management.preview_column_config = function (doctype, config) {
    // Create preview dialog
    const preview_dialog = new frappe.ui.Dialog({
        title: __('Preview: {0}', [doctype]),
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'preview_html',
                options: '<div id="column-preview-container">Loading preview...</div>'
            }
        ],
        size: 'extra-large'
    });

    preview_dialog.show();

    // Get sample data for preview
    frappe.call({
        method: 'column_management.api.enhanced_list.get_list_data',
        args: {
            doctype: doctype,
            columns: config.columns.filter(c => c.visible),
            page: 1,
            page_size: 10
        },
        callback: function (r) {
            if (r.message && r.message.success) {
                column_management.render_preview(r.message.data, preview_dialog);
            } else {
                preview_dialog.$wrapper.find('#column-preview-container').html(
                    '<div class="text-muted">Unable to load preview data</div>'
                );
            }
        }
    });
};

column_management.render_preview = function (data, dialog) {
    const container = dialog.$wrapper.find('#column-preview-container');
    const records = data.records || [];
    const columns = data.columns || [];

    if (records.length === 0) {
        container.html('<div class="text-muted">No data available for preview</div>');
        return;
    }

    let html = `
        <div class="preview-table-container">
            <table class="table table-bordered">
                <thead>
                    <tr>
    `;

    // Render headers
    columns.forEach(column => {
        const pinned_class = column.pinned ? `pinned-${column.pinned}` : '';
        html += `<th class="${pinned_class}" style="width: ${column.width}px">${column.label}</th>`;
    });

    html += `
                    </tr>
                </thead>
                <tbody>
    `;

    // Render data rows
    records.forEach(record => {
        html += '<tr>';
        columns.forEach(column => {
            const value = record[column.fieldname] || '';
            const pinned_class = column.pinned ? `pinned-${column.pinned}` : '';
            html += `<td class="${pinned_class}" style="width: ${column.width}px">${value}</td>`;
        });
        html += '</tr>';
    });

    html += `
                </tbody>
            </table>
        </div>
        <div class="preview-info">
            <small class="text-muted">
                Showing ${records.length} sample records with ${columns.length} columns
            </small>
        </div>
    `;

    container.html(html);
};
// Width persistence and restoration functions
column_management.save_column_width = function (doctype, fieldname, width) {
    return new Promise((resolve, reject) => {
        frappe.call({
            method: 'column_management.api.column_manager.save_column_width',
            args: {
                doctype: doctype,
                fieldname: fieldname,
                width: width
            },
            callback: function (r) {
                if (r.message && r.message.success) {
                    resolve(r.message.data);
                } else {
                    reject(r.message?.message || 'Failed to save column width');
                }
            },
            error: function (err) {
                reject(err.message || 'Network error while saving column width');
            }
        });
    });
};

column_management.save_multiple_column_widths = function (doctype, width_data) {
    return new Promise((resolve, reject) => {
        frappe.call({
            method: 'column_management.api.column_manager.save_multiple_column_widths',
            args: {
                doctype: doctype,
                width_data: width_data
            },
            callback: function (r) {
                if (r.message && r.message.success) {
                    resolve(r.message.data);
                } else {
                    reject(r.message?.message || 'Failed to save column widths');
                }
            },
            error: function (err) {
                reject(err.message || 'Network error while saving column widths');
            }
        });
    });
};

column_management.get_column_width = function (doctype, fieldname) {
    return new Promise((resolve, reject) => {
        frappe.call({
            method: 'column_management.api.column_manager.get_column_width',
            args: {
                doctype: doctype,
                fieldname: fieldname
            },
            callback: function (r) {
                if (r.message && r.message.success) {
                    resolve(r.message.data.width);
                } else {
                    reject(r.message?.message || 'Failed to get column width');
                }
            },
            error: function (err) {
                reject(err.message || 'Network error while getting column width');
            }
        });
    });
};

column_management.get_all_column_widths = function (doctype) {
    return new Promise((resolve, reject) => {
        frappe.call({
            method: 'column_management.api.column_manager.get_all_column_widths',
            args: {
                doctype: doctype
            },
            callback: function (r) {
                if (r.message && r.message.success) {
                    resolve(r.message.data.column_widths);
                } else {
                    reject(r.message?.message || 'Failed to get column widths');
                }
            },
            error: function (err) {
                reject(err.message || 'Network error while getting column widths');
            }
        });
    });
};

column_management.restore_column_widths = function (doctype) {
    return new Promise((resolve, reject) => {
        frappe.call({
            method: 'column_management.api.column_manager.restore_column_widths',
            args: {
                doctype: doctype
            },
            callback: function (r) {
                if (r.message && r.message.success) {
                    resolve(r.message.data.column_widths);
                } else {
                    reject(r.message?.message || 'Failed to restore column widths');
                }
            },
            error: function (err) {
                reject(err.message || 'Network error while restoring column widths');
            }
        });
    });
};

column_management.calculate_default_width = function (doctype, fieldname) {
    return new Promise((resolve, reject) => {
        frappe.call({
            method: 'column_management.api.column_manager.calculate_default_width',
            args: {
                doctype: doctype,
                fieldname: fieldname
            },
            callback: function (r) {
                if (r.message && r.message.success) {
                    resolve(r.message.data.default_width);
                } else {
                    reject(r.message?.message || 'Failed to calculate default width');
                }
            },
            error: function (err) {
                reject(err.message || 'Network error while calculating default width');
            }
        });
    });
};

// Enhanced list view integration with width persistence
column_management.init_enhanced_list_integration = function () {
    // Override list view rendering to include width restoration
    if (frappe.views && frappe.views.ListView) {
        const original_render = frappe.views.ListView.prototype.render;

        frappe.views.ListView.prototype.render = function () {
            const result = original_render.call(this);

            // Restore column widths after rendering
            if (this.doctype) {
                column_management.restore_and_apply_column_widths(this.doctype, this);
            }

            return result;
        };
    }
};

column_management.restore_and_apply_column_widths = function (doctype, list_view) {
    // Restore column widths and apply them to the list view
    column_management.restore_column_widths(doctype)
        .then(width_data => {
            if (width_data && Object.keys(width_data).length > 0) {
                column_management.apply_column_widths_to_list(list_view, width_data);
            }
        })
        .catch(err => {
            console.warn('Failed to restore column widths:', err);
        });
};

column_management.apply_column_widths_to_list = function (list_view, width_data) {
    // Apply width data to the actual list view columns
    if (!list_view.$result || !width_data) return;

    const $headers = list_view.$result.find('.list-row-head .list-row-col');

    $headers.each(function (index, header) {
        const $header = $(header);
        const fieldname = $header.data('fieldname') || $header.attr('data-fieldname');

        if (fieldname && width_data[fieldname]) {
            const width = width_data[fieldname];
            $header.css('width', width + 'px');
            $header.css('min-width', width + 'px');
            $header.css('max-width', width + 'px');
        }
    });

    // Also apply to data rows
    const $rows = list_view.$result.find('.list-row:not(.list-row-head) .list-row-col');

    $rows.each(function (index, cell) {
        const $cell = $(cell);
        const fieldname = $cell.data('fieldname') || $cell.attr('data-fieldname');

        if (fieldname && width_data[fieldname]) {
            const width = width_data[fieldname];
            $cell.css('width', width + 'px');
            $cell.css('min-width', width + 'px');
            $cell.css('max-width', width + 'px');
        }
    });
};

// Column resize functionality with persistence
column_management.init_column_resize_handlers = function (list_view) {
    if (!list_view || !list_view.$result) return;

    const $headers = list_view.$result.find('.list-row-head .list-row-col');

    $headers.each(function (index, header) {
        const $header = $(header);
        const fieldname = $header.data('fieldname') || $header.attr('data-fieldname');

        if (!fieldname) return;

        // Add resize handle
        const $resizeHandle = $('<div class="column-resize-handle"></div>');
        $header.append($resizeHandle);

        // Make header resizable
        $header.resizable({
            handles: 'e',
            minWidth: 50,
            maxWidth: 1000,
            resize: function (event, ui) {
                const newWidth = ui.size.width;

                // Apply width to corresponding data cells
                const $dataCells = list_view.$result.find(`.list-row:not(.list-row-head) .list-row-col[data-fieldname="${fieldname}"]`);
                $dataCells.css('width', newWidth + 'px');
            },
            stop: function (event, ui) {
                const newWidth = ui.size.width;

                // Save the new width
                column_management.save_column_width(list_view.doctype, fieldname, newWidth)
                    .then(() => {
                        frappe.show_alert({
                            message: __('Column width saved'),
                            indicator: 'green'
                        });
                    })
                    .catch(err => {
                        console.error('Failed to save column width:', err);
                        frappe.show_alert({
                            message: __('Failed to save column width'),
                            indicator: 'red'
                        });
                    });
            }
        });

        // Add double-click auto-resize
        $header.on('dblclick', function () {
            column_management.auto_resize_column(list_view, fieldname, $header);
        });
    });
};

column_management.auto_resize_column = function (list_view, fieldname, $header) {
    // Calculate optimal width based on content
    let maxWidth = 80; // Minimum width

    // Check header text width
    const headerText = $header.text().trim();
    const headerWidth = column_management.calculate_text_width(headerText) + 40; // Add padding
    maxWidth = Math.max(maxWidth, headerWidth);

    // Check data cell widths
    const $dataCells = list_view.$result.find(`.list-row:not(.list-row-head) .list-row-col[data-fieldname="${fieldname}"]`);

    $dataCells.each(function () {
        const cellText = $(this).text().trim();
        const cellWidth = column_management.calculate_text_width(cellText) + 20; // Add padding
        maxWidth = Math.max(maxWidth, cellWidth);
    });

    // Limit maximum width
    maxWidth = Math.min(maxWidth, 300);

    // Apply the calculated width
    $header.css('width', maxWidth + 'px');
    $dataCells.css('width', maxWidth + 'px');

    // Save the new width
    column_management.save_column_width(list_view.doctype, fieldname, maxWidth)
        .then(() => {
            frappe.show_alert({
                message: __('Column auto-resized and saved'),
                indicator: 'green'
            });
        })
        .catch(err => {
            console.error('Failed to save auto-resized width:', err);
        });
};

column_management.calculate_text_width = function (text) {
    // Create a temporary element to measure text width
    const $temp = $('<span>').text(text).css({
        'position': 'absolute',
        'visibility': 'hidden',
        'white-space': 'nowrap',
        'font-family': 'inherit',
        'font-size': 'inherit'
    }).appendTo('body');

    const width = $temp.width();
    $temp.remove();

    return width;
};

// Debounced width saving for performance
column_management.debounced_save_widths = frappe.utils.debounce(function (doctype, width_data) {
    column_management.save_multiple_column_widths(doctype, width_data)
        .then(() => {
            console.log('Column widths saved successfully');
        })
        .catch(err => {
            console.error('Failed to save column widths:', err);
        });
}, 1000);

// Batch width updates for better performance
column_management.batch_width_updates = {};

column_management.queue_width_update = function (doctype, fieldname, width) {
    if (!column_management.batch_width_updates[doctype]) {
        column_management.batch_width_updates[doctype] = {};
    }

    column_management.batch_width_updates[doctype][fieldname] = width;

    // Debounced save
    column_management.debounced_save_widths(doctype, column_management.batch_width_updates[doctype]);
};

// Initialize width persistence when document is ready
$(document).ready(function () {
    // Initialize enhanced list integration
    column_management.init_enhanced_list_integration();

    // Hook into list view events
    $(document).on('list_view_rendered', function (event, list_view) {
        if (list_view && list_view.doctype) {
            // Initialize column resize handlers
            setTimeout(() => {
                column_management.init_column_resize_handlers(list_view);
            }, 100);
        }
    });
});
// Enhanced List View Component with Pinned Column Rendering Logic
column_management.components.EnhancedListView = class EnhancedListView {
    constructor(options) {
        this.doctype = options.doctype;
        this.container = options.container;
        this.columns = options.columns || [];
        this.data = options.data || [];
        this.callbacks = options.callbacks || {};

        // Pinning state
        this.pinnedLeftColumns = [];
        this.pinnedRightColumns = [];
        this.regularColumns = [];

        this.init();
    }

    init() {
        this.organize_columns();
        this.render();
        this.bind_events();
        this.setup_pinned_column_positioning();
    }

    organize_columns() {
        this.pinnedLeftColumns = this.columns.filter(col => col.pinned === 'left').sort((a, b) => (a.order || 0) - (b.order || 0));
        this.pinnedRightColumns = this.columns.filter(col => col.pinned === 'right').sort((a, b) => (a.order || 0) - (b.order || 0));
        this.regularColumns = this.columns.filter(col => !col.pinned).sort((a, b) => (a.order || 0) - (b.order || 0));
    }

    render() {
        let html = `
            <div class="enhanced-list-container">
                <div class="enhanced-list-view">
                    <div class="table-container">
                        <div class="table-wrapper">
                            <table class="enhanced-table">
                                <thead class="table-header">
                                    ${this.render_header()}
                                </thead>
                                <tbody class="table-body">
                                    ${this.render_body()}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        `;

        this.container.html(html);
    }

    render_header() {
        let html = '<tr class="header-row">';

        // Render pinned left columns
        this.pinnedLeftColumns.forEach((column, index) => {
            html += this.render_header_cell(column, 'pinned-left', index + 1);
        });

        // Render regular columns
        this.regularColumns.forEach(column => {
            html += this.render_header_cell(column, '');
        });

        // Render pinned right columns
        this.pinnedRightColumns.forEach((column, index) => {
            html += this.render_header_cell(column, 'pinned-right', index + 1);
        });

        html += '</tr>';
        return html;
    }

    render_header_cell(column, pinnedClass, pinnedIndex) {
        const sortable = column.sortable !== false ? 'sortable' : '';
        const pinnedIndexClass = pinnedIndex ? `pinned-column-${pinnedIndex}` : '';

        return `
            <th class="header-cell ${sortable} ${pinnedClass} ${pinnedIndexClass}" 
                data-fieldname="${column.fieldname}"
                style="width: ${column.width}px; min-width: ${column.width}px; max-width: ${column.width}px;">
                <div class="header-content">
                    <span class="header-label">${column.label}</span>
                    <div class="header-controls">
                        ${column.sortable !== false ? '<i class="fa fa-sort sort-icon"></i>' : ''}
                        <i class="fa fa-ellipsis-v column-menu" data-fieldname="${column.fieldname}"></i>
                    </div>
                </div>
                <div class="resize-handle" data-fieldname="${column.fieldname}"></div>
            </th>
        `;
    }

    render_body() {
        let html = '';

        this.data.forEach((row, rowIndex) => {
            html += '<tr class="data-row">';

            // Render pinned left columns
            this.pinnedLeftColumns.forEach((column, index) => {
                html += this.render_data_cell(row, column, 'pinned-left', index + 1);
            });

            // Render regular columns
            this.regularColumns.forEach(column => {
                html += this.render_data_cell(row, column, '');
            });

            // Render pinned right columns
            this.pinnedRightColumns.forEach((column, index) => {
                html += this.render_data_cell(row, column, 'pinned-right', index + 1);
            });

            html += '</tr>';
        });

        return html;
    }

    render_data_cell(row, column, pinnedClass, pinnedIndex) {
        const pinnedIndexClass = pinnedIndex ? `pinned-column-${pinnedIndex}` : '';
        const value = row[column.fieldname] || '';

        return `
            <td class="data-cell ${pinnedClass} ${pinnedIndexClass}" 
                data-fieldname="${column.fieldname}"
                style="width: ${column.width}px; min-width: ${column.width}px; max-width: ${column.width}px;">
                <div class="cell-content">${this.format_cell_value(value, column)}</div>
            </td>
        `;
    }

    format_cell_value(value, column) {
        // Basic formatting - can be extended based on field type
        if (value === null || value === undefined) {
            return '';
        }

        switch (column.fieldtype) {
            case 'Currency':
                return frappe.format(value, { fieldtype: 'Currency' });
            case 'Date':
                return frappe.format(value, { fieldtype: 'Date' });
            case 'Datetime':
                return frappe.format(value, { fieldtype: 'Datetime' });
            case 'Check':
                return value ? '<i class="fa fa-check text-success"></i>' : '<i class="fa fa-times text-muted"></i>';
            default:
                return frappe.utils.escape_html(value);
        }
    }

    setup_pinned_column_positioning() {
        // Calculate and set CSS custom properties for multiple pinned columns
        let leftOffset = 0;
        let rightOffset = 0;

        // Set left pinned column positions
        this.pinnedLeftColumns.forEach((column, index) => {
            if (index > 0) {
                document.documentElement.style.setProperty(`--pinned-left-${index}-width`, `${leftOffset}px`);
            }
            leftOffset += column.width;
        });

        // Set right pinned column positions
        this.pinnedRightColumns.forEach((column, index) => {
            if (index > 0) {
                document.documentElement.style.setProperty(`--pinned-right-${index}-width`, `${rightOffset}px`);
            }
            rightOffset += column.width;
        });
    }

    bind_events() {
        const self = this;

        // Column header right-click context menu
        this.container.on('contextmenu', '.header-cell', function (e) {
            e.preventDefault();
            self.show_column_context_menu(e, $(this));
            return false;
        });

        // Column resize functionality
        this.container.on('mousedown', '.resize-handle', function (e) {
            self.start_column_resize(e, $(this));
        });

        // Hide context menu when clicking elsewhere
        $(document).on('click', function () {
            $('.column-context-menu').remove();
        });
    }

    show_column_context_menu(event, $headerCell) {
        const fieldname = $headerCell.data('fieldname');
        const column = this.columns.find(c => c.fieldname === fieldname);

        if (!column) return;

        // Remove any existing context menu
        $('.column-context-menu').remove();

        const pinned = column.pinned;
        let menuItems = '';

        // Pin options
        if (pinned === 'left') {
            menuItems += `
                <button class="dropdown-item unpin-context" data-fieldname="${fieldname}">
                    <i class="fa fa-times"></i> ${__('Unpin')}
                </button>
                <button class="dropdown-item pin-right-context" data-fieldname="${fieldname}">
                    <i class="fa fa-thumb-tack"></i> ${__('Pin Right')}
                </button>
            `;
        } else if (pinned === 'right') {
            menuItems += `
                <button class="dropdown-item unpin-context" data-fieldname="${fieldname}">
                    <i class="fa fa-times"></i> ${__('Unpin')}
                </button>
                <button class="dropdown-item pin-left-context" data-fieldname="${fieldname}">
                    <i class="fa fa-thumb-tack"></i> ${__('Pin Left')}
                </button>
            `;
        } else {
            menuItems += `
                <button class="dropdown-item pin-left-context" data-fieldname="${fieldname}">
                    <i class="fa fa-thumb-tack"></i> ${__('Pin Left')}
                </button>
                <button class="dropdown-item pin-right-context" data-fieldname="${fieldname}">
                    <i class="fa fa-thumb-tack"></i> ${__('Pin Right')}
                </button>
            `;
        }

        menuItems += `
            <div class="divider"></div>
            <button class="dropdown-item hide-column-context" data-fieldname="${fieldname}">
                <i class="fa fa-eye-slash"></i> ${__('Hide Column')}
            </button>
        `;

        const contextMenu = $(`
            <div class="column-context-menu" style="position: absolute; z-index: 1000;">
                ${menuItems}
            </div>
        `);

        // Position the menu
        const menuWidth = 150;
        const menuHeight = 120;
        let left = event.pageX;
        let top = event.pageY;

        // Adjust position if menu would go off screen
        if (left + menuWidth > $(window).width()) {
            left = event.pageX - menuWidth;
        }
        if (top + menuHeight > $(window).height()) {
            top = event.pageY - menuHeight;
        }

        contextMenu.css({
            left: left + 'px',
            top: top + 'px'
        });

        $('body').append(contextMenu);

        // Bind context menu events
        const self = this;
        contextMenu.on('click', '.pin-left-context', function () {
            self.pin_column(fieldname, 'left');
            $('.column-context-menu').remove();
        });

        contextMenu.on('click', '.pin-right-context', function () {
            self.pin_column(fieldname, 'right');
            $('.column-context-menu').remove();
        });

        contextMenu.on('click', '.unpin-context', function () {
            self.unpin_column(fieldname);
            $('.column-context-menu').remove();
        });

        contextMenu.on('click', '.hide-column-context', function () {
            self.hide_column(fieldname);
            $('.column-context-menu').remove();
        });
    }

    pin_column(fieldname, position) {
        const column = this.columns.find(c => c.fieldname === fieldname);
        if (!column) return;

        // Add animation class
        const $headerCell = this.container.find(`.header-cell[data-fieldname="${fieldname}"]`);
        const $dataCells = this.container.find(`.data-cell[data-fieldname="${fieldname}"]`);

        $headerCell.addClass('column-pinning');
        $dataCells.addClass('column-pinning');

        // Update column configuration
        column.pinned = position;

        // Re-organize and re-render with animation
        setTimeout(() => {
            this.organize_columns();
            this.render();
            this.setup_pinned_column_positioning();

            frappe.show_alert({
                message: __('Column "{0}" pinned to {1}', [column.label, position]),
                indicator: 'green'
            });

            if (this.callbacks.onColumnPin) {
                this.callbacks.onColumnPin(fieldname, position);
            }
        }, 150);
    }

    unpin_column(fieldname) {
        const column = this.columns.find(c => c.fieldname === fieldname);
        if (!column) return;

        // Add animation class
        const $headerCell = this.container.find(`.header-cell[data-fieldname="${fieldname}"]`);
        const $dataCells = this.container.find(`.data-cell[data-fieldname="${fieldname}"]`);

        $headerCell.addClass('column-unpinning');
        $dataCells.addClass('column-unpinning');

        // Update column configuration
        column.pinned = null;

        // Re-organize and re-render with animation
        setTimeout(() => {
            this.organize_columns();
            this.render();
            this.setup_pinned_column_positioning();

            frappe.show_alert({
                message: __('Column "{0}" unpinned', [column.label]),
                indicator: 'blue'
            });

            if (this.callbacks.onColumnUnpin) {
                this.callbacks.onColumnUnpin(fieldname);
            }
        }, 150);
    }

    hide_column(fieldname) {
        const column = this.columns.find(c => c.fieldname === fieldname);
        if (!column) return;

        column.visible = false;

        // Re-organize and re-render
        this.organize_columns();
        this.render();
        this.setup_pinned_column_positioning();

        frappe.show_alert({
            message: __('Column "{0}" hidden', [column.label]),
            indicator: 'orange'
        });

        if (this.callbacks.onColumnHide) {
            this.callbacks.onColumnHide(fieldname);
        }
    }

    start_column_resize(event, $handle) {
        const fieldname = $handle.data('fieldname');
        const column = this.columns.find(c => c.fieldname === fieldname);
        if (!column) return;

        const startX = event.pageX;
        const startWidth = column.width;

        const $headerCell = this.container.find(`.header-cell[data-fieldname="${fieldname}"]`);
        const $dataCells = this.container.find(`.data-cell[data-fieldname="${fieldname}"]`);

        $headerCell.addClass('resizing');

        const handleMouseMove = (e) => {
            const diff = e.pageX - startX;
            const newWidth = Math.max(50, Math.min(1000, startWidth + diff));

            // Update column width in real-time
            $headerCell.css('width', newWidth + 'px');
            $dataCells.css('width', newWidth + 'px');
        };

        const handleMouseUp = (e) => {
            const diff = e.pageX - startX;
            const newWidth = Math.max(50, Math.min(1000, startWidth + diff));

            // Update column configuration
            column.width = newWidth;

            // Clean up
            $headerCell.removeClass('resizing');
            $(document).off('mousemove', handleMouseMove);
            $(document).off('mouseup', handleMouseUp);

            // Update pinned column positioning if needed
            if (column.pinned) {
                this.setup_pinned_column_positioning();
            }

            if (this.callbacks.onColumnResize) {
                this.callbacks.onColumnResize(fieldname, newWidth);
            }
        };

        $(document).on('mousemove', handleMouseMove);
        $(document).on('mouseup', handleMouseUp);

        event.preventDefault();
    }

    update_data(newData) {
        this.data = newData;
        this.container.find('.table-body').html(this.render_body());
    }

    update_columns(newColumns) {
        this.columns = newColumns;
        this.organize_columns();
        this.render();
        this.setup_pinned_column_positioning();
    }
};
//Unlimited Column Display System - Task 8.1 & 8.2
column_management.init_unlimited_column_display = function () {
    // Initialize the unlimited column display system
    column_management.components.UnlimitedColumnDisplay = class UnlimitedColumnDisplay {
        constructor(options) {
            this.container = options.container;
            this.doctype = options.doctype;
            this.columns = options.columns || [];
            this.data = options.data || [];
            this.callbacks = options.callbacks || {};

            // Performance optimization settings
            this.virtualScrolling = options.virtualScrolling !== false;
            this.columnVirtualization = options.columnVirtualization !== false;
            this.visibleColumnBuffer = options.visibleColumnBuffer || 5;
            this.scrollThrottle = options.scrollThrottle || 16; // ~60fps

            // State management
            this.scrollLeft = 0;
            this.scrollTop = 0;
            this.containerWidth = 0;
            this.containerHeight = 0;
            this.totalWidth = 0;
            this.visibleColumns = [];
            this.renderedColumns = [];
            this.isScrolling = false;
            this.scrollTimer = null;

            // Column navigation state
            this.miniMapVisible = false;
            this.searchQuery = '';
            this.keyboardNavigation = true;

            this.init();
        }

        init() {
            this.setupContainer();
            this.calculateDimensions();
            this.setupEventListeners();
            this.render();
            this.setupKeyboardNavigation();
        }

        setupContainer() {
            this.container.addClass('unlimited-column-display');
            this.container.html(`
                <div class="column-display-header">
                    <div class="column-controls">
                        <button class="btn btn-xs btn-default toggle-minimap" title="${__('Toggle Mini-map')}">
                            <i class="fa fa-map"></i> ${__('Mini-map')}
                        </button>
                        <button class="btn btn-xs btn-default column-search-btn" title="${__('Search Columns')}">
                            <i class="fa fa-search"></i> ${__('Search')}
                        </button>
                        <div class="column-search-box" style="display: none;">
                            <input type="text" class="form-control column-search-input" 
                                   placeholder="${__('Search columns...')}" />
                        </div>
                        <span class="column-info">
                            ${__('Showing {0} of {1} columns', [0, this.columns.length])}
                        </span>
                    </div>
                    <div class="scroll-indicators">
                        <div class="horizontal-scroll-indicator">
                            <div class="scroll-thumb"></div>
                        </div>
                    </div>
                </div>
                <div class="column-display-body">
                    <div class="virtual-table-container">
                        <div class="table-header-container">
                            <div class="virtual-header-row"></div>
                        </div>
                        <div class="table-body-container">
                            <div class="virtual-scroll-spacer-left"></div>
                            <div class="virtual-table-body"></div>
                            <div class="virtual-scroll-spacer-right"></div>
                        </div>
                    </div>
                    <div class="column-minimap" style="display: none;">
                        <div class="minimap-content"></div>
                        <div class="minimap-viewport"></div>
                    </div>
                </div>
            `);

            // Get container references
            this.headerContainer = this.container.find('.table-header-container');
            this.bodyContainer = this.container.find('.table-body-container');
            this.virtualHeader = this.container.find('.virtual-header-row');
            this.virtualBody = this.container.find('.virtual-table-body');
            this.miniMap = this.container.find('.column-minimap');
            this.scrollIndicator = this.container.find('.horizontal-scroll-indicator');
            this.scrollThumb = this.container.find('.scroll-thumb');
        }

        calculateDimensions() {
            this.containerWidth = this.container.width();
            this.containerHeight = this.container.height() || 600;

            // Calculate total width of all columns
            this.totalWidth = this.columns.reduce((total, col) => {
                return total + (col.width || 150);
            }, 0);

            // Calculate visible columns based on container width
            this.updateVisibleColumns();
        }

        updateVisibleColumns() {
            const startX = this.scrollLeft;
            const endX = startX + this.containerWidth;

            this.visibleColumns = [];
            this.renderedColumns = [];

            let currentX = 0;
            let startIndex = -1;
            let endIndex = -1;

            // Find visible column range
            for (let i = 0; i < this.columns.length; i++) {
                const col = this.columns[i];
                const colWidth = col.width || 150;

                // Check if column intersects with visible area
                if (currentX + colWidth > startX && currentX < endX) {
                    if (startIndex === -1) startIndex = i;
                    endIndex = i;
                    this.visibleColumns.push({
                        ...col,
                        index: i,
                        left: currentX,
                        right: currentX + colWidth
                    });
                }

                currentX += colWidth;
            }

            // Add buffer columns for smooth scrolling
            const bufferStart = Math.max(0, startIndex - this.visibleColumnBuffer);
            const bufferEnd = Math.min(this.columns.length - 1, endIndex + this.visibleColumnBuffer);

            // Build rendered columns with buffer
            currentX = 0;
            for (let i = 0; i < this.columns.length; i++) {
                const col = this.columns[i];
                const colWidth = col.width || 150;

                if (i >= bufferStart && i <= bufferEnd) {
                    this.renderedColumns.push({
                        ...col,
                        index: i,
                        left: currentX,
                        right: currentX + colWidth,
                        visible: i >= startIndex && i <= endIndex
                    });
                }

                currentX += colWidth;
            }
        }

        setupEventListeners() {
            const self = this;

            // Horizontal scroll with momentum and throttling
            this.bodyContainer.on('scroll', this.throttle(function (e) {
                self.handleHorizontalScroll(e);
            }, this.scrollThrottle));

            // Smooth scrolling with momentum
            this.bodyContainer.on('wheel', function (e) {
                if (Math.abs(e.originalEvent.deltaX) > Math.abs(e.originalEvent.deltaY)) {
                    e.preventDefault();
                    self.handleMomentumScroll(e.originalEvent.deltaX);
                }
            });

            // Mini-map toggle
            this.container.on('click', '.toggle-minimap', function () {
                self.toggleMiniMap();
            });

            // Column search
            this.container.on('click', '.column-search-btn', function () {
                self.toggleColumnSearch();
            });

            this.container.on('input', '.column-search-input', function () {
                self.handleColumnSearch($(this).val());
            });

            // Resize observer for responsive behavior
            if (window.ResizeObserver) {
                this.resizeObserver = new ResizeObserver(function (entries) {
                    self.handleResize();
                });
                this.resizeObserver.observe(this.container[0]);
            }

            // Window resize fallback
            $(window).on('resize.unlimited-columns', function () {
                self.handleResize();
            });
        }

        setupKeyboardNavigation() {
            if (!this.keyboardNavigation) return;

            const self = this;

            // Make container focusable
            this.container.attr('tabindex', '0');

            this.container.on('keydown', function (e) {
                if (!self.container.is(':focus')) return;

                switch (e.keyCode) {
                    case 37: // Left arrow
                        e.preventDefault();
                        self.navigateColumn('left');
                        break;
                    case 39: // Right arrow
                        e.preventDefault();
                        self.navigateColumn('right');
                        break;
                    case 36: // Home
                        e.preventDefault();
                        self.scrollToColumn(0);
                        break;
                    case 35: // End
                        e.preventDefault();
                        self.scrollToColumn(self.columns.length - 1);
                        break;
                    case 70: // F key - find
                        if (e.ctrlKey || e.metaKey) {
                            e.preventDefault();
                            self.toggleColumnSearch();
                        }
                        break;
                    case 77: // M key - minimap
                        if (e.ctrlKey || e.metaKey) {
                            e.preventDefault();
                            self.toggleMiniMap();
                        }
                        break;
                }
            });
        }

        handleHorizontalScroll(e) {
            const newScrollLeft = e.target.scrollLeft;

            if (newScrollLeft !== this.scrollLeft) {
                this.scrollLeft = newScrollLeft;
                this.updateVisibleColumns();
                this.updateScrollIndicator();
                this.updateMiniMapViewport();

                // Sync header scroll
                this.headerContainer[0].scrollLeft = newScrollLeft;

                // Mark as scrolling for performance optimizations
                this.isScrolling = true;
                clearTimeout(this.scrollTimer);
                this.scrollTimer = setTimeout(() => {
                    this.isScrolling = false;
                    this.optimizeRendering();
                }, 150);

                // Re-render visible columns
                this.renderColumns();
            }
        }

        handleMomentumScroll(deltaX) {
            const scrollAmount = deltaX * 2; // Adjust scroll sensitivity
            const newScrollLeft = Math.max(0, Math.min(
                this.totalWidth - this.containerWidth,
                this.scrollLeft + scrollAmount
            ));

            // Smooth scroll animation
            this.bodyContainer.animate({
                scrollLeft: newScrollLeft
            }, {
                duration: 200,
                easing: 'easeOutCubic',
                step: (now) => {
                    this.scrollLeft = now;
                    this.updateVisibleColumns();
                    this.renderColumns();
                }
            });
        }

        handleResize() {
            this.calculateDimensions();
            this.updateScrollIndicator();
            this.renderMiniMap();
            this.render();
        }

        navigateColumn(direction) {
            const currentVisible = this.visibleColumns[0];
            if (!currentVisible) return;

            let targetIndex;
            if (direction === 'left') {
                targetIndex = Math.max(0, currentVisible.index - 1);
            } else {
                targetIndex = Math.min(this.columns.length - 1, currentVisible.index + 1);
            }

            this.scrollToColumn(targetIndex);
        }

        scrollToColumn(columnIndex) {
            if (columnIndex < 0 || columnIndex >= this.columns.length) return;

            let targetScrollLeft = 0;
            for (let i = 0; i < columnIndex; i++) {
                targetScrollLeft += this.columns[i].width || 150;
            }

            // Smooth scroll to column
            this.bodyContainer.animate({
                scrollLeft: targetScrollLeft
            }, {
                duration: 300,
                easing: 'easeInOutQuad'
            });

            // Highlight the target column briefly
            setTimeout(() => {
                this.highlightColumn(columnIndex);
            }, 300);
        }

        highlightColumn(columnIndex) {
            const $headerCell = this.virtualHeader.find(`[data-column-index="${columnIndex}"]`);
            if ($headerCell.length) {
                $headerCell.addClass('column-highlight');
                setTimeout(() => {
                    $headerCell.removeClass('column-highlight');
                }, 1000);
            }
        }

        toggleMiniMap() {
            this.miniMapVisible = !this.miniMapVisible;

            if (this.miniMapVisible) {
                this.miniMap.show();
                this.renderMiniMap();
                this.container.find('.toggle-minimap').addClass('active');
            } else {
                this.miniMap.hide();
                this.container.find('.toggle-minimap').removeClass('active');
            }
        }

        toggleColumnSearch() {
            const $searchBox = this.container.find('.column-search-box');
            const $searchInput = this.container.find('.column-search-input');

            if ($searchBox.is(':visible')) {
                $searchBox.hide();
                $searchInput.val('');
                this.handleColumnSearch('');
            } else {
                $searchBox.show();
                $searchInput.focus();
            }
        }

        handleColumnSearch(query) {
            this.searchQuery = query.toLowerCase();

            if (this.searchQuery) {
                // Find matching columns
                const matchingColumns = this.columns.filter((col, index) => {
                    return col.label.toLowerCase().includes(this.searchQuery) ||
                        col.fieldname.toLowerCase().includes(this.searchQuery);
                });

                if (matchingColumns.length > 0) {
                    // Scroll to first matching column
                    const firstMatch = this.columns.findIndex(col =>
                        col.fieldname === matchingColumns[0].fieldname
                    );
                    this.scrollToColumn(firstMatch);
                }

                // Highlight matching columns in mini-map
                this.updateMiniMapHighlights();
            } else {
                // Clear highlights
                this.clearSearchHighlights();
            }
        }

        renderMiniMap() {
            if (!this.miniMapVisible) return;

            const miniMapContent = this.miniMap.find('.minimap-content');
            const miniMapWidth = this.miniMap.width();
            const scale = miniMapWidth / this.totalWidth;

            let html = '';
            let currentX = 0;

            this.columns.forEach((col, index) => {
                const colWidth = (col.width || 150) * scale;
                const isPinned = col.pinned;
                const isHighlighted = this.searchQuery &&
                    (col.label.toLowerCase().includes(this.searchQuery) ||
                        col.fieldname.toLowerCase().includes(this.searchQuery));

                let className = 'minimap-column';
                if (isPinned === 'left') className += ' pinned-left';
                if (isPinned === 'right') className += ' pinned-right';
                if (isHighlighted) className += ' search-highlight';

                html += `
                    <div class="${className}" 
                         data-column-index="${index}"
                         style="left: ${currentX}px; width: ${colWidth}px;"
                         title="${col.label}">
                    </div>
                `;

                currentX += colWidth;
            });

            miniMapContent.html(html);
            this.updateMiniMapViewport();

            // Mini-map click navigation
            miniMapContent.off('click.minimap').on('click.minimap', '.minimap-column', (e) => {
                const columnIndex = parseInt($(e.target).data('column-index'));
                this.scrollToColumn(columnIndex);
            });
        }

        updateMiniMapViewport() {
            if (!this.miniMapVisible) return;

            const miniMapViewport = this.miniMap.find('.minimap-viewport');
            const miniMapWidth = this.miniMap.width();
            const scale = miniMapWidth / this.totalWidth;

            const viewportLeft = this.scrollLeft * scale;
            const viewportWidth = this.containerWidth * scale;

            miniMapViewport.css({
                left: viewportLeft + 'px',
                width: viewportWidth + 'px'
            });
        }

        updateMiniMapHighlights() {
            if (!this.miniMapVisible) return;

            this.miniMap.find('.minimap-column').removeClass('search-highlight');

            if (this.searchQuery) {
                this.columns.forEach((col, index) => {
                    if (col.label.toLowerCase().includes(this.searchQuery) ||
                        col.fieldname.toLowerCase().includes(this.searchQuery)) {
                        this.miniMap.find(`[data-column-index="${index}"]`).addClass('search-highlight');
                    }
                });
            }
        }

        clearSearchHighlights() {
            this.miniMap.find('.minimap-column').removeClass('search-highlight');
            this.virtualHeader.find('.header-cell').removeClass('search-highlight');
        }

        updateScrollIndicator() {
            if (this.totalWidth <= this.containerWidth) {
                this.scrollIndicator.hide();
                return;
            }

            this.scrollIndicator.show();

            const thumbWidth = (this.containerWidth / this.totalWidth) * 100;
            const thumbLeft = (this.scrollLeft / (this.totalWidth - this.containerWidth)) * (100 - thumbWidth);

            this.scrollThumb.css({
                width: thumbWidth + '%',
                left: thumbLeft + '%'
            });
        }

        render() {
            this.renderColumns();
            this.updateScrollIndicator();
            this.updateColumnInfo();

            if (this.miniMapVisible) {
                this.renderMiniMap();
            }
        }

        renderColumns() {
            if (this.columnVirtualization) {
                this.renderVirtualizedColumns();
            } else {
                this.renderAllColumns();
            }
        }

        renderVirtualizedColumns() {
            // Render only visible columns for performance
            let headerHtml = '';
            let bodyHtml = '';

            // Calculate spacer widths
            const leftSpacerWidth = this.renderedColumns.length > 0 ? this.renderedColumns[0].left : 0;
            const rightSpacerWidth = this.totalWidth - (this.renderedColumns.length > 0 ?
                this.renderedColumns[this.renderedColumns.length - 1].right : 0);

            // Set spacer widths
            this.container.find('.virtual-scroll-spacer-left').width(leftSpacerWidth);
            this.container.find('.virtual-scroll-spacer-right').width(rightSpacerWidth);

            // Render visible columns
            this.renderedColumns.forEach((col, index) => {
                const isPinned = col.pinned;
                const isHighlighted = this.searchQuery &&
                    (col.label.toLowerCase().includes(this.searchQuery) ||
                        col.fieldname.toLowerCase().includes(this.searchQuery));

                let headerClass = 'header-cell virtual-column';
                let bodyClass = 'data-cell virtual-column';

                if (isPinned === 'left') {
                    headerClass += ' pinned-left';
                    bodyClass += ' pinned-left';
                }
                if (isPinned === 'right') {
                    headerClass += ' pinned-right';
                    bodyClass += ' pinned-right';
                }
                if (isHighlighted) {
                    headerClass += ' search-highlight';
                }

                // Header cell
                headerHtml += `
                    <div class="${headerClass}" 
                         data-column-index="${col.index}"
                         data-fieldname="${col.fieldname}"
                         style="width: ${col.width || 150}px; min-width: ${col.width || 150}px;">
                        <div class="header-content">
                            <span class="header-label">${col.label}</span>
                            <i class="fa fa-sort sort-icon"></i>
                            <i class="fa fa-ellipsis-v column-menu"></i>
                        </div>
                        <div class="resize-handle"></div>
                    </div>
                `;
            });

            this.virtualHeader.html(headerHtml);

            // Render data rows (simplified for demo)
            this.data.slice(0, 50).forEach((row, rowIndex) => {
                let rowHtml = '<div class="virtual-row">';

                this.renderedColumns.forEach((col) => {
                    const cellValue = row[col.fieldname] || '';
                    let cellClass = 'data-cell virtual-column';

                    if (col.pinned === 'left') cellClass += ' pinned-left';
                    if (col.pinned === 'right') cellClass += ' pinned-right';

                    rowHtml += `
                        <div class="${cellClass}" 
                             style="width: ${col.width || 150}px; min-width: ${col.width || 150}px;">
                            <div class="cell-content">${cellValue}</div>
                        </div>
                    `;
                });

                rowHtml += '</div>';
                bodyHtml += rowHtml;
            });

            this.virtualBody.html(bodyHtml);
        }

        renderAllColumns() {
            // Fallback: render all columns (less performant but simpler)
            let headerHtml = '';
            let bodyHtml = '';

            this.columns.forEach((col, index) => {
                const isHighlighted = this.searchQuery &&
                    (col.label.toLowerCase().includes(this.searchQuery) ||
                        col.fieldname.toLowerCase().includes(this.searchQuery));

                let headerClass = 'header-cell';
                if (col.pinned === 'left') headerClass += ' pinned-left';
                if (col.pinned === 'right') headerClass += ' pinned-right';
                if (isHighlighted) headerClass += ' search-highlight';

                headerHtml += `
                    <div class="${headerClass}" 
                         data-column-index="${index}"
                         data-fieldname="${col.fieldname}"
                         style="width: ${col.width || 150}px;">
                        <div class="header-content">
                            <span class="header-label">${col.label}</span>
                            <i class="fa fa-sort sort-icon"></i>
                            <i class="fa fa-ellipsis-v column-menu"></i>
                        </div>
                        <div class="resize-handle"></div>
                    </div>
                `;
            });

            this.virtualHeader.html(headerHtml);

            // Render data rows
            this.data.slice(0, 50).forEach((row, rowIndex) => {
                let rowHtml = '<div class="data-row">';

                this.columns.forEach((col) => {
                    const cellValue = row[col.fieldname] || '';
                    let cellClass = 'data-cell';

                    if (col.pinned === 'left') cellClass += ' pinned-left';
                    if (col.pinned === 'right') cellClass += ' pinned-right';

                    rowHtml += `
                        <div class="${cellClass}" style="width: ${col.width || 150}px;">
                            <div class="cell-content">${cellValue}</div>
                        </div>
                    `;
                });

                rowHtml += '</div>';
                bodyHtml += rowHtml;
            });

            this.virtualBody.html(bodyHtml);
        }

        updateColumnInfo() {
            const visibleCount = this.visibleColumns.length;
            const totalCount = this.columns.length;
            this.container.find('.column-info').text(
                __('Showing {0} of {1} columns', [visibleCount, totalCount])
            );
        }

        optimizeRendering() {
            // Perform optimizations when scrolling stops
            if (!this.isScrolling) {
                // Clean up off-screen elements
                this.cleanupOffscreenElements();

                // Update column visibility states
                this.updateColumnVisibility();
            }
        }

        cleanupOffscreenElements() {
            // Remove elements that are far off-screen to save memory
            const buffer = this.visibleColumnBuffer * 2;

            this.virtualHeader.find('.header-cell').each((index, element) => {
                const $element = $(element);
                const columnIndex = parseInt($element.data('column-index'));

                if (columnIndex < this.visibleColumns[0]?.index - buffer ||
                    columnIndex > this.visibleColumns[this.visibleColumns.length - 1]?.index + buffer) {
                    // Mark for cleanup but don't remove immediately to avoid flicker
                    $element.addClass('cleanup-candidate');
                }
            });
        }

        updateColumnVisibility() {
            // Update visibility classes for CSS optimizations
            this.virtualHeader.find('.header-cell').removeClass('fully-visible partially-visible');

            this.visibleColumns.forEach(col => {
                const $headerCell = this.virtualHeader.find(`[data-column-index="${col.index}"]`);

                if (col.left >= this.scrollLeft && col.right <= this.scrollLeft + this.containerWidth) {
                    $headerCell.addClass('fully-visible');
                } else {
                    $headerCell.addClass('partially-visible');
                }
            });
        }

        // Utility function for throttling scroll events
        throttle(func, limit) {
            let inThrottle;
            return function () {
                const args = arguments;
                const context = this;
                if (!inThrottle) {
                    func.apply(context, args);
                    inThrottle = true;
                    setTimeout(() => inThrottle = false, limit);
                }
            }
        }

        // Public API methods
        scrollToStart() {
            this.bodyContainer.animate({ scrollLeft: 0 }, 300);
        }

        scrollToEnd() {
            this.bodyContainer.animate({
                scrollLeft: this.totalWidth - this.containerWidth
            }, 300);
        }

        jumpToColumn(fieldname) {
            const columnIndex = this.columns.findIndex(col => col.fieldname === fieldname);
            if (columnIndex !== -1) {
                this.scrollToColumn(columnIndex);
            }
        }

        setColumns(newColumns) {
            this.columns = newColumns;
            this.calculateDimensions();
            this.render();
        }

        setData(newData) {
            this.data = newData;
            this.render();
        }

        destroy() {
            // Cleanup
            if (this.resizeObserver) {
                this.resizeObserver.disconnect();
            }
            $(window).off('resize.unlimited-columns');
            clearTimeout(this.scrollTimer);
            this.container.off();
        }
    };
};
// Enhanced Column Navigation and Mini-map - Task 8.2 Extensions
column_management.components.ColumnNavigator = class ColumnNavigator {
    constructor(options) {
        this.container = options.container;
        this.columns = options.columns || [];
        this.callbacks = options.callbacks || {};
        this.keyboardShortcuts = options.keyboardShortcuts !== false;

        // Navigation state
        this.currentColumnIndex = 0;
        this.searchResults = [];
        this.searchIndex = 0;

        this.init();
    }

    init() {
        this.render();
        this.bindEvents();
        this.setupKeyboardShortcuts();
    }

    render() {
        const html = `
            <div class="column-navigator">
                <div class="navigator-header">
                    <h6><i class="fa fa-compass"></i> ${__('Column Navigator')}</h6>
                    <button class="btn btn-xs btn-default close-navigator">
                        <i class="fa fa-times"></i>
                    </button>
                </div>
                <div class="navigator-search">
                    <div class="input-group">
                        <input type="text" class="form-control navigator-search-input" 
                               placeholder="${__('Search columns...')}" />
                        <div class="input-group-btn">
                            <button class="btn btn-default search-prev" title="${__('Previous')}">
                                <i class="fa fa-chevron-up"></i>
                            </button>
                            <button class="btn btn-default search-next" title="${__('Next')}">
                                <i class="fa fa-chevron-down"></i>
                            </button>
                        </div>
                    </div>
                    <div class="search-results-info"></div>
                </div>
                <div class="navigator-shortcuts">
                    <div class="shortcut-group">
                        <h6>${__('Quick Navigation')}</h6>
                        <div class="shortcut-buttons">
                            <button class="btn btn-xs btn-default" data-action="first">
                                <i class="fa fa-fast-backward"></i> ${__('First')}
                            </button>
                            <button class="btn btn-xs btn-default" data-action="prev">
                                <i class="fa fa-chevron-left"></i> ${__('Previous')}
                            </button>
                            <button class="btn btn-xs btn-default" data-action="next">
                                <i class="fa fa-chevron-right"></i> ${__('Next')}
                            </button>
                            <button class="btn btn-xs btn-default" data-action="last">
                                <i class="fa fa-fast-forward"></i> ${__('Last')}
                            </button>
                        </div>
                    </div>
                    <div class="shortcut-group">
                        <h6>${__('Jump to Column')}</h6>
                        <div class="column-jump">
                            <select class="form-control column-select">
                                <option value="">${__('Select column...')}</option>
                                ${this.renderColumnOptions()}
                            </select>
                            <button class="btn btn-default jump-to-column">
                                <i class="fa fa-arrow-right"></i> ${__('Go')}
                            </button>
                        </div>
                    </div>
                </div>
                <div class="navigator-minimap">
                    <h6>${__('Column Overview')}</h6>
                    <div class="minimap-container">
                        <div class="minimap-track">
                            ${this.renderMiniMapColumns()}
                        </div>
                        <div class="minimap-viewport-indicator"></div>
                    </div>
                    <div class="minimap-legend">
                        <span class="legend-item">
                            <span class="legend-color normal"></span> ${__('Normal')}
                        </span>
                        <span class="legend-item">
                            <span class="legend-color pinned-left"></span> ${__('Pinned Left')}
                        </span>
                        <span class="legend-item">
                            <span class="legend-color pinned-right"></span> ${__('Pinned Right')}
                        </span>
                    </div>
                </div>
                <div class="navigator-keyboard-help">
                    <h6>${__('Keyboard Shortcuts')}</h6>
                    <div class="keyboard-shortcuts">
                        <div class="shortcut-item">
                            <kbd>←</kbd><kbd>→</kbd> ${__('Navigate columns')}
                        </div>
                        <div class="shortcut-item">
                            <kbd>Home</kbd><kbd>End</kbd> ${__('First/Last column')}
                        </div>
                        <div class="shortcut-item">
                            <kbd>Ctrl</kbd>+<kbd>F</kbd> ${__('Search columns')}
                        </div>
                        <div class="shortcut-item">
                            <kbd>Ctrl</kbd>+<kbd>M</kbd> ${__('Toggle mini-map')}
                        </div>
                        <div class="shortcut-item">
                            <kbd>F3</kbd> ${__('Find next')}
                        </div>
                        <div class="shortcut-item">
                            <kbd>Shift</kbd>+<kbd>F3</kbd> ${__('Find previous')}
                        </div>
                    </div>
                </div>
            </div>
        `;

        this.container.html(html);
    }

    renderColumnOptions() {
        return this.columns.map((col, index) => {
            const pinned = col.pinned ? ` (${col.pinned === 'left' ? 'Left' : 'Right'} Pinned)` : '';
            return `<option value="${index}">${col.label}${pinned}</option>`;
        }).join('');
    }

    renderMiniMapColumns() {
        const totalWidth = this.columns.reduce((sum, col) => sum + (col.width || 150), 0);
        const mapWidth = 200; // Fixed minimap width
        const scale = mapWidth / totalWidth;

        let html = '';
        let currentX = 0;

        this.columns.forEach((col, index) => {
            const colWidth = (col.width || 150) * scale;
            let className = 'minimap-column';

            if (col.pinned === 'left') className += ' pinned-left';
            else if (col.pinned === 'right') className += ' pinned-right';

            html += `
                <div class="${className}" 
                     data-column-index="${index}"
                     style="left: ${currentX}px; width: ${Math.max(2, colWidth)}px;"
                     title="${col.label}">
                </div>
            `;

            currentX += colWidth;
        });

        return html;
    }

    bindEvents() {
        const self = this;

        // Close navigator
        this.container.on('click', '.close-navigator', function () {
            self.hide();
        });

        // Search functionality
        this.container.on('input', '.navigator-search-input', function () {
            self.handleSearch($(this).val());
        });

        this.container.on('click', '.search-prev', function () {
            self.navigateSearchResults(-1);
        });

        this.container.on('click', '.search-next', function () {
            self.navigateSearchResults(1);
        });

        // Quick navigation buttons
        this.container.on('click', '[data-action]', function () {
            const action = $(this).data('action');
            self.handleQuickNavigation(action);
        });

        // Column jump
        this.container.on('click', '.jump-to-column', function () {
            const selectedIndex = parseInt(self.container.find('.column-select').val());
            if (!isNaN(selectedIndex)) {
                self.jumpToColumn(selectedIndex);
            }
        });

        this.container.on('change', '.column-select', function () {
            const selectedIndex = parseInt($(this).val());
            if (!isNaN(selectedIndex)) {
                self.jumpToColumn(selectedIndex);
            }
        });

        // Minimap navigation
        this.container.on('click', '.minimap-column', function () {
            const columnIndex = parseInt($(this).data('column-index'));
            self.jumpToColumn(columnIndex);
        });

        // Enter key in search
        this.container.on('keydown', '.navigator-search-input', function (e) {
            if (e.keyCode === 13) { // Enter
                e.preventDefault();
                if (e.shiftKey) {
                    self.navigateSearchResults(-1);
                } else {
                    self.navigateSearchResults(1);
                }
            }
        });
    }

    setupKeyboardShortcuts() {
        if (!this.keyboardShortcuts) return;

        const self = this;

        $(document).on('keydown.column-navigator', function (e) {
            // Only handle shortcuts when navigator is visible
            if (!self.container.is(':visible')) return;

            switch (e.keyCode) {
                case 114: // F3
                    e.preventDefault();
                    if (e.shiftKey) {
                        self.navigateSearchResults(-1);
                    } else {
                        self.navigateSearchResults(1);
                    }
                    break;

                case 70: // F key
                    if (e.ctrlKey || e.metaKey) {
                        e.preventDefault();
                        self.focusSearch();
                    }
                    break;

                case 77: // M key
                    if (e.ctrlKey || e.metaKey) {
                        e.preventDefault();
                        self.toggleMiniMapHighlight();
                    }
                    break;

                case 27: // Escape
                    e.preventDefault();
                    self.hide();
                    break;
            }
        });
    }

    handleSearch(query) {
        this.searchResults = [];
        this.searchIndex = 0;

        if (!query.trim()) {
            this.updateSearchResults();
            this.clearSearchHighlights();
            return;
        }

        const searchTerm = query.toLowerCase();

        this.columns.forEach((col, index) => {
            if (col.label.toLowerCase().includes(searchTerm) ||
                col.fieldname.toLowerCase().includes(searchTerm)) {
                this.searchResults.push({
                    index: index,
                    column: col,
                    matchType: col.label.toLowerCase().includes(searchTerm) ? 'label' : 'fieldname'
                });
            }
        });

        this.updateSearchResults();
        this.highlightSearchResults();

        if (this.searchResults.length > 0) {
            this.jumpToColumn(this.searchResults[0].index);
        }
    }

    navigateSearchResults(direction) {
        if (this.searchResults.length === 0) return;

        this.searchIndex += direction;

        if (this.searchIndex >= this.searchResults.length) {
            this.searchIndex = 0;
        } else if (this.searchIndex < 0) {
            this.searchIndex = this.searchResults.length - 1;
        }

        this.updateSearchResults();
        this.jumpToColumn(this.searchResults[this.searchIndex].index);
    }

    updateSearchResults() {
        const info = this.container.find('.search-results-info');

        if (this.searchResults.length === 0) {
            info.text('');
        } else {
            info.text(__('Result {0} of {1}', [this.searchIndex + 1, this.searchResults.length]));
        }

        // Update button states
        this.container.find('.search-prev, .search-next').prop('disabled', this.searchResults.length === 0);
    }

    highlightSearchResults() {
        this.clearSearchHighlights();

        this.searchResults.forEach(result => {
            this.container.find(`.minimap-column[data-column-index="${result.index}"]`)
                .addClass('search-highlight');
        });
    }

    clearSearchHighlights() {
        this.container.find('.minimap-column').removeClass('search-highlight current-result');
    }

    handleQuickNavigation(action) {
        switch (action) {
            case 'first':
                this.jumpToColumn(0);
                break;
            case 'last':
                this.jumpToColumn(this.columns.length - 1);
                break;
            case 'prev':
                this.jumpToColumn(Math.max(0, this.currentColumnIndex - 1));
                break;
            case 'next':
                this.jumpToColumn(Math.min(this.columns.length - 1, this.currentColumnIndex + 1));
                break;
        }
    }

    jumpToColumn(columnIndex) {
        if (columnIndex < 0 || columnIndex >= this.columns.length) return;

        this.currentColumnIndex = columnIndex;

        // Update UI
        this.updateCurrentColumnIndicator();
        this.container.find('.column-select').val(columnIndex);

        // Highlight current result if in search mode
        if (this.searchResults.length > 0) {
            this.container.find('.minimap-column').removeClass('current-result');
            this.container.find(`.minimap-column[data-column-index="${columnIndex}"]`)
                .addClass('current-result');
        }

        // Callback to parent component
        if (this.callbacks.onColumnJump) {
            this.callbacks.onColumnJump(columnIndex, this.columns[columnIndex]);
        }
    }

    updateCurrentColumnIndicator() {
        // Update minimap viewport indicator
        const totalWidth = this.columns.reduce((sum, col) => sum + (col.width || 150), 0);
        const mapWidth = 200;
        const scale = mapWidth / totalWidth;

        let currentX = 0;
        for (let i = 0; i < this.currentColumnIndex; i++) {
            currentX += (this.columns[i].width || 150) * scale;
        }

        const currentColWidth = (this.columns[this.currentColumnIndex]?.width || 150) * scale;

        this.container.find('.minimap-viewport-indicator').css({
            left: currentX + 'px',
            width: Math.max(2, currentColWidth) + 'px'
        });
    }

    focusSearch() {
        this.container.find('.navigator-search-input').focus().select();
    }

    toggleMiniMapHighlight() {
        this.container.find('.minimap-container').toggleClass('highlighted');
    }

    show() {
        this.container.show();
        this.updateCurrentColumnIndicator();
    }

    hide() {
        this.container.hide();
        this.clearSearchHighlights();
        $(document).off('keydown.column-navigator');
    }

    setColumns(newColumns) {
        this.columns = newColumns;
        this.render();
        this.bindEvents();
    }

    setCurrentColumn(columnIndex) {
        this.currentColumnIndex = columnIndex;
        this.updateCurrentColumnIndicator();
    }

    destroy() {
        $(document).off('keydown.column-navigator');
        this.container.off();
    }
};

// Integration function to create column navigator
column_management.create_column_navigator = function (container, columns, callbacks) {
    return new column_management.components.ColumnNavigator({
        container: container,
        columns: columns,
        callbacks: callbacks
    });
};

// Quick jump functionality
column_management.components.QuickJump = class QuickJump {
    constructor(options) {
        this.columns = options.columns || [];
        this.callbacks = options.callbacks || {};
        this.fuzzySearch = options.fuzzySearch !== false;

        this.init();
    }

    init() {
        this.setupQuickJumpDialog();
    }

    setupQuickJumpDialog() {
        const self = this;

        // Create quick jump dialog
        this.dialog = new frappe.ui.Dialog({
            title: __('Quick Jump to Column'),
            fields: [
                {
                    fieldtype: 'Data',
                    fieldname: 'column_search',
                    label: __('Search Columns'),
                    placeholder: __('Type column name...'),
                    reqd: 1
                },
                {
                    fieldtype: 'HTML',
                    fieldname: 'search_results',
                    options: '<div class="quick-jump-results"></div>'
                }
            ],
            primary_action_label: __('Jump'),
            primary_action: function (values) {
                const selectedColumn = self.getSelectedColumn();
                if (selectedColumn) {
                    self.jumpToColumn(selectedColumn);
                    self.dialog.hide();
                }
            }
        });

        // Setup search functionality
        this.dialog.fields_dict.column_search.$input.on('input', function () {
            self.performSearch($(this).val());
        });

        this.dialog.fields_dict.column_search.$input.on('keydown', function (e) {
            self.handleKeyNavigation(e);
        });
    }

    show() {
        this.dialog.show();
        this.dialog.fields_dict.column_search.$input.focus();
        this.performSearch(''); // Show all columns initially
    }

    performSearch(query) {
        const results = this.searchColumns(query);
        this.renderSearchResults(results);
    }

    searchColumns(query) {
        if (!query.trim()) {
            return this.columns.map((col, index) => ({
                column: col,
                index: index,
                score: 1,
                matchType: 'all'
            }));
        }

        const searchTerm = query.toLowerCase();
        const results = [];

        this.columns.forEach((col, index) => {
            let score = 0;
            let matchType = '';

            // Exact label match
            if (col.label.toLowerCase() === searchTerm) {
                score = 100;
                matchType = 'exact-label';
            }
            // Exact fieldname match
            else if (col.fieldname.toLowerCase() === searchTerm) {
                score = 95;
                matchType = 'exact-fieldname';
            }
            // Label starts with search term
            else if (col.label.toLowerCase().startsWith(searchTerm)) {
                score = 90;
                matchType = 'starts-label';
            }
            // Fieldname starts with search term
            else if (col.fieldname.toLowerCase().startsWith(searchTerm)) {
                score = 85;
                matchType = 'starts-fieldname';
            }
            // Label contains search term
            else if (col.label.toLowerCase().includes(searchTerm)) {
                score = 70;
                matchType = 'contains-label';
            }
            // Fieldname contains search term
            else if (col.fieldname.toLowerCase().includes(searchTerm)) {
                score = 65;
                matchType = 'contains-fieldname';
            }
            // Fuzzy match
            else if (this.fuzzySearch && this.fuzzyMatch(col.label.toLowerCase(), searchTerm)) {
                score = 50;
                matchType = 'fuzzy';
            }

            if (score > 0) {
                results.push({
                    column: col,
                    index: index,
                    score: score,
                    matchType: matchType
                });
            }
        });

        // Sort by score (highest first)
        return results.sort((a, b) => b.score - a.score);
    }

    fuzzyMatch(text, pattern) {
        const textLen = text.length;
        const patternLen = pattern.length;

        if (patternLen > textLen) return false;
        if (patternLen === textLen) return text === pattern;

        let textIndex = 0;
        let patternIndex = 0;

        while (textIndex < textLen && patternIndex < patternLen) {
            if (text[textIndex] === pattern[patternIndex]) {
                patternIndex++;
            }
            textIndex++;
        }

        return patternIndex === patternLen;
    }

    renderSearchResults(results) {
        const container = this.dialog.$wrapper.find('.quick-jump-results');

        if (results.length === 0) {
            container.html(`
                <div class="no-results">
                    <i class="fa fa-search"></i>
                    <p>${__('No columns found')}</p>
                </div>
            `);
            return;
        }

        let html = '<div class="search-results-list">';

        results.slice(0, 10).forEach((result, index) => {
            const col = result.column;
            const isSelected = index === 0;
            const pinnedIndicator = col.pinned ?
                `<span class="pinned-indicator pinned-${col.pinned}">
                    <i class="fa fa-thumb-tack"></i> ${col.pinned}
                </span>` : '';

            html += `
                <div class="result-item ${isSelected ? 'selected' : ''}" 
                     data-column-index="${result.index}">
                    <div class="result-main">
                        <div class="result-label">${this.highlightMatch(col.label, this.dialog.get_value('column_search'))}</div>
                        <div class="result-fieldname">${col.fieldname}</div>
                    </div>
                    <div class="result-meta">
                        ${pinnedIndicator}
                        <span class="result-type">${col.fieldtype}</span>
                    </div>
                </div>
            `;
        });

        html += '</div>';

        if (results.length > 10) {
            html += `<div class="more-results">${__('... and {0} more', [results.length - 10])}</div>`;
        }

        container.html(html);

        // Bind click events
        container.find('.result-item').on('click', (e) => {
            const columnIndex = parseInt($(e.currentTarget).data('column-index'));
            this.jumpToColumn(this.columns[columnIndex]);
            this.dialog.hide();
        });
    }

    highlightMatch(text, query) {
        if (!query.trim()) return text;

        const regex = new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
        return text.replace(regex, '<mark>$1</mark>');
    }

    handleKeyNavigation(e) {
        const $results = this.dialog.$wrapper.find('.result-item');
        const $selected = $results.filter('.selected');

        switch (e.keyCode) {
            case 38: // Up arrow
                e.preventDefault();
                if ($selected.length) {
                    const $prev = $selected.prev('.result-item');
                    if ($prev.length) {
                        $selected.removeClass('selected');
                        $prev.addClass('selected');
                    }
                }
                break;

            case 40: // Down arrow
                e.preventDefault();
                if ($selected.length) {
                    const $next = $selected.next('.result-item');
                    if ($next.length) {
                        $selected.removeClass('selected');
                        $next.addClass('selected');
                    }
                } else if ($results.length) {
                    $results.first().addClass('selected');
                }
                break;

            case 13: // Enter
                e.preventDefault();
                const selectedColumn = this.getSelectedColumn();
                if (selectedColumn) {
                    this.jumpToColumn(selectedColumn);
                    this.dialog.hide();
                }
                break;
        }
    }

    getSelectedColumn() {
        const $selected = this.dialog.$wrapper.find('.result-item.selected');
        if ($selected.length) {
            const columnIndex = parseInt($selected.data('column-index'));
            return this.columns[columnIndex];
        }
        return null;
    }

    jumpToColumn(column) {
        if (this.callbacks.onColumnJump) {
            this.callbacks.onColumnJump(column);
        }
    }

    setColumns(newColumns) {
        this.columns = newColumns;
    }
};

// Create quick jump instance
column_management.create_quick_jump = function (columns, callbacks) {
    return new column_management.components.QuickJump({
        columns: columns,
        callbacks: callbacks
    });
};
// Enhanced Pagination System Initialization - Task 9.1
column_management.init_enhanced_pagination = function () {
    // Override default Frappe list pagination
    if (frappe.views && frappe.views.ListView) {
        const original_setup_paging = frappe.views.ListView.prototype.setup_paging;

        frappe.views.ListView.prototype.setup_paging = function () {
            // Call original setup first
            original_setup_paging.call(this);

            // Replace with enhanced pagination
            if (this.$paging_area && this.doctype) {
                this.setup_enhanced_pagination();
            }
        };

        frappe.views.ListView.prototype.setup_enhanced_pagination = function () {
            const self = this;

            // Create enhanced pagination container
            const $pagination_container = $('<div class="enhanced-pagination-container"></div>');
            this.$paging_area.html($pagination_container);

            // Initialize enhanced pagination component
            this.enhanced_pagination = new column_management.components.EnhancedPagination({
                container: $pagination_container,
                doctype: this.doctype,
                currentPage: this.start ? Math.floor(this.start / this.page_length) + 1 : 1,
                pageSize: this.page_length || 20,
                totalRecords: this.total_count || 0,
                callbacks: {
                    onPageChange: function (state) {
                        self.handle_page_change(state);
                    },
                    onPageSizeChange: function (state) {
                        self.handle_page_size_change(state);
                    }
                }
            });

            // Store reference for updates
            this.pagination_component = this.enhanced_pagination;
        };

        frappe.views.ListView.prototype.handle_page_change = function (state) {
            const new_start = (state.page - 1) * state.pageSize;
            this.start = new_start;

            // Use enhanced data loading with error handling
            this.load_paginated_data(state);
        };

        frappe.views.ListView.prototype.handle_page_size_change = function (state) {
            this.page_length = state.pageSize;
            this.start = (state.page - 1) * state.pageSize;

            // Use enhanced data loading with error handling
            this.load_paginated_data(state);
        };

        frappe.views.ListView.prototype.load_paginated_data = function (pagination_state) {
            const self = this;

            // Prepare filter state
            const filter_state = {
                filters: this.get_current_filters(),
                active_saved_filter: this.active_saved_filter || null
            };

            // Show loading indicator
            if (this.pagination_component) {
                this.pagination_component.show_loading();
            }

            // Call enhanced API
            frappe.call({
                method: 'column_management.api.enhanced_list.get_paginated_filtered_data',
                args: {
                    doctype: this.doctype,
                    filter_state: filter_state,
                    pagination_state: pagination_state
                },
                callback: function (r) {
                    if (self.pagination_component) {
                        self.pagination_component.hide_loading();
                    }

                    if (r.message && r.message.success) {
                        // Update list data
                        self.data = r.message.data.records;
                        self.total_count = r.message.data.pagination.total_count;

                        // Update pagination component
                        if (self.pagination_component) {
                            self.pagination_component.update_total_records(self.total_count);
                        }

                        // Re-render list
                        self.render_list();

                    } else {
                        // Handle error
                        column_management.enhanced_data_loader.handle_loading_error(
                            new Error(r.message?.message || 'Failed to load data'),
                            self.$result
                        );
                    }
                },
                error: function (err) {
                    if (self.pagination_component) {
                        self.pagination_component.hide_loading();
                    }

                    column_management.enhanced_data_loader.handle_loading_error(
                        err,
                        self.$result
                    );
                }
            });
        };

        frappe.views.ListView.prototype.get_current_filters = function () {
            // Extract current filters from list view
            const filters = [];

            if (this.filter_area && this.filter_area.filter_list) {
                this.filter_area.filter_list.get_filters().forEach(filter => {
                    if (filter[1] && filter[2] && filter[3] !== undefined) {
                        filters.push({
                            fieldname: filter[1],
                            operator: filter[2],
                            value: filter[3],
                            logic: 'AND' // Default logic
                        });
                    }
                });
            }

            return filters;
        };

        // Override refresh to update pagination
        const original_refresh = frappe.views.ListView.prototype.refresh;
        frappe.views.ListView.prototype.refresh = function () {
            const self = this;

            // Show loading on pagination if it exists
            if (this.pagination_component) {
                this.pagination_component.show_loading();
            }

            return original_refresh.call(this).then(function () {
                // Update pagination after refresh
                if (self.pagination_component) {
                    self.pagination_component.update_total_records(self.total_count || 0);
                    self.pagination_component.hide_loading();
                }
            });
        };
    }
};

// Enhanced Pagination with Filter Integration - Task 9.2
column_management.init_pagination_filter_integration = function () {
    // Override filter application to reset pagination
    if (frappe.views && frappe.views.ListView) {
        const original_apply_filters = frappe.views.ListView.prototype.apply_filters;

        frappe.views.ListView.prototype.apply_filters = function () {
            const self = this;

            // Reset pagination to first page when filters change
            if (this.pagination_component) {
                this.pagination_component.reset_to_first_page();
            }

            // Show loading indicator
            if (this.pagination_component) {
                this.pagination_component.show_loading();
            }

            // Apply original filters and handle the promise
            const result = original_apply_filters.call(this);

            // Handle both promise and non-promise returns
            if (result && typeof result.then === 'function') {
                return result.then(function (data) {
                    self.handle_filter_applied();
                    return data;
                }).catch(function (error) {
                    self.handle_filter_error(error);
                    throw error;
                });
            } else {
                // Synchronous call
                setTimeout(() => {
                    self.handle_filter_applied();
                }, 100);
                return result;
            }
        };

        frappe.views.ListView.prototype.handle_filter_applied = function () {
            // Hide loading indicator
            if (this.pagination_component) {
                this.pagination_component.hide_loading();

                // Update total records count
                this.pagination_component.update_total_records(this.total_count || 0);
            }
        };

        frappe.views.ListView.prototype.handle_filter_error = function (error) {
            // Hide loading indicator
            if (this.pagination_component) {
                this.pagination_component.hide_loading();
            }

            // Show error message
            column_management.enhanced_data_loader.handle_loading_error(
                error,
                this.$result
            );
        };

        // Override set_filter to reset pagination
        const original_set_filter = frappe.views.ListView.prototype.set_filter;

        frappe.views.ListView.prototype.set_filter = function (fieldname, operator, value) {
            // Reset pagination when setting new filter
            if (this.pagination_component) {
                this.pagination_component.reset_to_first_page();
            }

            return original_set_filter.call(this, fieldname, operator, value);
        };

        // Override clear_filters to reset pagination
        const original_clear_filters = frappe.views.ListView.prototype.clear_filters;

        frappe.views.ListView.prototype.clear_filters = function () {
            // Reset pagination when clearing filters
            if (this.pagination_component) {
                this.pagination_component.reset_to_first_page();
            }

            return original_clear_filters.call(this);
        };

        // Override toggle_filter to reset pagination
        const original_toggle_filter = frappe.views.ListView.prototype.toggle_filter;

        if (original_toggle_filter) {
            frappe.views.ListView.prototype.toggle_filter = function (fieldname, operator, value) {
                // Reset pagination when toggling filter
                if (this.pagination_component) {
                    this.pagination_component.reset_to_first_page();
                }

                return original_toggle_filter.call(this, fieldname, operator, value);
            };
        }

        // Override remove_filter to reset pagination
        const original_remove_filter = frappe.views.ListView.prototype.remove_filter;

        if (original_remove_filter) {
            frappe.views.ListView.prototype.remove_filter = function (fieldname) {
                // Reset pagination when removing filter
                if (this.pagination_component) {
                    this.pagination_component.reset_to_first_page();
                }

                return original_remove_filter.call(this, fieldname);
            };
        }
    }
};

// Enhanced Data Loading with Pagination - Task 9.2
column_management.enhanced_data_loader = {
    load_paginated_data: function (doctype, filters, page, page_size, sort_by, sort_order) {
        return new Promise((resolve, reject) => {
            // Show loading indicators
            const loading_indicator = this.show_loading_indicator();

            frappe.call({
                method: 'column_management.api.enhanced_list.get_list_data',
                args: {
                    doctype: doctype,
                    filters: filters || {},
                    page: page || 1,
                    page_size: page_size || 20,
                    sort_by: sort_by || 'modified',
                    sort_order: sort_order || 'desc'
                },
                callback: function (r) {
                    loading_indicator.hide();

                    if (r.message && r.message.success) {
                        resolve({
                            data: r.message.data,
                            total_count: r.message.total_count,
                            page_info: r.message.page_info
                        });
                    } else {
                        reject(new Error(r.message?.error || 'Failed to load data'));
                    }
                },
                error: function (err) {
                    loading_indicator.hide();
                    reject(err);
                }
            });
        });
    },

    show_loading_indicator: function () {
        const $indicator = $(`
            <div class="pagination-data-loading" style="
                position: fixed;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                background: rgba(0, 0, 0, 0.8);
                color: white;
                padding: 15px 20px;
                border-radius: 4px;
                z-index: 9999;
                display: flex;
                align-items: center;
                gap: 10px;
            ">
                <i class="fa fa-spinner fa-spin"></i>
                ${__('Loading data...')}
            </div>
        `);

        $('body').append($indicator);

        return {
            hide: function () {
                $indicator.remove();
            }
        };
    },

    handle_loading_error: function (error, container) {
        const $error = $(`
            <div class="pagination-error-message" style="
                padding: 20px;
                text-align: center;
                color: #dc3545;
                background: #f8d7da;
                border: 1px solid #f5c6cb;
                border-radius: 4px;
                margin: 10px 0;
            ">
                <i class="fa fa-exclamation-triangle"></i>
                <p style="margin: 8px 0 0 0;">${error.message || __('Failed to load data')}</p>
                <button class="btn btn-sm btn-outline-danger retry-load" style="margin-top: 10px;">
                    <i class="fa fa-refresh"></i> ${__('Retry')}
                </button>
            </div>
        `);

        if (container) {
            container.html($error);

            $error.find('.retry-load').on('click', function () {
                // Trigger reload
                if (cur_list && cur_list.refresh) {
                    cur_list.refresh();
                }
            });
        }

        // Show error notification
        frappe.show_alert({
            message: error.message || __('Failed to load data'),
            indicator: 'red'
        });
    }
};

// Initialize pagination filter integration
$(document).ready(function () {
    column_management.init_pagination_filter_integration();
});
// Initialize dynamic filtering system - Task 10.1
column_management.init_dynamic_filtering = function() {
    // Initialize DynamicFilterComponent
    column_management.components.DynamicFilter = class DynamicFilter {
        constructor(options) {
            this.doctype = options.doctype;
            this.container = options.container;
            this.availableFields = options.availableFields || [];
            this.activeFilters = options.activeFilters || [];
            this.savedFilters = options.savedFilters || [];
            this.callbacks = options.callbacks || {};
            
            // Filter state
            this.filterConditions = [];
            this.nextConditionId = 1;
            
            // Field operators mapping
            this.fieldOperators = {
                'Data': ['=', '!=', 'like', 'not like', 'in', 'not in', 'is', 'is not'],
                'Text': ['=', '!=', 'like', 'not like', 'in', 'not in', 'is', 'is not'],
                'Link': ['=', '!=', 'like', 'not like', 'in', 'not in', 'is', 'is not'],
                'Select': ['=', '!=', 'in', 'not in', 'is', 'is not'],
                'Int': ['=', '!=', '>', '<', '>=', '<=', 'between', 'in', 'not in', 'is', 'is not'],
                'Float': ['=', '!=', '>', '<', '>=', '<=', 'between', 'in', 'not in', 'is', 'is not'],
                'Currency': ['=', '!=', '>', '<', '>=', '<=', 'between', 'in', 'not in', 'is', 'is not'],
                'Date': ['=', '!=', '>', '<', '>=', '<=', 'between', 'is', 'is not'],
                'Datetime': ['=', '!=', '>', '<', '>=', '<=', 'between', 'is', 'is not'],
                'Time': ['=', '!=', '>', '<', '>=', '<=', 'between', 'is', 'is not'],
                'Check': ['=', '!=', 'is', 'is not'],
                'Small Text': ['=', '!=', 'like', 'not like', 'in', 'not in', 'is', 'is not'],
                'Long Text': ['=', '!=', 'like', 'not like', 'in', 'not in', 'is', 'is not'],
                'Code': ['=', '!=', 'like', 'not like', 'in', 'not in', 'is', 'is not'],
                'Table': ['is', 'is not'],
                'Attach': ['=', '!=', 'like', 'not like', 'is', 'is not'],
                'Attach Image': ['=', '!=', 'like', 'not like', 'is', 'is not']
            };
            
            this.init();
        }
        
        init() {
            this.render();
            this.bind_events();
            this.load_active_filters();
        }
        
        render() {
            let html = `
                <div class="dynamic-filter-component">
                    <div class="filter-header">
                        <div class="filter-controls">
                            <button class="btn btn-primary btn-sm add-condition">
                                <i class="fa fa-plus"></i> ${__('Add Condition')}
                            </button>
                            <button class="btn btn-default btn-sm clear-all">
                                <i class="fa fa-times"></i> ${__('Clear All')}
                            </button>
                            <div class="filter-presets-dropdown dropdown">
                                <button class="btn btn-default btn-sm dropdown-toggle" data-toggle="dropdown">
                                    <i class="fa fa-bookmark"></i> ${__('Saved Filters')}
                                    <span class="caret"></span>
                                </button>
                                <ul class="dropdown-menu">
                                    ${this.render_saved_filters_menu()}
                                </ul>
                            </div>
                            <button class="btn btn-success btn-sm save-filter">
                                <i class="fa fa-save"></i> ${__('Save Filter')}
                            </button>
                        </div>
                        <div class="filter-indicators">
                            ${this.render_active_filters()}
                        </div>
                    </div>
                    <div class="filter-conditions">
                        ${this.render_filter_conditions()}
                    </div>
                </div>
            `;
            
            this.container.html(html);
        }
        
        render_saved_filters_menu() {
            if (this.savedFilters.length === 0) {
                return `<li><a class="disabled">${__('No saved filters')}</a></li>`;
            }
            
            let html = '';
            this.savedFilters.forEach(filter => {
                html += `
                    <li>
                        <a href="#" class="load-saved-filter" data-filter-id="${filter.id}">
                            <i class="fa fa-filter"></i> ${filter.name}
                            ${filter.is_public ? '<i class="fa fa-globe text-muted"></i>' : ''}
                        </a>
                    </li>
                `;
            });
            
            html += `
                <li class="divider"></li>
                <li><a href="#" class="manage-saved-filters"><i class="fa fa-cog"></i> ${__('Manage Filters')}</a></li>
            `;
            
            return html;
        }
        
        render_active_filters() {
            if (this.filterConditions.length === 0) {
                return `<div class="empty-filters">${__('No active filters')}</div>`;
            }
            
            let html = '<div class="active-filters">';
            
            this.filterConditions.forEach((condition, index) => {
                const field = this.availableFields.find(f => f.fieldname === condition.fieldname);
                const fieldLabel = field ? field.label : condition.fieldname;
                
                let valueText = condition.value;
                if (Array.isArray(condition.value)) {
                    valueText = condition.value.join(', ');
                }
                
                html += `
                    <div class="filter-indicator">
                        ${index > 0 ? `<span class="filter-logic">${condition.logic || 'AND'}</span>` : ''}
                        <span class="filter-text">
                            ${fieldLabel} ${condition.operator} ${valueText}
                        </span>
                        <button class="remove-filter" data-condition-id="${condition.id}">
                            <i class="fa fa-times"></i>
                        </button>
                    </div>
                `;
            });
            
            html += '</div>';
            return html;
        }
        
        render_filter_conditions() {
            if (this.filterConditions.length === 0) {
                return `
                    <div class="empty-filters">
                        <i class="fa fa-filter fa-2x"></i>
                        <p>${__('No filter conditions added yet')}</p>
                        <small>${__('Click "Add Condition" to start filtering')}</small>
                    </div>
                `;
            }
            
            let html = '<div class="filter-conditions-list">';
            
            this.filterConditions.forEach((condition, index) => {
                html += this.render_single_condition(condition, index);
            });
            
            html += '</div>';
            return html;
        }
        
        render_single_condition(condition, index) {
            const field = this.availableFields.find(f => f.fieldname === condition.fieldname);
            const operators = field ? this.fieldOperators[field.fieldtype] || this.fieldOperators['Data'] : this.fieldOperators['Data'];
            
            return `
                <div class="filter-condition" data-condition-id="${condition.id}">
                    <div class="filter-row">
                        ${index > 0 ? this.render_logic_selector(condition) : ''}
                        ${this.render_field_selector(condition)}
                        ${this.render_operator_selector(condition, operators)}
                        ${this.render_value_input(condition, field)}
                        <div class="filter-actions">
                            <button class="btn btn-danger btn-xs remove-condition" data-condition-id="${condition.id}">
                                <i class="fa fa-times"></i>
                            </button>
                        </div>
                    </div>
                </div>
            `;
        }
        
        render_logic_selector(condition) {
            return `
                <div class="filter-logic">
                    <select class="form-control logic-selector" data-condition-id="${condition.id}">
                        <option value="AND" ${condition.logic === 'AND' ? 'selected' : ''}>${__('AND')}</option>
                        <option value="OR" ${condition.logic === 'OR' ? 'selected' : ''}>${__('OR')}</option>
                    </select>
                </div>
            `;
        }
        
        render_field_selector(condition) {
            let options = '<option value="">' + __('Select Field') + '</option>';
            
            this.availableFields.forEach(field => {
                const selected = condition.fieldname === field.fieldname ? 'selected' : '';
                options += `<option value="${field.fieldname}" ${selected}>${field.label} (${field.fieldtype})</option>`;
            });
            
            return `
                <div class="filter-field">
                    <select class="form-control field-selector" data-condition-id="${condition.id}">
                        ${options}
                    </select>
                </div>
            `;
        }
        
        render_operator_selector(condition, operators) {
            let options = '<option value="">' + __('Select Operator') + '</option>';
            
            operators.forEach(op => {
                const selected = condition.operator === op ? 'selected' : '';
                const label = this.get_operator_label(op);
                options += `<option value="${op}" ${selected}>${label}</option>`;
            });
            
            return `
                <div class="filter-operator">
                    <select class="form-control operator-selector" data-condition-id="${condition.id}">
                        ${options}
                    </select>
                </div>
            `;
        }
        
        render_value_input(condition, field) {
            if (!field || !condition.operator) {
                return `
                    <div class="filter-value">
                        <input type="text" class="form-control value-input" disabled 
                               placeholder="${__('Select field and operator first')}" />
                    </div>
                `;
            }
            
            // Handle special operators
            if (['is', 'is not'].includes(condition.operator)) {
                return `
                    <div class="filter-value">
                        <select class="form-control value-input" data-condition-id="${condition.id}">
                            <option value="null" ${condition.value === 'null' ? 'selected' : ''}>${__('Empty/Null')}</option>
                            <option value="not null" ${condition.value === 'not null' ? 'selected' : ''}>${__('Not Empty')}</option>
                        </select>
                    </div>
                `;
            }
            
            if (condition.operator === 'between') {
                const values = Array.isArray(condition.value) ? condition.value : ['', ''];
                return `
                    <div class="filter-value">
                        <div class="input-group">
                            <input type="${this.get_input_type(field.fieldtype)}" 
                                   class="form-control value-input-from" 
                                   data-condition-id="${condition.id}"
                                   value="${values[0] || ''}" 
                                   placeholder="${__('From')}" />
                            <span class="input-group-addon">${__('to')}</span>
                            <input type="${this.get_input_type(field.fieldtype)}" 
                                   class="form-control value-input-to" 
                                   data-condition-id="${condition.id}"
                                   value="${values[1] || ''}" 
                                   placeholder="${__('To')}" />
                        </div>
                    </div>
                `;
            }
            
            if (['in', 'not in'].includes(condition.operator)) {
                const value = Array.isArray(condition.value) ? condition.value.join(', ') : condition.value || '';
                return `
                    <div class="filter-value">
                        <input type="text" class="form-control value-input" 
                               data-condition-id="${condition.id}"
                               value="${value}" 
                               placeholder="${__('Enter values separated by comma')}" />
                    </div>
                `;
            }
            
            // Handle different field types
            if (field.fieldtype === 'Check') {
                return `
                    <div class="filter-value">
                        <div class="checkbox-wrapper">
                            <label>
                                <input type="checkbox" class="value-input" 
                                       data-condition-id="${condition.id}"
                                       ${condition.value ? 'checked' : ''} />
                                ${__('Checked')}
                            </label>
                        </div>
                    </div>
                `;
            }
            
            if (field.fieldtype === 'Link') {
                return `
                    <div class="filter-value">
                        <div class="link-field-wrapper">
                            <input type="text" class="form-control link-input value-input" 
                                   data-condition-id="${condition.id}"
                                   data-doctype="${field.options || ''}"
                                   value="${condition.value || ''}" 
                                   placeholder="${__('Search or enter value')}" />
                            <button class="btn btn-default link-search-btn" type="button">
                                <i class="fa fa-search"></i>
                            </button>
                            <div class="link-autocomplete-dropdown" style="display: none;"></div>
                        </div>
                    </div>
                `;
            }
            
            if (field.fieldtype === 'Select' && field.options) {
                const options = field.options.split('\n').filter(opt => opt.trim());
                let selectOptions = '<option value="">' + __('Select Value') + '</option>';
                
                options.forEach(opt => {
                    const selected = condition.value === opt ? 'selected' : '';
                    selectOptions += `<option value="${opt}" ${selected}>${opt}</option>`;
                });
                
                return `
                    <div class="filter-value">
                        <select class="form-control value-input" data-condition-id="${condition.id}">
                            ${selectOptions}
                        </select>
                    </div>
                `;
            }
            
            // Default input
            return `
                <div class="filter-value">
                    <input type="${this.get_input_type(field.fieldtype)}" 
                           class="form-control value-input" 
                           data-condition-id="${condition.id}"
                           value="${condition.value || ''}" 
                           placeholder="${__('Enter value')}" />
                </div>
            `;
        }
        
        get_input_type(fieldtype) {
            const typeMap = {
                'Int': 'number',
                'Float': 'number',
                'Currency': 'number',
                'Date': 'date',
                'Datetime': 'datetime-local',
                'Time': 'time',
                'Email': 'email',
                'Phone': 'tel',
                'URL': 'url'
            };
            
            return typeMap[fieldtype] || 'text';
        }
        
        get_operator_label(operator) {
            const labels = {
                '=': __('Equals'),
                '!=': __('Not Equals'),
                '>': __('Greater Than'),
                '<': __('Less Than'),
                '>=': __('Greater Than or Equal'),
                '<=': __('Less Than or Equal'),
                'like': __('Contains'),
                'not like': __('Does Not Contain'),
                'in': __('In'),
                'not in': __('Not In'),
                'between': __('Between'),
                'is': __('Is'),
                'is not': __('Is Not')
            };
            
            return labels[operator] || operator;
        }
        
        bind_events() {
            const self = this;
            
            // Add condition
            this.container.on('click', '.add-condition', function() {
                self.add_condition();
            });
            
            // Clear all conditions
            this.container.on('click', '.clear-all', function() {
                self.clear_all_conditions();
            });
            
            // Remove single condition
            this.container.on('click', '.remove-condition', function() {
                const conditionId = parseInt($(this).data('condition-id'));
                self.remove_condition(conditionId);
            });
            
            // Remove from indicator
            this.container.on('click', '.remove-filter', function() {
                const conditionId = parseInt($(this).data('condition-id'));
                self.remove_condition(conditionId);
            });
            
            // Field selection change
            this.container.on('change', '.field-selector', function() {
                const conditionId = parseInt($(this).data('condition-id'));
                const fieldname = $(this).val();
                self.update_condition_field(conditionId, fieldname);
            });
            
            // Operator selection change
            this.container.on('change', '.operator-selector', function() {
                const conditionId = parseInt($(this).data('condition-id'));
                const operator = $(this).val();
                self.update_condition_operator(conditionId, operator);
            });
            
            // Logic selection change
            this.container.on('change', '.logic-selector', function() {
                const conditionId = parseInt($(this).data('condition-id'));
                const logic = $(this).val();
                self.update_condition_logic(conditionId, logic);
            });
            
            // Value input changes
            this.container.on('change keyup', '.value-input', function() {
                const conditionId = parseInt($(this).data('condition-id'));
                let value = $(this).val();
                
                // Handle checkbox
                if ($(this).is(':checkbox')) {
                    value = $(this).is(':checked');
                }
                
                self.update_condition_value(conditionId, value);
            });
            
            // Between value inputs
            this.container.on('change keyup', '.value-input-from, .value-input-to', function() {
                const conditionId = parseInt($(this).data('condition-id'));
                const fromValue = self.container.find(`.value-input-from[data-condition-id="${conditionId}"]`).val();
                const toValue = self.container.find(`.value-input-to[data-condition-id="${conditionId}"]`).val();
                self.update_condition_value(conditionId, [fromValue, toValue]);
            });
            
            // Link field search
            this.container.on('click', '.link-search-btn', function() {
                const $input = $(this).siblings('.link-input');
                const conditionId = parseInt($input.data('condition-id'));
                const doctype = $input.data('doctype');
                self.show_link_selector(conditionId, doctype, $input);
            });
            
            // Link field autocomplete
            this.container.on('keyup', '.link-input', function() {
                const $input = $(this);
                const doctype = $input.data('doctype');
                const query = $input.val();
                
                if (query.length >= 2) {
                    self.show_link_autocomplete($input, doctype, query);
                } else {
                    $input.siblings('.link-autocomplete-dropdown').hide();
                }
            });
            
            // Autocomplete item selection
            this.container.on('click', '.autocomplete-item', function() {
                const value = $(this).data('value');
                const $input = $(this).closest('.link-field-wrapper').find('.link-input');
                const conditionId = parseInt($input.data('condition-id'));
                
                $input.val(value);
                self.update_condition_value(conditionId, value);
                $(this).parent().hide();
            });
            
            // Save filter
            this.container.on('click', '.save-filter', function() {
                self.show_save_filter_dialog();
            });
            
            // Load saved filter
            this.container.on('click', '.load-saved-filter', function(e) {
                e.preventDefault();
                const filterId = $(this).data('filter-id');
                self.load_saved_filter(filterId);
            });
            
            // Manage saved filters
            this.container.on('click', '.manage-saved-filters', function(e) {
                e.preventDefault();
                self.show_manage_filters_dialog();
            });
        }
        
        add_condition() {
            const condition = {
                id: this.nextConditionId++,
                fieldname: '',
                operator: '',
                value: '',
                logic: 'AND'
            };
            
            this.filterConditions.push(condition);
            this.render_conditions_section();
            this.validate_and_apply_filters();
        }
        
        remove_condition(conditionId) {
            this.filterConditions = this.filterConditions.filter(c => c.id !== conditionId);
            this.render_conditions_section();
            this.validate_and_apply_filters();
        }
        
        clear_all_conditions() {
            this.filterConditions = [];
            this.render_conditions_section();
            this.validate_and_apply_filters();
        }
        
        update_condition_field(conditionId, fieldname) {
            const condition = this.filterConditions.find(c => c.id === conditionId);
            if (condition) {
                condition.fieldname = fieldname;
                condition.operator = ''; // Reset operator when field changes
                condition.value = ''; // Reset value when field changes
                
                // Re-render the specific condition
                this.render_single_condition_in_place(condition);
                this.validate_and_apply_filters();
            }
        }
        
        update_condition_operator(conditionId, operator) {
            const condition = this.filterConditions.find(c => c.id === conditionId);
            if (condition) {
                condition.operator = operator;
                condition.value = ''; // Reset value when operator changes
                
                // Re-render the specific condition
                this.render_single_condition_in_place(condition);
                this.validate_and_apply_filters();
            }
        }
        
        update_condition_logic(conditionId, logic) {
            const condition = this.filterConditions.find(c => c.id === conditionId);
            if (condition) {
                condition.logic = logic;
                this.render_indicators_section();
                this.validate_and_apply_filters();
            }
        }
        
        update_condition_value(conditionId, value) {
            const condition = this.filterConditions.find(c => c.id === conditionId);
            if (condition) {
                condition.value = value;
                this.render_indicators_section();
                this.validate_and_apply_filters();
            }
        }
        
        render_single_condition_in_place(condition) {
            const index = this.filterConditions.findIndex(c => c.id === condition.id);
            const $conditionElement = this.container.find(`.filter-condition[data-condition-id="${condition.id}"]`);
            const newHtml = this.render_single_condition(condition, index);
            $conditionElement.replaceWith(newHtml);
        }
        
        render_conditions_section() {
            this.container.find('.filter-conditions').html(this.render_filter_conditions());
        }
        
        render_indicators_section() {
            this.container.find('.filter-indicators').html(this.render_active_filters());
        }
        
        validate_and_apply_filters() {
            const validConditions = this.filterConditions.filter(condition => {
                return condition.fieldname && condition.operator && 
                       (condition.value !== '' || ['is', 'is not'].includes(condition.operator));
            });
            
            if (this.callbacks.onFilterChange) {
                this.callbacks.onFilterChange(validConditions);
            }
        }
        
        show_link_selector(conditionId, doctype, $input) {
            if (!doctype) return;
            
            frappe.ui.form.make_quick_entry(doctype, (doc) => {
                $input.val(doc.name);
                this.update_condition_value(conditionId, doc.name);
            });
        }
        
        show_link_autocomplete($input, doctype, query) {
            if (!doctype) return;
            
            frappe.call({
                method: 'frappe.desk.search.search_link',
                args: {
                    doctype: doctype,
                    txt: query,
                    page_length: 10
                },
                callback: (r) => {
                    if (r.results) {
                        let html = '';
                        r.results.forEach(result => {
                            html += `
                                <div class="autocomplete-item" data-value="${result.value}">
                                    ${result.label || result.value}
                                </div>
                            `;
                        });
                        
                        const $dropdown = $input.siblings('.link-autocomplete-dropdown');
                        $dropdown.html(html).show();
                    }
                }
            });
        }
        
        show_save_filter_dialog() {
            if (this.filterConditions.length === 0) {
                frappe.msgprint(__('No filter conditions to save'));
                return;
            }
            
            const dialog = new frappe.ui.Dialog({
                title: __('Save Filter'),
                fields: [
                    {
                        fieldtype: 'Data',
                        fieldname: 'filter_name',
                        label: __('Filter Name'),
                        reqd: 1
                    },
                    {
                        fieldtype: 'Check',
                        fieldname: 'is_public',
                        label: __('Make Public'),
                        description: __('Allow other users to use this filter')
                    }
                ],
                primary_action_label: __('Save'),
                primary_action: (values) => {
                    this.save_filter(values.filter_name, values.is_public);
                    dialog.hide();
                }
            });
            
            dialog.show();
        }
        
        save_filter(name, isPublic) {
            const filterData = {
                name: name,
                doctype: this.doctype,
                conditions: this.filterConditions,
                is_public: isPublic || false
            };
            
            if (this.callbacks.onFilterSave) {
                this.callbacks.onFilterSave(filterData);
            }
        }
        
        load_saved_filter(filterId) {
            const savedFilter = this.savedFilters.find(f => f.id === filterId);
            if (savedFilter && savedFilter.conditions) {
                this.filterConditions = savedFilter.conditions.map(condition => ({
                    ...condition,
                    id: this.nextConditionId++
                }));
                
                this.render_conditions_section();
                this.render_indicators_section();
                this.validate_and_apply_filters();
                
                frappe.show_alert({
                    message: __('Filter "{0}" loaded', [savedFilter.name]),
                    indicator: 'green'
                });
            }
        }
        
        show_manage_filters_dialog() {
            const dialog = new frappe.ui.Dialog({
                title: __('Manage Saved Filters'),
                fields: [
                    {
                        fieldtype: 'HTML',
                        fieldname: 'filters_html',
                        options: '<div class="saved-filters-manager">Loading...</div>'
                    }
                ],
                size: 'large'
            });
            
            dialog.show();
            
            // Render saved filters management interface
            const $container = dialog.$wrapper.find('.saved-filters-manager');
            this.render_saved_filters_manager($container);
        }
        
        render_saved_filters_manager($container) {
            let html = '';
            
            if (this.savedFilters.length === 0) {
                html = `
                    <div class="empty-config">
                        <i class="fa fa-bookmark fa-2x"></i>
                        <p>${__('No saved filters found')}</p>
                    </div>
                `;
            } else {
                this.savedFilters.forEach(filter => {
                    html += `
                        <div class="saved-filter-item">
                            <div class="filter-info">
                                <h6>${filter.name}</h6>
                                <small>
                                    ${filter.conditions.length} ${__('conditions')}
                                    ${filter.is_public ? '• ' + __('Public') : '• ' + __('Private')}
                                    ${filter.created_by ? '• ' + __('by {0}', [filter.created_by]) : ''}
                                </small>
                            </div>
                            <div class="filter-actions">
                                <button class="btn btn-primary btn-xs load-filter" data-filter-id="${filter.id}">
                                    ${__('Load')}
                                </button>
                                <button class="btn btn-default btn-xs edit-filter" data-filter-id="${filter.id}">
                                    ${__('Edit')}
                                </button>
                                <button class="btn btn-danger btn-xs delete-filter" data-filter-id="${filter.id}">
                                    ${__('Delete')}
                                </button>
                            </div>
                        </div>
                    `;
                });
            }
            
            $container.html(html);
            
            // Bind events for filter management
            $container.on('click', '.load-filter', (e) => {
                const filterId = $(e.target).data('filter-id');
                this.load_saved_filter(filterId);
                $container.closest('.modal').modal('hide');
            });
            
            $container.on('click', '.delete-filter', (e) => {
                const filterId = $(e.target).data('filter-id');
                this.delete_saved_filter(filterId, $container);
            });
        }
        
        delete_saved_filter(filterId, $container) {
            frappe.confirm(__('Are you sure you want to delete this filter?'), () => {
                if (this.callbacks.onFilterDelete) {
                    this.callbacks.onFilterDelete(filterId);
                }
                
                // Remove from local array
                this.savedFilters = this.savedFilters.filter(f => f.id !== filterId);
                
                // Re-render
                this.render_saved_filters_manager($container);
                this.render(); // Update dropdown menu
                
                frappe.show_alert({
                    message: __('Filter deleted'),
                    indicator: 'red'
                });
            });
        }
        
        load_active_filters() {
            // Load any existing active filters
            if (this.activeFilters && this.activeFilters.length > 0) {
                this.filterConditions = this.activeFilters.map(filter => ({
                    id: this.nextConditionId++,
                    fieldname: filter.fieldname,
                    operator: filter.operator,
                    value: filter.value,
                    logic: filter.logic || 'AND'
                }));
                
                this.render_conditions_section();
                this.render_indicators_section();
            }
        }
        
        get_filter_conditions() {
            return this.filterConditions.filter(condition => {
                return condition.fieldname && condition.operator && 
                       (condition.value !== '' || ['is', 'is not'].includes(condition.operator));
            });
        }
        
        set_filter_conditions(conditions) {
            this.filterConditions = conditions.map(condition => ({
                ...condition,
                id: this.nextConditionId++
            }));
            
            this.render_conditions_section();
            this.render_indicators_section();
        }
        
        clear_filters() {
            this.clear_all_conditions();
        }
    };
};