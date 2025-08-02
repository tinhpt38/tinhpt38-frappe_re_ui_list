// Simple Column Management Test
console.log('Column Management JavaScript loaded');

// Wait for page to be ready
$(document).ready(function () {
    console.log('Document ready, checking for list view...');
    
    // Check if we're on a list view
    if (typeof cur_list !== 'undefined' && cur_list && cur_list.doctype) {
        console.log('✅ Found list view:', cur_list.doctype);
        addColumnManageButton(cur_list);
    } else {
        console.log('❌ Not on list view or cur_list not found');
        console.log('cur_list:', cur_list);
        
        // Try to find list view elements
        if ($('.list-view-container').length > 0) {
            console.log('✅ Found list-view-container');
            addColumnManageButton();
        } else {
            console.log('❌ No list-view-container found');
        }
    }
});

function addColumnManageButton(listView) {
    console.log('Adding Column Manage button...');
    
    // Try different selectors for page actions
    const selectors = [
        '.page-actions',
        '.list-actions',
        '.list-header',
        '.list-container .list-header',
        '.list-view-container .list-header'
    ];
    
    let buttonAdded = false;
    
    for (let selector of selectors) {
        const $container = $(selector);
        if ($container.length > 0) {
            console.log('✅ Found container:', selector);
            
            // Check if button already exists
            if ($container.find('.column-management-btn').length === 0) {
                const btn = $(`
                    <button class="btn btn-default btn-sm column-management-btn" 
                            style="margin-left: 10px;">
                        <i class="fa fa-columns"></i> Manage Columns
                    </button>
                `);

                btn.on('click', function () {
                    const doctype = listView ? listView.doctype : 'Unknown';
                    console.log('Column Manage button clicked for doctype:', doctype);
                    alert('Column Management clicked for ' + doctype);
                });

                $container.append(btn);
                console.log('✅ Button added to:', selector);
                buttonAdded = true;
                break;
            } else {
                console.log('Button already exists in:', selector);
            }
        }
    }
    
    if (!buttonAdded) {
        console.log('❌ Could not find suitable container for button');
        // Add button to body as fallback
        const btn = $(`
            <button class="btn btn-default btn-sm column-management-btn" 
                    style="position: fixed; top: 10px; right: 10px; z-index: 9999;">
                <i class="fa fa-columns"></i> Manage Columns
            </button>
        `);
        
        btn.on('click', function () {
            alert('Column Management clicked (fallback)');
        });
        
        $('body').append(btn);
        console.log('✅ Button added to body as fallback');
    }
}

// Also try to add button when page content changes
$(document).on('DOMNodeInserted', function(e) {
    if ($(e.target).hasClass('list-view-container') || $(e.target).find('.list-view-container').length > 0) {
        console.log('List view container detected, adding button...');
        setTimeout(function() {
            addColumnManageButton();
        }, 1000);
    }
}); 