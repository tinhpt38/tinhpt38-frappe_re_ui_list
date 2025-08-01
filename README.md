# ERPNext Column Management

Hệ thống quản lý cột nâng cao cho ERPNext List Views, cung cấp trải nghiệm người dùng được cải thiện và tính linh hoạt cao.

**Tác giả**: P. Tính  
**Repository**: https://github.com/tinhpt38/tinhpt38-frappe_re_ui_list

## Tính năng

- **Cấu hình cột động**: Chọn, sắp xếp lại và cấu hình cột cho bất kỳ DocType nào
- **Quản lý chiều rộng cột**: Thay đổi kích thước cột với khả năng lưu trữ qua các phiên
- **Ghim cột**: Ghim các cột quan trọng ở bên trái hoặc bên phải
- **Hiển thị cột không giới hạn**: Hiển thị số lượng cột bất kỳ với virtual scrolling
- **Phân trang nâng cao**: Cải thiện phân trang với kích thước trang có thể cấu hình
- **Lọc động**: Lọc nâng cao với logic AND/OR và các preset đã lưu
- **Thống kê thời gian thực**: Dashboard thống kê trực tiếp dựa trên dữ liệu hiện tại
- **Tùy chọn người dùng**: Cài đặt cá nhân được lưu theo từng user và DocType
- **Responsive mobile**: Giao diện được tối ưu cho thiết bị di động và tablet
- **Tối ưu hiệu suất**: Virtual scrolling và caching cho datasets lớn

## Cài đặt

### Yêu cầu hệ thống

- ERPNext/Frappe Framework v13.0 trở lên
- Python 3.7 trở lên

### Cài đặt qua Bench

```bash
# Lấy app từ GitHub
bench get-app https://github.com/tinhpt38/tinhpt38-frappe_re_ui_list.git

# Cài đặt trên site của bạn
bench --site your-site-name install-app column_management

# Chạy migration
bench --site your-site-name migrate
```

### Cài đặt thủ công

1. Clone repository vào thư mục apps:
```bash
cd frappe-bench/apps
git clone https://github.com/tinhpt38/tinhpt38-frappe_re_ui_list.git column_management
```

2. Cài đặt app:
```bash
bench --site your-site-name install-app column_management
```

3. Chạy migrations:
```bash
bench --site your-site-name migrate
```

## Usage

After installation, the column management features will be automatically available in all List Views:

1. **Column Manager**: Click the "Manage Columns" button in any List View
2. **Column Resizing**: Drag column borders to resize
3. **Column Pinning**: Right-click column headers for pinning options
4. **Advanced Filters**: Use the enhanced filter panel for complex queries
5. **Statistics Dashboard**: View real-time statistics in the sidebar

## Configuration

### Default Statistics

The app comes with pre-configured statistics for common DocTypes like Sales Invoice and Purchase Invoice. You can add more through:

1. Go to "Statistics Config" DocType
2. Create new statistics configurations
3. Configure calculation types, fields, and formatting

### Permissions

By default, all users with read access to a DocType can use column management features. System Managers have full access to configuration.

## Development

### Setup Development Environment

```bash
# Create a new bench
bench init frappe-bench --frappe-branch version-13

# Get ERPNext
cd frappe-bench
bench get-app erpnext --branch version-13

# Get Column Management
bench get-app https://github.com/your-org/column_management.git

# Create a new site
bench new-site development.localhost

# Install apps
bench --site development.localhost install-app erpnext
bench --site development.localhost install-app column_management

# Start development server
bench start
```

### Running Tests

```bash
# Run all tests
bench --site development.localhost run-tests --app column_management

# Run specific test
bench --site development.localhost run-tests --app column_management --module column_management.tests.test_column_service
```

## API Reference

### Column Management API

```python
# Get column configuration
frappe.call({
    method: "column_management.api.column_manager.get_column_config",
    args: {
        doctype: "Sales Invoice"
    }
})

# Save column configuration
frappe.call({
    method: "column_management.api.column_manager.save_column_config",
    args: {
        doctype: "Sales Invoice",
        config: column_config_data
    }
})
```

### Enhanced List API

```python
# Get enhanced list data
frappe.call({
    method: "column_management.api.enhanced_list.get_list_data",
    args: {
        doctype: "Sales Invoice",
        columns: selected_columns,
        filters: active_filters,
        page: 1,
        page_size: 20
    }
})
```

## Đóng góp

1. Fork repository
2. Tạo feature branch
3. Thực hiện thay đổi
4. Thêm tests cho tính năng mới
5. Chạy test suite
6. Gửi pull request

## Giấy phép

MIT License. Xem file LICENSE để biết chi tiết.

## Hỗ trợ

- **Tác giả**: P. Tính
- **Repository**: https://github.com/tinhpt38/tinhpt38-frappe_re_ui_list
- **Issues**: https://github.com/tinhpt38/tinhpt38-frappe_re_ui_list/issues
- **Wiki**: https://github.com/tinhpt38/tinhpt38-frappe_re_ui_list/wiki

## Changelog

### v1.0.0
- Phát hành đầu tiên
- Chức năng quản lý cột cốt lõi
- Quản lý và lưu trữ chiều rộng cột
- Hệ thống ghim cột
- Phân trang nâng cao
- Lọc động
- Dashboard thống kê thời gian thực
- Thiết kế responsive cho mobile