// List View Applier Debug Version
frappe.provide('column_management.listViewApplierDebug');

column_management.listViewApplierDebug = {
    currentDoctype: null,
    currentUser: null,
    columnConfig: null,
    
    // Initialize list view applier
    init: function(doctype) {
        this.currentDoctype = doctype;
        this.currentUser = frappe.user ? frappe.user.name : 'Administrator';
        console.log('🔧 [DEBUG] Initializing list view applier for:', doctype);
        this.loadAndApplyConfig();
    },
    
    // Load and apply column configuration
    loadAndApplyConfig: function() {
        console.log('📡 [DEBUG] Loading column config for list view...');
        
        frappe.call({
            method: 'column_management.api.column_manager.get_column_config',
            args: {
                doctype: this.currentDoctype
            },
            callback: (r) => {
                console.log('📡 [DEBUG] Config response:', r);
                if (r.message && r.message.success) {
                    this.columnConfig = r.message.data;
                    console.log('📋 [DEBUG] Column config loaded:', this.columnConfig);
                    this.applyColumnConfig();
                } else {
                    console.log('⚠️ [DEBUG] No custom config found, using defaults');
                }
            },
            error: (r) => {
                console.log('❌ [DEBUG] Error loading config:', r);
            }
        });
    },
    
    // Apply column configuration to list view
    applyColumnConfig: function() {
        if (!this.columnConfig || !this.columnConfig.selected_columns) {
            console.log('⚠️ [DEBUG] No column config to apply');
            return;
        }
        
        console.log('🎨 [DEBUG] Applying column config...');
        console.log('📋 [DEBUG] Selected columns:', this.columnConfig.selected_columns);
        
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
            const listHeader = $('.list-header, .list-view-container .list-header, .list-row-header');
            const listBody = $('.list-body, .list-view-container .list-body');
            
            console.log(`🔍 [DEBUG] Attempt ${attempts}: listView=${listView.length}, listHeader=${listHeader.length}, listBody=${listBody.length}`);
            
            if (listView.length > 0 && listHeader.length > 0) {
                console.log('✅ [DEBUG] List view ready, applying config...');
                callback();
            } else if (attempts < maxAttempts) {
                console.log(`⏳ [DEBUG] Waiting for list view... (${attempts}/${maxAttempts})`);
                setTimeout(checkListView, 100);
            } else {
                console.log('❌ [DEBUG] List view not found after timeout');
            }
        };
        
        checkListView();
    },
    
    // Apply column visibility
    applyColumnVisibility: function() {
        const columns = this.columnConfig.selected_columns;
        console.log('👁️ [DEBUG] Applying column visibility for', columns.length, 'columns');
        
        columns.forEach((column, index) => {
            console.log(`🔍 [DEBUG] Processing column: ${column.fieldname}, visible: ${column.visible}`);
            
            if (column.visible === 0) {
                // Hide column
                this.hideColumn(column.fieldname);
                console.log(`🙈 [DEBUG] Hiding column: ${column.fieldname}`);
            } else {
                // Show column
                this.showColumn(column.fieldname);
                console.log(`👁️ [DEBUG] Showing column: ${column.fieldname}`);
            }
        });
        
        console.log('✅ [DEBUG] Column visibility applied');
    },
    
    // Apply column width
    applyColumnWidth: function() {
        const columns = this.columnConfig.selected_columns;
        console.log('📏 [DEBUG] Applying column widths for', columns.length, 'columns');
        
        columns.forEach((column) => {
            if (column.width) {
                this.setColumnWidth(column.fieldname, column.width);
                console.log(`📏 [DEBUG] Set width for ${column.fieldname}: ${column.width}px`);
            }
        });
        
        console.log('✅ [DEBUG] Column widths applied');
    },
    
    // Apply column order
    applyColumnOrder: function() {
        const columns = this.columnConfig.selected_columns;
        console.log('📋 [DEBUG] Applying column order for', columns.length, 'columns');
        
        // Sort by order
        columns.sort((a, b) => (a.order || 0) - (b.order || 0));
        
        // Reorder columns
        columns.forEach((column, index) => {
            this.moveColumn(column.fieldname, index);
            console.log(`📋 [DEBUG] Move column ${column.fieldname} to position ${index}`);
        });
        
        console.log('✅ [DEBUG] Column order applied');
    },
    
    // Apply pinned columns
    applyPinnedColumns: function() {
        const columns = this.columnConfig.selected_columns;
        console.log('📌 [DEBUG] Applying pinned columns for', columns.length, 'columns');
        
        columns.forEach((column) => {
            if (column.pinned) {
                this.pinColumn(column.fieldname, column.pinned);
                console.log(`📌 [DEBUG] Pin column ${column.fieldname} to ${column.pinned}`);
            } else {
                this.unpinColumn(column.fieldname);
                console.log(`📌 [DEBUG] Unpin column ${column.fieldname}`);
            }
        });
        
        console.log('✅ [DEBUG] Pinned columns applied');
    },
    
    // Hide column
    hideColumn: function(fieldname) {
        const selectors = [
            `[data-fieldname="${fieldname}"]`,
            `.list-row-header [data-fieldname="${fieldname}"]`,
            `.list-row [data-fieldname="${fieldname}"]`,
            `th[data-fieldname="${fieldname}"]`,
            `td[data-fieldname="${fieldname}"]`,
            `.list-view-container [data-fieldname="${fieldname}"]`
        ];
        
        let hiddenCount = 0;
        selectors.forEach(selector => {
            const elements = $(selector);
            if (elements.length > 0) {
                elements.hide();
                hiddenCount += elements.length;
                console.log(`🙈 [DEBUG] Hidden ${elements.length} elements with selector: ${selector}`);
            }
        });
        
        console.log(`🙈 [DEBUG] Total hidden elements for ${fieldname}: ${hiddenCount}`);
    },
    
    // Show column
    showColumn: function(fieldname) {
        const selectors = [
            `[data-fieldname="${fieldname}"]`,
            `.list-row-header [data-fieldname="${fieldname}"]`,
            `.list-row [data-fieldname="${fieldname}"]`,
            `th[data-fieldname="${fieldname}"]`,
            `td[data-fieldname="${fieldname}"]`,
            `.list-view-container [data-fieldname="${fieldname}"]`
        ];
        
        let shownCount = 0;
        selectors.forEach(selector => {
            const elements = $(selector);
            if (elements.length > 0) {
                elements.show();
                shownCount += elements.length;
                console.log(`👁️ [DEBUG] Shown ${elements.length} elements with selector: ${selector}`);
            }
        });
        
        console.log(`👁️ [DEBUG] Total shown elements for ${fieldname}: ${shownCount}`);
    },
    
    // Set column width
    setColumnWidth: function(fieldname, width) {
        const selectors = [
            `[data-fieldname="${fieldname}"]`,
            `.list-row-header [data-fieldname="${fieldname}"]`,
            `.list-row [data-fieldname="${fieldname}"]`,
            `th[data-fieldname="${fieldname}"]`,
            `td[data-fieldname="${fieldname}"]`
        ];
        
        let styledCount = 0;
        selectors.forEach(selector => {
            const elements = $(selector);
            if (elements.length > 0) {
                elements.css('width', width + 'px').css('min-width', width + 'px');
                styledCount += elements.length;
                console.log(`📏 [DEBUG] Styled ${elements.length} elements with selector: ${selector}`);
            }
        });
        
        console.log(`📏 [DEBUG] Total styled elements for ${fieldname}: ${styledCount}`);
    },
    
    // Move column
    moveColumn: function(fieldname, position) {
        const headerCell = $(`.list-row-header [data-fieldname="${fieldname}"]`);
        const dataCells = $(`.list-row [data-fieldname="${fieldname}"]`);
        
        console.log(`📋 [DEBUG] Moving column ${fieldname} to position ${position}`);
        console.log(`📋 [DEBUG] Found ${headerCell.length} header cells, ${dataCells.length} data cells`);
        
        if (headerCell.length > 0) {
            // Move header cell
            const headerRow = headerCell.closest('tr');
            const targetPosition = headerRow.children().eq(position);
            if (targetPosition.length > 0) {
                headerCell.insertBefore(targetPosition);
                console.log(`📋 [DEBUG] Moved header cell for ${fieldname}`);
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
        
        console.log(`📋 [DEBUG] Moved data cells for ${fieldname}`);
    },
    
    // Pin column
    pinColumn: function(fieldname, position) {
        const cells = $(`[data-fieldname="${fieldname}"]`);
        
        console.log(`📌 [DEBUG] Pinning column ${fieldname} to ${position}`);
        console.log(`📌 [DEBUG] Found ${cells.length} cells to pin`);
        
        cells.each(function() {
            const $cell = $(this);
            if (position === 'left') {
                $cell.addClass('pinned-left');
            } else if (position === 'right') {
                $cell.addClass('pinned-right');
            }
        });
        
        console.log(`📌 [DEBUG] Pinned ${cells.length} cells for ${fieldname}`);
    },
    
    // Unpin column
    unpinColumn: function(fieldname) {
        const cells = $(`[data-fieldname="${fieldname}"]`);
        cells.removeClass('pinned-left pinned-right');
        console.log(`📌 [DEBUG] Unpinned ${cells.length} cells for ${fieldname}`);
    },
    
    // Update list header
    updateListHeader: function() {
        const columns = this.columnConfig.selected_columns;
        
        // Update header text
        columns.forEach((column) => {
            const headerCell = $(`.list-row-header [data-fieldname="${column.fieldname}"]`);
            if (headerCell.length > 0) {
                headerCell.text(column.label || column.fieldname);
                console.log(`📋 [DEBUG] Updated header for ${column.fieldname}: ${column.label}`);
            }
        });
        
        console.log('✅ [DEBUG] List header updated');
    },
    
    // Debug current list view structure
    debugListViewStructure: function() {
        console.log('🔍 [DEBUG] Current list view structure:');
        console.log('📋 [DEBUG] List view containers:', $('.list-view-container, .list-container, .list-view').length);
        console.log('📋 [DEBUG] List headers:', $('.list-header, .list-view-container .list-header, .list-row-header').length);
        console.log('📋 [DEBUG] List bodies:', $('.list-body, .list-view-container .list-body').length);
        console.log('📋 [DEBUG] All data-fieldname elements:', $('[data-fieldname]').length);
        
        // List all data-fieldname elements
        $('[data-fieldname]').each(function() {
            const fieldname = $(this).data('fieldname');
            const tagName = $(this).prop('tagName');
            const classes = $(this).attr('class');
            console.log(`📋 [DEBUG] Element: ${tagName}, fieldname: ${fieldname}, classes: ${classes}`);
        });
    },
    
    // Refresh list view
    refresh: function() {
        console.log('🔄 [DEBUG] Refreshing list view...');
        
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
        console.log('📋 [DEBUG] List view detected, applying column config...');
        column_management.listViewApplierDebug.init(cur_list.doctype);
    }
});

// Listen for list view changes
$(document).on('DOMNodeInserted', function(e) {
    const $target = $(e.target);
    
    // Check if list view container was added
    if ($target.hasClass('list-view-container') || 
        $target.hasClass('list-container') ||
        $target.find('.list-view-container').length > 0) {
        
        console.log('🔄 [DEBUG] List view container detected, applying config...');
        setTimeout(() => {
            if (cur_list && cur_list.doctype) {
                column_management.listViewApplierDebug.init(cur_list.doctype);
            }
        }, 500);
    }
});

// Global function to apply config
window.applyColumnConfigDebug = function(doctype) {
    column_management.listViewApplierDebug.init(doctype);
};

// Global function to debug list view structure
window.debugListViewStructure = function() {
    column_management.listViewApplierDebug.debugListViewStructure();
};

console.log('🎉 [DEBUG] List View Applier Debug loaded'); 