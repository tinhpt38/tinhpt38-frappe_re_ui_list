// Enhanced Column Management JavaScript
console.log('🚀 Enhanced Column Management JavaScript loaded');

// Global variables
let columnManagementInitialized = false;
let listViewDetected = false;

// Wait for page to be ready
$(document).ready(function () {
    console.log('📄 Document ready, initializing enhanced column management...');
    
    // Initialize immediately
    initializeColumnManagement();
    
    // Also try after a delay to catch late-loading content
    setTimeout(initializeColumnManagement, 1000);
    setTimeout(initializeColumnManagement, 3000);
    setTimeout(initializeColumnManagement, 5000);
});

// Main initialization function
function initializeColumnManagement() {
    if (columnManagementInitialized) {
        console.log('⚠️ Column management already initialized, skipping...');
        return;
    }
    
    console.log('🔍 Searching for list view...');
    
    // Method 1: Check cur_list
    if (typeof cur_list !== 'undefined' && cur_list && cur_list.doctype) {
        console.log('✅ Found cur_list:', cur_list.doctype);
        addColumnManageButton(cur_list);
        columnManagementInitialized = true;
        listViewDetected = true;
        return;
    }
    
    // Method 2: Check for list view containers
    const listViewSelectors = [
        '.list-view-container',
        '.list-container',
        '.list-view',
        '[data-doctype]',
        '.list-header'
    ];
    
    for (let selector of listViewSelectors) {
        const $element = $(selector);
        if ($element.length > 0) {
            console.log('✅ Found list view element:', selector);
            
            // Try to get doctype from various sources
            let doctype = null;
            
            // From data attribute
            doctype = $element.attr('data-doctype') || $element.find('[data-doctype]').attr('data-doctype');
            
            // From URL
            if (!doctype) {
                const url = window.location.pathname;
                const match = url.match(/\/([^\/]+)\/list$/);
                if (match) {
                    doctype = match[1];
                }
            }
            
            // From page title or breadcrumb
            if (!doctype) {
                const title = $('title').text() || $('.breadcrumb').text();
                if (title) {
                    const match = title.match(/([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)/);
                    if (match) {
                        doctype = match[1].replace(/\s+/g, '');
                    }
                }
            }
            
            console.log('📋 Detected doctype:', doctype);
            
            const mockListView = {
                doctype: doctype || 'Unknown',
                $page: $element
            };
            
            addColumnManageButton(mockListView);
            columnManagementInitialized = true;
            listViewDetected = true;
            return;
        }
    }
    
    // Method 3: Check for specific ERPNext patterns
    if (window.location.pathname.includes('/list') || window.location.pathname.includes('/List')) {
        console.log('✅ URL indicates list view');
        
        // Extract doctype from URL
        const urlParts = window.location.pathname.split('/');
        const doctype = urlParts[urlParts.length - 2]; // Usually /doctype/list
        
        console.log('📋 Extracted doctype from URL:', doctype);
        
        const mockListView = {
            doctype: doctype,
            $page: $('body')
        };
        
        addColumnManageButton(mockListView);
        columnManagementInitialized = true;
        listViewDetected = true;
        return;
    }
    
    console.log('❌ No list view detected yet...');
}

// Enhanced button addition function
function addColumnManageButton(listView) {
    console.log('🔧 Adding Column Manage button for:', listView.doctype);
    
    // Multiple selectors to try
    const selectors = [
        '.page-actions',
        '.list-actions',
        '.list-header .page-actions',
        '.list-view-container .page-actions',
        '.list-container .page-actions',
        '.list-header',
        '.list-view-container .list-header',
        '.list-container .list-header',
        '.page-header .page-actions',
        '.page-header'
    ];
    
    let buttonAdded = false;
    
    for (let selector of selectors) {
        const $container = $(selector);
        if ($container.length > 0) {
            console.log('✅ Found container:', selector);
            
            // Check if button already exists
            if ($container.find('.column-management-btn').length === 0) {
                const btn = createColumnManageButton(listView.doctype);
                $container.append(btn);
                console.log('✅ Button added to:', selector);
                buttonAdded = true;
                break;
            } else {
                console.log('⚠️ Button already exists in:', selector);
            }
        }
    }
    
    if (!buttonAdded) {
        console.log('❌ Could not find suitable container, adding fallback button');
        const btn = createColumnManageButton(listView.doctype, true);
        $('body').append(btn);
        console.log('✅ Fallback button added to body');
    }
}

// Create button function
function createColumnManageButton(doctype, isFallback = false) {
    const btn = $(`
        <button class="btn btn-default btn-sm column-management-btn" 
                style="${isFallback ? 'position: fixed; top: 10px; right: 10px; z-index: 9999;' : 'margin-left: 10px;'}"
                title="Manage columns for ${doctype}">
            <i class="fa fa-columns"></i> Manage Columns
        </button>
    `);

    btn.on('click', function (e) {
        e.preventDefault();
        e.stopPropagation();
        
        console.log('🖱️ Column Manage button clicked for doctype:', doctype);
        
        // Show a simple dialog first
        showColumnManageDialog(doctype);
    });

    return btn;
}

// Show column manager dialog
function showColumnManageDialog(doctype) {
    // Use the new column manager dialog
    if (typeof column_management !== 'undefined' && column_management.dialog) {
        column_management.dialog.init(doctype);
    } else {
        // Fallback to simple dialog
        const dialog = new frappe.ui.Dialog({
            title: `Manage Columns for ${doctype}`,
            fields: [
                {
                    fieldtype: 'HTML',
                    fieldname: 'content',
                    options: `
                        <div style="padding: 20px; text-align: center;">
                            <h4>Column Management</h4>
                            <p>Doctype: <strong>${doctype}</strong></p>
                            <p>Loading column manager...</p>
                            <button class="btn btn-primary" onclick="showColumnManager('${doctype}')">
                                Open Column Manager
                            </button>
                        </div>
                    `
                }
            ],
            size: 'medium'
        });

        dialog.show();
    }
}

// Test API function
function testColumnAPI(doctype) {
    console.log('🧪 Testing API for doctype:', doctype);
    
    frappe.call({
        method: 'column_management.api.column_manager.get_column_config',
        args: {
            doctype: doctype
        },
        callback: function (r) {
            console.log('📡 API Response:', r);
            
            if (r.message && r.message.success) {
                frappe.show_alert('✅ API working! Found ' + (r.message.data?.length || 0) + ' columns', 'success');
            } else {
                frappe.show_alert('❌ API error: ' + (r.message?.error || 'Unknown error'), 'error');
            }
        },
        error: function (r) {
            console.error('❌ API Error:', r);
            frappe.show_alert('❌ API call failed', 'error');
        }
    });
}

// Listen for DOM changes
$(document).on('DOMNodeInserted', function(e) {
    if (!columnManagementInitialized && !listViewDetected) {
        const $target = $(e.target);
        
        // Check if this is a list view element
        if ($target.hasClass('list-view-container') || 
            $target.hasClass('list-container') ||
            $target.find('.list-view-container').length > 0 ||
            $target.find('.list-container').length > 0) {
            
            console.log('🔄 List view container detected via DOM change');
            setTimeout(initializeColumnManagement, 500);
        }
    }
});

// Listen for URL changes (for SPA navigation)
let currentUrl = window.location.pathname;
setInterval(function() {
    if (window.location.pathname !== currentUrl) {
        console.log('🔄 URL changed, re-initializing...');
        currentUrl = window.location.pathname;
        columnManagementInitialized = false;
        listViewDetected = false;
        setTimeout(initializeColumnManagement, 1000);
    }
}, 1000);

// Global function for testing
window.testColumnManagement = function() {
    console.log('🧪 Manual test triggered');
    console.log('Current URL:', window.location.pathname);
    console.log('cur_list:', cur_list);
    console.log('List view containers:', $('.list-view-container').length);
    console.log('Page actions:', $('.page-actions').length);
    
    // Force re-initialization
    columnManagementInitialized = false;
    listViewDetected = false;
    initializeColumnManagement();
};

console.log('🎉 Enhanced Column Management JavaScript loaded successfully'); 