# Column Manager Component

## Overview

The Column Manager Component is a sophisticated Vue.js-like component built for ERPNext/Frappe framework that provides advanced column management capabilities for List Views. It allows users to:

- Select and deselect columns for display
- Reorder columns using drag-and-drop
- Adjust column widths
- Pin columns to left or right sides
- Search and filter columns
- Save and restore user preferences

## Features

### Core Functionality
- **Column Selection**: Toggle column visibility with checkboxes
- **Drag & Drop Reordering**: Intuitive column reordering using Sortable.js
- **Width Management**: Adjust column widths with validation
- **Column Pinning**: Pin important columns to left or right sides
- **Search**: Find specific columns quickly
- **Auto-resize**: Automatically calculate optimal column widths

### Advanced Features
- **Validation**: Comprehensive validation for column configurations
- **Responsive Design**: Mobile-friendly interface
- **Keyboard Shortcuts**: Power user shortcuts (Ctrl+A, Ctrl+S, etc.)
- **Real-time Updates**: Live preview of changes
- **Error Handling**: Robust error handling and user feedback
- **Accessibility**: WCAG compliant with proper ARIA labels

## Usage

### Basic Initialization

```javascript
// Initialize Column Manager for a list view
const columnManager = new ColumnManager({
    doctype: 'Your DocType',
    listview: listViewInstance
});
```

### API Methods

```javascript
// Show the column manager dialog
columnManager.show_column_manager_dialog();

// Save current configuration
await columnManager.save_column_config();

// Reset to default configuration
columnManager.reset_to_default();

// Apply configuration to list view
await columnManager.apply_column_config();

// Cleanup resources
columnManager.destroy();
```

### Configuration Options

```javascript
const columnManager = new ColumnManager({
    doctype: 'Your DocType',
    listview: listViewInstance,
    validation_rules: {
        min_width: 50,
        max_width: 1000,
        max_columns: 50,
        required_columns: ['name']
    }
});
```

## Column Configuration Format

Each column configuration object contains:

```javascript
{
    fieldname: 'field_name',      // Field name from DocType
    label: 'Display Label',       // Human-readable label
    fieldtype: 'Data',           // Frappe field type
    width: 150,                  // Width in pixels
    visible: true,               // Visibility flag
    order: 0,                    // Display order
    pinned: 'left'               // Pin position: 'left', 'right', or null
}
```

## Events

The component triggers custom events that other components can listen to:

```javascript
// Listen for configuration changes
$(document).on('column_config_saved', function(event, data) {
    console.log('Column configuration saved:', data);
});
```

## Styling

The component includes comprehensive CSS styling with:

- Responsive design for mobile devices
- Dark mode support
- Smooth animations and transitions
- Accessibility improvements
- Bootstrap-compatible styling

### CSS Classes

- `.column-manager` - Main container
- `.column-item` - Individual column item
- `.column-item.error` - Validation error state
- `.column-item.warning` - Warning state
- `.sortable-ghost` - Drag placeholder
- `.pinned-left`, `.pinned-right` - Pinned column indicators

## Testing

A standalone test file is provided at `column_manager_test.html` for testing the component outside of the Frappe environment.

### Running Tests

1. Open `column_manager_test.html` in a web browser
2. Click "Open Column Manager" button
3. Test all functionality including:
   - Column selection/deselection
   - Drag and drop reordering
   - Width adjustment
   - Pin/unpin functionality
   - Search functionality
   - Save/reset operations

## Browser Support

- Chrome 60+
- Firefox 55+
- Safari 12+
- Edge 79+

## Dependencies

- jQuery 3.6+
- Sortable.js 1.15+
- Bootstrap 5.1+ (for styling)
- Font Awesome 6.0+ (for icons)

## Integration with Frappe

The component automatically integrates with Frappe List Views:

```javascript
// Auto-initialization when list view loads
$(document).on('list_view_loaded', function(e, listview) {
    if (listview && listview.doctype) {
        window.column_manager = new ColumnManager({
            doctype: listview.doctype,
            listview: listview
        });
    }
});
```

## Performance Considerations

- Uses debounced input handlers to prevent excessive API calls
- Implements virtual scrolling for large column lists
- Caches column metadata to reduce server requests
- Optimized DOM manipulation for smooth interactions

## Accessibility

The component follows WCAG 2.1 guidelines:

- Proper ARIA labels and roles
- Keyboard navigation support
- High contrast mode compatibility
- Screen reader friendly

## Troubleshooting

### Common Issues

1. **Sortable.js not working**: Ensure Sortable.js is loaded before the component
2. **Styles not applied**: Check that CSS file is included in hooks.py
3. **API errors**: Verify backend API endpoints are properly configured
4. **Mobile issues**: Test responsive breakpoints and touch interactions

### Debug Mode

Enable debug logging:

```javascript
// Add to browser console
localStorage.setItem('column_manager_debug', 'true');
```

## Contributing

When contributing to this component:

1. Follow the existing code style
2. Add comprehensive comments
3. Include unit tests for new features
4. Update documentation
5. Test on multiple browsers and devices

## License

MIT License - see LICENSE file for details.