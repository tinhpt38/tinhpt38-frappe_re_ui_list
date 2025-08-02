/**
 * Performance Monitoring and Optimization
 * Copyright (c) 2024, ERPNext Column Management Team
 */

frappe.provide('column_management.performance');

column_management.performance = {
    
    /**
     * Performance monitor class
     */
    PerformanceMonitor: class {
        constructor(options = {}) {
            this.doctype = options.doctype;
            this.monitoring_interval = options.monitoring_interval || 30000; // 30 seconds
            this.metrics_history = [];
            this.alerts = [];
            this.is_monitoring = false;
            this.monitor_timer = null;
            
            // Performance thresholds
            this.thresholds = {
                response_time: 1000, // ms
                memory_usage: 85, // %
                cpu_usage: 80, // %
                cache_hit_ratio: 0.7
            };
            
            this.init();
        }
        
        init() {
            this.setup_performance_tracking();
            this.start_monitoring();
        }
        
        setup_performance_tracking() {
            // Track page load performance
            if (window.performance && window.performance.timing) {
                this.track_page_load_performance();
            }
            
            // Track AJAX request performance
            this.setup_ajax_performance_tracking();
            
            // Track user interactions
            this.setup_interaction_tracking();
        }
        
        track_page_load_performance() {
            const timing = window.performance.timing;
            const metrics = {
                dns_lookup: timing.domainLookupEnd - timing.domainLookupStart,
                tcp_connect: timing.connectEnd - timing.connectStart,
                server_response: timing.responseEnd - timing.requestStart,
                dom_processing: timing.domComplete - timing.domLoading,
                page_load: timing.loadEventEnd - timing.navigationStart
            };
            
            this.record_metric('page_load', metrics);
        }
        
        setup_ajax_performance_tracking() {
            const self = this;
            
            // Override frappe.call to track performance
            const original_call = frappe.call;
            frappe.call = function(options) {
                const start_time = performance.now();
                const method = options.method || 'unknown';
                
                // Add success callback wrapper
                const original_success = options.callback;
                options.callback = function(response) {
                    const end_time = performance.now();
                    const duration = end_time - start_time;
                    
                    self.record_metric('ajax_request', {
                        method: method,
                        duration: duration,
                        success: true,
                        timestamp: Date.now()
                    });
                    
                    if (original_success) {
                        original_success(response);
                    }
                };
                
                // Add error callback wrapper
                const original_error = options.error;
                options.error = function(response) {
                    const end_time = performance.now();
                    const duration = end_time - start_time;
                    
                    self.record_metric('ajax_request', {
                        method: method,
                        duration: duration,
                        success: false,
                        error: response,
                        timestamp: Date.now()
                    });
                    
                    if (original_error) {
                        original_error(response);
                    }
                };
                
                return original_call.call(this, options);
            };
        }
        
        setup_interaction_tracking() {
            const self = this;
            
            // Track scroll performance
            let scroll_start = null;
            $(window).on('scroll', function() {
                if (!scroll_start) {
                    scroll_start = performance.now();
                }
                
                clearTimeout(self.scroll_timeout);
                self.scroll_timeout = setTimeout(() => {
                    const scroll_end = performance.now();
                    const duration = scroll_end - scroll_start;
                    
                    self.record_metric('scroll_performance', {
                        duration: duration,
                        timestamp: Date.now()
                    });
                    
                    scroll_start = null;
                }, 100);
            });
            
            // Track click response times
            $(document).on('click', '[data-performance-track]', function() {
                const start_time = performance.now();
                const element = this;
                
                setTimeout(() => {
                    const end_time = performance.now();
                    const duration = end_time - start_time;
                    
                    self.record_metric('click_response', {
                        element: element.tagName,
                        duration: duration,
                        timestamp: Date.now()
                    });
                }, 0);
            });
        }
        
        start_monitoring() {
            if (this.is_monitoring) {
                return;
            }
            
            this.is_monitoring = true;
            this.monitor_timer = setInterval(() => {
                this.collect_system_metrics();
            }, this.monitoring_interval);
            
            console.log('Performance monitoring started');
        }
        
        stop_monitoring() {
            if (!this.is_monitoring) {
                return;
            }
            
            this.is_monitoring = false;
            if (this.monitor_timer) {
                clearInterval(this.monitor_timer);
                this.monitor_timer = null;
            }
            
            console.log('Performance monitoring stopped');
        }
        
        async collect_system_metrics() {
            try {
                // Get performance dashboard data
                const response = await frappe.call({
                    method: 'column_management.column_management.api.enhanced_list.get_performance_dashboard',
                    args: {
                        doctype: this.doctype
                    }
                });
                
                if (response.message && response.message.success) {
                    const data = response.message.data;
                    this.process_system_metrics(data);
                }
                
            } catch (error) {
                console.error('Error collecting system metrics:', error);
            }
        }
        
        process_system_metrics(data) {
            const metrics = data.realtime_metrics;
            
            // Record system metrics
            this.record_metric('system_performance', {
                cpu_usage: metrics.system?.cpu?.usage_percent || 0,
                memory_usage: metrics.system?.memory?.usage_percent || 0,
                cache_hit_ratio: metrics.cache?.hit_ratio || 0,
                response_time: metrics.application?.average_response_time || 0,
                timestamp: Date.now()
            });
            
            // Check for alerts
            this.check_performance_alerts(metrics);
            
            // Update dashboard if visible
            this.update_performance_dashboard(data);
        }
        
        check_performance_alerts(metrics) {
            const alerts = [];
            
            // CPU usage alert
            const cpu_usage = metrics.system?.cpu?.usage_percent || 0;
            if (cpu_usage > this.thresholds.cpu_usage) {
                alerts.push({
                    type: 'warning',
                    message: `High CPU usage: ${cpu_usage.toFixed(1)}%`,
                    severity: 'high',
                    timestamp: Date.now()
                });
            }
            
            // Memory usage alert
            const memory_usage = metrics.system?.memory?.usage_percent || 0;
            if (memory_usage > this.thresholds.memory_usage) {
                alerts.push({
                    type: 'warning',
                    message: `High memory usage: ${memory_usage.toFixed(1)}%`,
                    severity: 'high',
                    timestamp: Date.now()
                });
            }
            
            // Cache performance alert
            const cache_hit_ratio = metrics.cache?.hit_ratio || 1;
            if (cache_hit_ratio < this.thresholds.cache_hit_ratio) {
                alerts.push({
                    type: 'info',
                    message: `Low cache hit ratio: ${(cache_hit_ratio * 100).toFixed(1)}%`,
                    severity: 'medium',
                    timestamp: Date.now()
                });
            }
            
            // Response time alert
            const response_time = metrics.application?.average_response_time || 0;
            if (response_time > this.thresholds.response_time) {
                alerts.push({
                    type: 'warning',
                    message: `Slow response time: ${response_time.toFixed(0)}ms`,
                    severity: 'medium',
                    timestamp: Date.now()
                });
            }
            
            // Add new alerts
            alerts.forEach(alert => {
                this.add_alert(alert);
            });
        }
        
        record_metric(type, data) {
            const metric = {
                type: type,
                data: data,
                timestamp: Date.now()
            };
            
            this.metrics_history.push(metric);
            
            // Keep only recent metrics (last 1000)
            if (this.metrics_history.length > 1000) {
                this.metrics_history.shift();
            }
            
            // Trigger metric recorded event
            $(document).trigger('performance-metric-recorded', metric);
        }
        
        add_alert(alert) {
            // Check if similar alert already exists
            const existing_alert = this.alerts.find(a => 
                a.message === alert.message && 
                (Date.now() - a.timestamp) < 60000 // Within last minute
            );
            
            if (!existing_alert) {
                this.alerts.push(alert);
                
                // Keep only recent alerts (last 50)
                if (this.alerts.length > 50) {
                    this.alerts.shift();
                }
                
                // Show alert to user
                this.show_alert(alert);
                
                // Trigger alert event
                $(document).trigger('performance-alert', alert);
            }
        }
        
        show_alert(alert) {
            if (alert.severity === 'high') {
                frappe.msgprint({
                    title: __('Performance Alert'),
                    message: alert.message,
                    indicator: 'red'
                });
            } else if (alert.severity === 'medium') {
                frappe.show_alert({
                    message: alert.message,
                    indicator: 'orange'
                }, 5);
            }
        }
        
        update_performance_dashboard(data) {
            // Update dashboard if it exists
            if (window.performance_dashboard) {
                window.performance_dashboard.update(data);
            }
        }
        
        get_metrics_summary() {
            const recent_metrics = this.metrics_history.filter(m => 
                Date.now() - m.timestamp < 300000 // Last 5 minutes
            );
            
            const summary = {
                total_requests: 0,
                average_response_time: 0,
                error_rate: 0,
                cache_performance: 0
            };
            
            const ajax_requests = recent_metrics.filter(m => m.type === 'ajax_request');
            if (ajax_requests.length > 0) {
                summary.total_requests = ajax_requests.length;
                summary.average_response_time = ajax_requests.reduce((sum, m) => 
                    sum + m.data.duration, 0) / ajax_requests.length;
                summary.error_rate = ajax_requests.filter(m => !m.data.success).length / ajax_requests.length;
            }
            
            const system_metrics = recent_metrics.filter(m => m.type === 'system_performance');
            if (system_metrics.length > 0) {
                const latest_system = system_metrics[system_metrics.length - 1];
                summary.cache_performance = latest_system.data.cache_hit_ratio;
            }
            
            return summary;
        }
        
        get_performance_report() {
            return {
                metrics_history: this.metrics_history,
                alerts: this.alerts,
                summary: this.get_metrics_summary(),
                thresholds: this.thresholds,
                monitoring_status: this.is_monitoring
            };
        }
        
        export_performance_data() {
            const data = this.get_performance_report();
            const blob = new Blob([JSON.stringify(data, null, 2)], {
                type: 'application/json'
            });
            
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `performance_report_${Date.now()}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        }
        
        clear_metrics() {
            this.metrics_history = [];
            this.alerts = [];
            console.log('Performance metrics cleared');
        }
        
        destroy() {
            this.stop_monitoring();
            this.clear_metrics();
            
            // Remove event listeners
            $(window).off('scroll');
            $(document).off('click', '[data-performance-track]');
            
            console.log('Performance monitor destroyed');
        }
    },
    
    /**
     * Performance dashboard widget
     */
    PerformanceDashboard: class {
        constructor(container, options = {}) {
            this.container = container;
            this.options = options;
            this.charts = {};
            this.data = null;
            
            this.init();
        }
        
        init() {
            this.create_dashboard_layout();
            this.setup_refresh_timer();
        }
        
        create_dashboard_layout() {
            const $container = $(this.container);
            $container.addClass('performance-dashboard');
            
            // Create header
            const $header = $('<div class="dashboard-header"></div>');
            $header.html(`
                <h4>Performance Dashboard</h4>
                <div class="dashboard-controls">
                    <button class="btn btn-sm btn-default" data-action="refresh">
                        <i class="fa fa-refresh"></i> Refresh
                    </button>
                    <button class="btn btn-sm btn-default" data-action="export">
                        <i class="fa fa-download"></i> Export
                    </button>
                </div>
            `);
            
            // Create metrics grid
            const $metrics = $('<div class="dashboard-metrics row"></div>');
            $metrics.html(`
                <div class="col-md-3">
                    <div class="metric-card" data-metric="cpu">
                        <div class="metric-value">--</div>
                        <div class="metric-label">CPU Usage</div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="metric-card" data-metric="memory">
                        <div class="metric-value">--</div>
                        <div class="metric-label">Memory Usage</div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="metric-card" data-metric="response">
                        <div class="metric-value">--</div>
                        <div class="metric-label">Response Time</div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="metric-card" data-metric="cache">
                        <div class="metric-value">--</div>
                        <div class="metric-label">Cache Hit Ratio</div>
                    </div>
                </div>
            `);
            
            // Create charts area
            const $charts = $('<div class="dashboard-charts row"></div>');
            $charts.html(`
                <div class="col-md-6">
                    <div class="chart-container">
                        <h5>System Performance</h5>
                        <canvas id="system-chart"></canvas>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="chart-container">
                        <h5>Response Times</h5>
                        <canvas id="response-chart"></canvas>
                    </div>
                </div>
            `);
            
            // Create alerts area
            const $alerts = $('<div class="dashboard-alerts"></div>');
            $alerts.html(`
                <h5>Recent Alerts</h5>
                <div class="alerts-list"></div>
            `);
            
            $container.append($header);
            $container.append($metrics);
            $container.append($charts);
            $container.append($alerts);
            
            this.setup_event_handlers();
        }
        
        setup_event_handlers() {
            const $container = $(this.container);
            
            $container.on('click', '[data-action="refresh"]', () => {
                this.refresh_data();
            });
            
            $container.on('click', '[data-action="export"]', () => {
                this.export_data();
            });
        }
        
        setup_refresh_timer() {
            setInterval(() => {
                this.refresh_data();
            }, 30000); // Refresh every 30 seconds
        }
        
        async refresh_data() {
            try {
                const response = await frappe.call({
                    method: 'column_management.column_management.api.enhanced_list.get_performance_dashboard',
                    args: {
                        doctype: this.options.doctype
                    }
                });
                
                if (response.message && response.message.success) {
                    this.update(response.message.data);
                }
                
            } catch (error) {
                console.error('Error refreshing dashboard data:', error);
            }
        }
        
        update(data) {
            this.data = data;
            this.update_metrics(data.realtime_metrics);
            this.update_charts(data);
            this.update_alerts(data.alerts);
        }
        
        update_metrics(metrics) {
            const $container = $(this.container);
            
            // Update CPU usage
            const cpu_usage = metrics.system?.cpu?.usage_percent || 0;
            $container.find('[data-metric="cpu"] .metric-value').text(`${cpu_usage.toFixed(1)}%`);
            
            // Update memory usage
            const memory_usage = metrics.system?.memory?.usage_percent || 0;
            $container.find('[data-metric="memory"] .metric-value').text(`${memory_usage.toFixed(1)}%`);
            
            // Update response time
            const response_time = metrics.application?.average_response_time || 0;
            $container.find('[data-metric="response"] .metric-value').text(`${response_time.toFixed(0)}ms`);
            
            // Update cache hit ratio
            const cache_ratio = metrics.cache?.hit_ratio || 0;
            $container.find('[data-metric="cache"] .metric-value').text(`${(cache_ratio * 100).toFixed(1)}%`);
            
            // Update metric card colors based on thresholds
            this.update_metric_colors(cpu_usage, memory_usage, response_time, cache_ratio);
        }
        
        update_metric_colors(cpu, memory, response, cache) {
            const $container = $(this.container);
            
            // CPU color
            const $cpu_card = $container.find('[data-metric="cpu"]');
            $cpu_card.removeClass('metric-good metric-warning metric-danger');
            if (cpu > 80) $cpu_card.addClass('metric-danger');
            else if (cpu > 60) $cpu_card.addClass('metric-warning');
            else $cpu_card.addClass('metric-good');
            
            // Memory color
            const $memory_card = $container.find('[data-metric="memory"]');
            $memory_card.removeClass('metric-good metric-warning metric-danger');
            if (memory > 85) $memory_card.addClass('metric-danger');
            else if (memory > 70) $memory_card.addClass('metric-warning');
            else $memory_card.addClass('metric-good');
            
            // Response time color
            const $response_card = $container.find('[data-metric="response"]');
            $response_card.removeClass('metric-good metric-warning metric-danger');
            if (response > 1000) $response_card.addClass('metric-danger');
            else if (response > 500) $response_card.addClass('metric-warning');
            else $response_card.addClass('metric-good');
            
            // Cache color
            const $cache_card = $container.find('[data-metric="cache"]');
            $cache_card.removeClass('metric-good metric-warning metric-danger');
            if (cache < 0.7) $cache_card.addClass('metric-danger');
            else if (cache < 0.8) $cache_card.addClass('metric-warning');
            else $cache_card.addClass('metric-good');
        }
        
        update_charts(data) {
            // This would typically use Chart.js or similar library
            // For now, just log the data
            console.log('Updating charts with data:', data);
        }
        
        update_alerts(alerts) {
            const $alerts_list = $(this.container).find('.alerts-list');
            $alerts_list.empty();
            
            if (!alerts || alerts.length === 0) {
                $alerts_list.html('<div class="text-muted">No recent alerts</div>');
                return;
            }
            
            alerts.slice(0, 5).forEach(alert => {
                const $alert = $(`
                    <div class="alert alert-${alert.type === 'critical' ? 'danger' : alert.type === 'warning' ? 'warning' : 'info'} alert-sm">
                        <strong>${alert.severity.toUpperCase()}:</strong> ${alert.message}
                        <small class="pull-right">${moment(alert.timestamp).fromNow()}</small>
                    </div>
                `);
                $alerts_list.append($alert);
            });
        }
        
        export_data() {
            if (!this.data) {
                frappe.msgprint(__('No data to export'));
                return;
            }
            
            const blob = new Blob([JSON.stringify(this.data, null, 2)], {
                type: 'application/json'
            });
            
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `performance_dashboard_${Date.now()}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        }
    },
    
    // Global performance monitor instance
    monitor: null,
    
    /**
     * Initialize performance monitoring
     */
    init: function(options = {}) {
        if (this.monitor) {
            this.monitor.destroy();
        }
        
        this.monitor = new this.PerformanceMonitor(options);
        return this.monitor;
    },
    
    /**
     * Create performance dashboard
     */
    create_dashboard: function(container, options = {}) {
        return new this.PerformanceDashboard(container, options);
    },
    
    /**
     * Get current performance metrics
     */
    get_metrics: function() {
        return this.monitor ? this.monitor.get_performance_report() : null;
    }
};

// Auto-initialize performance monitoring
$(document).ready(function() {
    // Initialize performance monitoring if enabled
    if (frappe.boot.enable_performance_monitoring !== false) {
        column_management.performance.init();
    }
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = column_management.performance;
}