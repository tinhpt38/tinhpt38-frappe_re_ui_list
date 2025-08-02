// List View Applier - Apply column configuration to List View
frappe.provide('column_management.listViewApplier');

column_management.listViewApplier = {
    currentDoctype: null,
    currentUser: null,
    columnConfig: null,
    
    // Initialize list view applier
    init: function(doctype) {
        this.currentDoctype = doctype;
        this.currentUser = frappe.user ? frappe.user.name : 'Administrator';
        console.log('🔧 Initializing list view applier for:', doctype);
        this.loadAndApplyConfig();
    },
    
    // Load and apply column configuration
    loadAndApplyConfig: function() {
        console.log('📡 Loading column config for list view...');
        
        frappe.call({
            method: 'column_management.api.column_manager.get_column_config',
            args: {
                doctype: this.currentDoctype
            },
            callback: (r) => {
                console.log('📡 Config response:', r);
                if (r.message && r.message.success) {
                    this.columnConfig = r.message.data;
                    this.applyColumnConfig();
                } else {
                    console.log('⚠️ No custom config found, using defaults');
                }
            },
            error: (r) => {
                console.log('❌ Error loading config:', r);
            }
        });
    },
    
    // Apply column configuration to list view
    applyColumnConfig: function() {
        if (!this.columnConfig || !this.columnConfig.selected_columns) {
            console.log('⚠️ No column config to apply');
            return;
        }
        
        console.log('🎨 Applying column config...');
        
        // Wait for list view to be ready
        this.waitForListView(() => {
            this.applyColumnVisibility();
            this.applyColumnWidth();
            this.applyColumnOrder();
            this.applyPinnedColumns();
            this.updateListHeader();
        });
    },
    
    // Wait for list view to be ready
    waitForListView: function(callback) {
        let attempts = 0;
        const maxAttempts = 50; // 5 seconds
        
        const checkListView = () => {
            attempts++;
            
            // Check if list view elements exist
            const listView = $('.list-view-container, .list-container, .list-view');
            const listHeader = $('.list-header, .list-view-container .list-header');
            const listBody = $('.list-body, .list-view-container .list-body');
            
            if (listView.length > 0 && listHeader.length > 0) {
                console.log('✅ List view ready, applying config...');
                callback();
            } else if (attempts < maxAttempts) {
                console.log(`⏳ Waiting for list view... (${attempts}/${maxAttempts})`);
                setTimeout(checkListView, 100);
            } else {
                console.log('❌ List view not found after timeout');
            }
        };
        
        checkListView();
    },
    
    // Apply column visibility
    applyColumnVisibility: function() {
        const columns = this.columnConfig.selected_columns;
        
        columns.forEach((column, index) => {
            if (column.visible === 0) {
                // Hide column
                this.hideColumn(column.fieldname);
            } else {
                // Show column
                this.showColumn(column.fieldname);
            }
        });
        
        console.log('✅ Column visibility applied');
    },
    
    // Apply column width
    applyColumnWidth: function() {
        const columns = this.columnConfig.selected_columns;
        
        columns.forEach((column) => {
            if (column.width) {
                this.setColumnWidth(column.fieldname, column.width);
            }
        });
        
        console.log('✅ Column widths applied');
    },
    
    // Apply column order
    applyColumnOrder: function() {
        const columns = this.columnConfig.selected_columns;
        
        // Sort by order
        columns.sort((a, b) => (a.order || 0) - (b.order || 0));
        
        // Reorder columns
        columns.forEach((column, index) => {
            this.moveColumn(column.fieldname, index);
        });
        
        console.log('✅ Column order applied');
    },
    
    // Apply pinned columns
    applyPinnedColumns: function() {
        const columns = this.columnConfig.selected_columns;
        
        columns.forEach((column) => {
            if (column.pinned) {
                this.pinColumn(column.fieldname, column.pinned);
            } else {
                this.unpinColumn(column.fieldname);
            }
        });
        
        console.log('✅ Pinned columns applied');
    },
    
    // Hide column
    hideColumn: function(fieldname) {
        const selector = `[data-fieldname="${fieldname}"], .list-row-header [data-fieldname="${fieldname}"], .list-row [data-fieldname="${fieldname}"]`;
        $(selector).hide();
    },
    
    // Show column
    showColumn: function(fieldname) {
        const selector = `[data-fieldname="${fieldname}"], .list-row-header [data-fieldname="${fieldname}"], .list-row [data-fieldname="${fieldname}"]`;
        $(selector).show();
    },
    
    // Set column width
    setColumnWidth: function(fieldname, width) {
        const selector = `[data-fieldname="${fieldname}"], .list-row-header [data-fieldname="${fieldname}"], .list-row [data-fieldname="${fieldname}"]`;
        $(selector).css('width', width + 'px').css('min-width', width + 'px');
    },
    
    // Move column
    moveColumn: function(fieldname, position) {
        const headerCell = $(`.list-row-header [data-fieldname="${fieldname}"]`);
        const dataCells = $(`.list-row [data-fieldname="${fieldname}"]`);
        
        if (headerCell.length > 0) {
            // Move header cell
            const headerRow = headerCell.closest('tr');
            const targetPosition = headerRow.children().eq(position);
            if (targetPosition.length > 0) {
                headerCell.insertBefore(targetPosition);
            }
        }
        
        // Move data cells
        dataCells.each(function() {
            const row = $(this).closest('tr');
            const targetPosition = row.children().eq(position);
            if (targetPosition.length > 0) {
                $(this).insertBefore(targetPosition);
            }
        });
    },
    
    // Pin column
    pinColumn: function(fieldname, position) {
        const cells = $(`[data-fieldname="${fieldname}"]`);
        
        cells.each(function() {
            const $cell = $(this);
            if (position === 'left') {
                $cell.addClass('pinned-left');
            } else if (position === 'right') {
                $cell.addClass('pinned-right');
            }
        });
    },
    
    // Unpin column
    unpinColumn: function(fieldname) {
        const cells = $(`[data-fieldname="${fieldname}"]`);
        cells.removeClass('pinned-left pinned-right');
    },
    
    // Update list header
    updateListHeader: function() {
        const columns = this.columnConfig.selected_columns;
        
        // Update header text
        columns.forEach((column) => {
            const headerCell = $(`.list-row-header [data-fieldname="${column.fieldname}"]`);
            if (headerCell.length > 0) {
                headerCell.text(column.label || column.fieldname);
            }
        });
        
        console.log('✅ List header updated');
    },
    
    // Refresh list view
    refresh: function() {
        console.log('🔄 Refreshing list view...');
        
        // Trigger list view refresh
        if (cur_list && cur_list.refresh) {
            cur_list.refresh();
        } else {
            // Fallback: reload page
            location.reload();
        }
    },
    
    // Apply config after list view refresh
    applyAfterRefresh: function() {
        setTimeout(() => {
            this.loadAndApplyConfig();
        }, 1000);
    }
};

// Auto-apply when list view loads
$(document).ready(function() {
    // Check if we're on a list view
    if (typeof cur_list !== 'undefined' && cur_list && cur_list.doctype) {
        console.log('📋 List view detected, applying column config...');
        column_management.listViewApplier.init(cur_list.doctype);
    }
});

// Listen for list view changes
$(document).on('DOMNodeInserted', function(e) {
    const $target = $(e.target);
    
    // Check if list view container was added
    if ($target.hasClass('list-view-container') || 
        $target.hasClass('list-container') ||
        $target.find('.list-view-container').length > 0) {
        
        console.log('🔄 List view container detected, applying config...');
        setTimeout(() => {
            if (cur_list && cur_list.doctype) {
                column_management.listViewApplier.init(cur_list.doctype);
            }
        }, 500);
    }
});

// Global function to apply config
window.applyColumnConfig = function(doctype) {
    column_management.listViewApplier.init(doctype);
};

// Global function to refresh
window.refreshListView = function() {
    column_management.listViewApplier.refresh();
};

console.log('🎉 List View Applier loaded'); 