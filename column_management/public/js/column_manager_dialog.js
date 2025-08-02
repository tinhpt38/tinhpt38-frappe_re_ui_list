// Column Manager Dialog - Complete Implementation
frappe.provide('column_management.dialog');

column_management.dialog = {
    currentDoctype: null,
    currentUser: null,
    availableColumns: [],
    selectedColumns: [],
    dialog: null,
    
    // Initialize dialog
    init: function(doctype) {
        this.currentDoctype = doctype;
        this.currentUser = frappe.user.name;
        this.loadColumnData();
    },
    
    // Load column data from server
    loadColumnData: function() {
        frappe.call({
            method: 'column_management.api.column_manager.get_column_config',
            args: {
                doctype: this.currentDoctype
            },
            callback: (r) => {
                if (r.message && r.message.success) {
                    this.availableColumns = r.message.data.available_columns || [];
                    this.selectedColumns = r.message.data.selected_columns || [];
                    this.showDialog();
                } else {
                    frappe.show_alert('❌ Failed to load column data', 'error');
                }
            },
            error: (r) => {
                frappe.show_alert('❌ Error loading column data', 'error');
            }
        });
    },
    
    // Show the main dialog
    showDialog: function() {
        const dialog = new frappe.ui.Dialog({
            title: `Manage Columns - ${this.currentDoctype}`,
            fields: [
                {
                    fieldtype: 'HTML',
                    fieldname: 'column_manager_html',
                    options: this.getDialogHTML()
                }
            ],
            size: 'large',
            primary_action_label: 'Save Configuration',
            primary_action: () => this.saveConfiguration()
        });
        
        this.dialog = dialog;
        dialog.show();
        
        // Initialize after dialog is shown
        setTimeout(() => {
            this.initializeDialog();
        }, 100);
    },
    
    // Get HTML for dialog
    getDialogHTML: function() {
        return `
            <div class="column-manager-container">
                <div class="row">
                    <!-- Available Columns -->
                    <div class="col-md-6">
                        <div class="panel panel-default">
                            <div class="panel-heading">
                                <h4 class="panel-title">
                                    <i class="fa fa-list"></i> Available Columns
                                    <span class="badge">${this.availableColumns.length}</span>
                                </h4>
                            </div>
                            <div class="panel-body">
                                <div class="form-group">
                                    <input type="text" class="form-control" id="column-search" 
                                           placeholder="Search columns..." />
                                </div>
                                <div class="available-columns-list" style="max-height: 300px; overflow-y: auto;">
                                    ${this.renderAvailableColumns()}
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Selected Columns -->
                    <div class="col-md-6">
                        <div class="panel panel-default">
                            <div class="panel-heading">
                                <h4 class="panel-title">
                                    <i class="fa fa-check-square-o"></i> Selected Columns
                                    <span class="badge">${this.selectedColumns.length}</span>
                                </h4>
                            </div>
                            <div class="panel-body">
                                <div class="selected-columns-list" style="max-height: 300px; overflow-y: auto;">
                                    ${this.renderSelectedColumns()}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Column Settings -->
                <div class="row" style="margin-top: 20px;">
                    <div class="col-md-12">
                        <div class="panel panel-default">
                            <div class="panel-heading">
                                <h4 class="panel-title">
                                    <i class="fa fa-cog"></i> Column Settings
                                </h4>
                            </div>
                            <div class="panel-body">
                                <div class="row">
                                    <div class="col-md-3">
                                        <label>Column Width (px)</label>
                                        <input type="number" class="form-control" id="column-width" 
                                               min="50" max="500" value="150" />
                                    </div>
                                    <div class="col-md-3">
                                        <label>Pin Position</label>
                                        <select class="form-control" id="pin-position">
                                            <option value="">No Pin</option>
                                            <option value="left">Pin Left</option>
                                            <option value="right">Pin Right</option>
                                        </select>
                                    </div>
                                    <div class="col-md-3">
                                        <label>Visibility</label>
                                        <select class="form-control" id="column-visibility">
                                            <option value="1">Visible</option>
                                            <option value="0">Hidden</option>
                                        </select>
                                    </div>
                                    <div class="col-md-3">
                                        <label>Order</label>
                                        <input type="number" class="form-control" id="column-order" 
                                               min="0" value="0" />
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Action Buttons -->
                <div class="row" style="margin-top: 20px;">
                    <div class="col-md-12 text-center">
                        <button class="btn btn-default" onclick="column_management.dialog.resetToDefaults()">
                            <i class="fa fa-refresh"></i> Reset to Defaults
                        </button>
                        <button class="btn btn-info" onclick="column_management.dialog.previewConfiguration()">
                            <i class="fa fa-eye"></i> Preview
                        </button>
                        <button class="btn btn-success" onclick="column_management.dialog.saveConfiguration()">
                            <i class="fa fa-save"></i> Save Configuration
                        </button>
                    </div>
                </div>
            </div>
        `;
    },
    
    // Render available columns
    renderAvailableColumns: function() {
        if (this.availableColumns.length === 0) {
            return '<div class="text-muted">No available columns found</div>';
        }
        
        return this.availableColumns.map(column => `
            <div class="column-item" data-fieldname="${column.fieldname}">
                <div class="row">
                    <div class="col-md-8">
                        <label class="column-label">
                            <input type="checkbox" class="column-checkbox" 
                                   ${this.isColumnSelected(column.fieldname) ? 'checked' : ''} />
                            ${column.label || column.fieldname}
                        </label>
                    </div>
                    <div class="col-md-4">
                        <span class="badge badge-info">${column.fieldtype}</span>
                    </div>
                </div>
            </div>
        `).join('');
    },
    
    // Render selected columns
    renderSelectedColumns: function() {
        if (this.selectedColumns.length === 0) {
            return '<div class="text-muted">No columns selected</div>';
        }
        
        return this.selectedColumns.map((column, index) => `
            <div class="selected-column-item" data-fieldname="${column.fieldname}">
                <div class="row">
                    <div class="col-md-6">
                        <strong>${column.label || column.fieldname}</strong>
                    </div>
                    <div class="col-md-2">
                        <span class="badge badge-info">${column.width}px</span>
                    </div>
                    <div class="col-md-2">
                        ${column.pinned ? `<span class="badge badge-warning">${column.pinned}</span>` : ''}
                    </div>
                    <div class="col-md-2">
                        <button class="btn btn-xs btn-danger" onclick="column_management.dialog.removeColumn('${column.fieldname}')">
                            <i class="fa fa-times"></i>
                        </button>
                    </div>
                </div>
            </div>
        `).join('');
    },
    
    // Check if column is selected
    isColumnSelected: function(fieldname) {
        return this.selectedColumns.some(col => col.fieldname === fieldname);
    },
    
    // Initialize dialog events
    initializeDialog: function() {
        // Search functionality
        $('#column-search').on('input', (e) => {
            const query = e.target.value.toLowerCase();
            $('.column-item').each(function() {
                const text = $(this).text().toLowerCase();
                $(this).toggle(text.includes(query));
            });
        });
        
        // Column selection
        $('.column-checkbox').on('change', (e) => {
            const fieldname = $(e.target).closest('.column-item').data('fieldname');
            if (e.target.checked) {
                this.addColumn(fieldname);
            } else {
                this.removeColumn(fieldname);
            }
        });
        
        // Settings change
        $('#column-width, #pin-position, #column-visibility, #column-order').on('change', () => {
            this.updateSelectedColumnSettings();
        });
    },
    
    // Add column to selected
    addColumn: function(fieldname) {
        const column = this.availableColumns.find(col => col.fieldname === fieldname);
        if (column && !this.isColumnSelected(fieldname)) {
            const newColumn = {
                fieldname: column.fieldname,
                label: column.label || column.fieldname,
                fieldtype: column.fieldtype,
                width: parseInt($('#column-width').val()) || 150,
                pinned: $('#pin-position').val() || null,
                visible: parseInt($('#column-visibility').val()) || 1,
                order: parseInt($('#column-order').val()) || 0
            };
            
            this.selectedColumns.push(newColumn);
            this.updateSelectedColumnsDisplay();
        }
    },
    
    // Remove column from selected
    removeColumn: function(fieldname) {
        this.selectedColumns = this.selectedColumns.filter(col => col.fieldname !== fieldname);
        this.updateSelectedColumnsDisplay();
        
        // Uncheck checkbox
        $(`.column-checkbox[data-fieldname="${fieldname}"]`).prop('checked', false);
    },
    
    // Update selected columns display
    updateSelectedColumnsDisplay: function() {
        $('.selected-columns-list').html(this.renderSelectedColumns());
        $('.badge').last().text(this.selectedColumns.length);
    },
    
    // Update settings for selected column
    updateSelectedColumnSettings: function() {
        // This will be used when a specific column is selected for editing
        // For now, it updates the default values for new columns
    },
    
    // Reset to defaults
    resetToDefaults: function() {
        frappe.confirm(
            'Are you sure you want to reset to default configuration?',
            () => {
                frappe.call({
                    method: 'column_management.api.column_manager.reset_column_config',
                    args: {
                        doctype: this.currentDoctype
                    },
                    callback: (r) => {
                        if (r.message && r.message.success) {
                            frappe.show_alert('✅ Configuration reset to defaults', 'success');
                            this.loadColumnData();
                        } else {
                            frappe.show_alert('❌ Failed to reset configuration', 'error');
                        }
                    }
                });
            }
        );
    },
    
    // Preview configuration
    previewConfiguration: function() {
        const previewDialog = new frappe.ui.Dialog({
            title: 'Preview Configuration',
            fields: [
                {
                    fieldtype: 'HTML',
                    fieldname: 'preview_html',
                    options: this.getPreviewHTML()
                }
            ],
            size: 'large'
        });
        
        previewDialog.show();
    },
    
    // Get preview HTML
    getPreviewHTML: function() {
        return `
            <div class="preview-container">
                <h4>Selected Columns (${this.selectedColumns.length})</h4>
                <table class="table table-bordered">
                    <thead>
                        <tr>
                            <th>Field</th>
                            <th>Label</th>
                            <th>Width</th>
                            <th>Pin</th>
                            <th>Visible</th>
                            <th>Order</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${this.selectedColumns.map(col => `
                            <tr>
                                <td>${col.fieldname}</td>
                                <td>${col.label}</td>
                                <td>${col.width}px</td>
                                <td>${col.pinned || '-'}</td>
                                <td>${col.visible ? 'Yes' : 'No'}</td>
                                <td>${col.order}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
    },
    
    // Save configuration
    saveConfiguration: function() {
        const config = {
            doctype: this.currentDoctype,
            columns: this.selectedColumns
        };
        
        frappe.call({
            method: 'column_management.api.column_manager.save_column_config',
            args: {
                doctype: this.currentDoctype,
                config: config
            },
            callback: (r) => {
                if (r.message && r.message.success) {
                    frappe.show_alert('✅ Configuration saved successfully', 'success');
                    this.dialog.hide();
                    
                    // Refresh the current list view
                    if (cur_list && cur_list.refresh) {
                        cur_list.refresh();
                    }
                } else {
                    frappe.show_alert('❌ Failed to save configuration', 'error');
                }
            },
            error: (r) => {
                frappe.show_alert('❌ Error saving configuration', 'error');
            }
        });
    }
};

// Global function to show column manager
window.showColumnManager = function(doctype) {
    column_management.dialog.init(doctype);
}; 