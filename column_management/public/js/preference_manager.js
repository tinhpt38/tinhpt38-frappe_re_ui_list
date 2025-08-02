/**
 * Preference Manager - Handles automatic saving and loading of user preferences
 * Copyright (c) 2024, ERPNext Column Management Team
 */

class PreferenceManager {
    constructor() {
        this.auto_save_enabled = true;
        this.auto_save_delay = 2000; // 2 seconds
        this.debounce_timers = {};
        this.cache = new Map();
        this.cache_ttl = 300000; // 5 minutes
        
        // Initialize on DOM ready
        $(document).ready(() => {
            this.initialize();
        });
    }
    
    initialize() {
        console.log('Preference Manager initialized');
        
        // Restore preferences on login
        this.restorePreferencesOnLogin();
        
        // Set up event listeners for automatic saving
        this.setupAutoSaveListeners();
        
        // Set up periodic cache cleanup
        this.setupCacheCleanup();
        
        // Set up real-time synchronization
        this.setupRealtimeSync();
    }
    
    /**
     * Get user preferences for a doctype
     */
    async getUserPreferences(doctype_name) {
        try {
            // Check cache first
            const cache_key = `prefs_${doctype_name}`;
            const cached = this.getFromCache(cache_key);
            if (cached) {
                return cached;
            }
            
            // Fetch from server
            const response = await frappe.call({
                method: 'column_management.api.preference_manager.get_user_preferences',
                args: {
                    doctype_name: doctype_name
                }
            });
            
            if (response.message && response.message.success) {
                const preferences = response.message.preferences;
                
                // Cache the result
                this.setCache(cache_key, preferences);
                
                return preferences;
            } else {
                throw new Error(response.message?.error || 'Failed to get preferences');
            }
            
        } catch (error) {
            console.error('Error getting user preferences:', error);
            return this.getDefaultPreferences(doctype_name);
        }
    }
    
    /**
     * Save user preferences for a doctype
     */
    async saveUserPreferences(doctype_name, preferences) {
        try {
            const response = await frappe.call({
                method: 'column_management.api.preference_manager.save_user_preferences',
                args: {
                    doctype_name: doctype_name,
                    preferences: preferences
                }
            });
            
            if (response.message && response.message.success) {
                // Update cache
                const cache_key = `prefs_${doctype_name}`;
                this.setCache(cache_key, preferences);
                
                console.log('Preferences saved successfully for', doctype_name);
                return true;
            } else {
                throw new Error(response.message?.error || 'Failed to save preferences');
            }
            
        } catch (error) {
            console.error('Error saving user preferences:', error);
            frappe.msgprint({
                title: __('Error'),
                message: __('Failed to save preferences: {0}', [error.message]),
                indicator: 'red'
            });
            return false;
        }
    }
    
    /**
     * Auto-save preferences with debouncing
     */
    autoSavePreferences(doctype_name, preference_type, updates) {
        if (!this.auto_save_enabled) {
            return;
        }
        
        const debounce_key = `${doctype_name}_${preference_type}`;
        
        // Clear existing timer
        if (this.debounce_timers[debounce_key]) {
            clearTimeout(this.debounce_timers[debounce_key]);
        }
        
        // Set new timer
        this.debounce_timers[debounce_key] = setTimeout(async () => {
            try {
                const response = await frappe.call({
                    method: 'column_management.api.preference_manager.auto_save_preferences',
                    args: {
                        doctype_name: doctype_name,
                        preference_type: preference_type,
                        updates: updates
                    }
                });
                
                if (response.message && response.message.success) {
                    console.log(`Auto-saved ${preference_type} preferences for ${doctype_name}`);
                    
                    // Update cache
                    const cache_key = `prefs_${doctype_name}`;
                    this.invalidateCache(cache_key);
                }
                
            } catch (error) {
                console.error('Error auto-saving preferences:', error);
            }
            
            // Clean up timer
            delete this.debounce_timers[debounce_key];
            
        }, this.auto_save_delay);
    }
    
    /**
     * Update column preferences
     */
    async updateColumnPreferences(doctype_name, column_updates) {
        try {
            // Auto-save if enabled
            if (this.auto_save_enabled) {
                this.autoSavePreferences(doctype_name, 'columns', column_updates);
                return true;
            }
            
            // Manual save
            const response = await frappe.call({
                method: 'column_management.api.preference_manager.update_column_preferences',
                args: {
                    doctype_name: doctype_name,
                    column_updates: column_updates
                }
            });
            
            return response.message && response.message.success;
            
        } catch (error) {
            console.error('Error updating column preferences:', error);
            return false;
        }
    }
    
    /**
     * Update filter preferences
     */
    async updateFilterPreferences(doctype_name, filter_updates) {
        try {
            // Auto-save if enabled
            if (this.auto_save_enabled) {
                this.autoSavePreferences(doctype_name, 'filters', filter_updates);
                return true;
            }
            
            // Manual save
            const response = await frappe.call({
                method: 'column_management.api.preference_manager.update_filter_preferences',
                args: {
                    doctype_name: doctype_name,
                    filter_updates: filter_updates
                }
            });
            
            return response.message && response.message.success;
            
        } catch (error) {
            console.error('Error updating filter preferences:', error);
            return false;
        }
    }
    
    /**
     * Update pagination preferences
     */
    async updatePaginationPreferences(doctype_name, pagination_updates) {
        try {
            // Auto-save if enabled
            if (this.auto_save_enabled) {
                this.autoSavePreferences(doctype_name, 'pagination', pagination_updates);
                return true;
            }
            
            // Manual save
            const response = await frappe.call({
                method: 'column_management.api.preference_manager.update_pagination_preferences',
                args: {
                    doctype_name: doctype_name,
                    pagination_updates: pagination_updates
                }
            });
            
            return response.message && response.message.success;
            
        } catch (error) {
            console.error('Error updating pagination preferences:', error);
            return false;
        }
    }
    
    /**
     * Restore preferences on login
     */
    async restorePreferencesOnLogin() {
        try {
            const response = await frappe.call({
                method: 'column_management.api.preference_manager.restore_preferences_on_login'
            });
            
            if (response.message && response.message.success) {
                console.log(`Restored ${response.message.restored_count} preferences on login`);
            }
            
        } catch (error) {
            console.error('Error restoring preferences on login:', error);
        }
    }
    
    /**
     * Reset preferences to defaults
     */
    async resetToDefaults(doctype_name) {
        try {
            const response = await frappe.call({
                method: 'column_management.api.preference_manager.reset_to_defaults',
                args: {
                    doctype_name: doctype_name
                }
            });
            
            if (response.message && response.message.success) {
                // Clear cache
                const cache_key = `prefs_${doctype_name}`;
                this.invalidateCache(cache_key);
                
                frappe.msgprint({
                    title: __('Success'),
                    message: __('Preferences reset to defaults successfully'),
                    indicator: 'green'
                });
                
                return response.message.preferences;
            } else {
                throw new Error(response.message?.error || 'Failed to reset preferences');
            }
            
        } catch (error) {
            console.error('Error resetting preferences:', error);
            frappe.msgprint({
                title: __('Error'),
                message: __('Failed to reset preferences: {0}', [error.message]),
                indicator: 'red'
            });
            return null;
        }
    }
    
    /**
     * Export user preferences
     */
    async exportPreferences(doctype_names = null) {
        try {
            const response = await frappe.call({
                method: 'column_management.api.preference_manager.export_user_preferences',
                args: {
                    doctype_names: doctype_names
                }
            });
            
            if (response.message && response.message.success) {
                const export_data = response.message.export_data;
                
                // Create download link
                const blob = new Blob([JSON.stringify(export_data, null, 2)], {
                    type: 'application/json'
                });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `column_preferences_${frappe.session.user}_${frappe.datetime.now_date()}.json`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
                
                frappe.msgprint({
                    title: __('Success'),
                    message: __('Preferences exported successfully'),
                    indicator: 'green'
                });
                
                return export_data;
            } else {
                throw new Error(response.message?.error || 'Failed to export preferences');
            }
            
        } catch (error) {
            console.error('Error exporting preferences:', error);
            frappe.msgprint({
                title: __('Error'),
                message: __('Failed to export preferences: {0}', [error.message]),
                indicator: 'red'
            });
            return null;
        }
    }
    
    /**
     * Import user preferences
     */
    async importPreferences(import_data, overwrite = false) {
        try {
            const response = await frappe.call({
                method: 'column_management.api.preference_manager.import_user_preferences',
                args: {
                    import_data: import_data,
                    overwrite: overwrite
                }
            });
            
            if (response.message && response.message.success) {
                // Clear all cache
                this.clearCache();
                
                frappe.msgprint({
                    title: __('Success'),
                    message: __('Imported {0} preferences successfully', [response.message.imported_count]),
                    indicator: 'green'
                });
                
                return response.message.imported_count;
            } else {
                throw new Error(response.message?.error || 'Failed to import preferences');
            }
            
        } catch (error) {
            console.error('Error importing preferences:', error);
            frappe.msgprint({
                title: __('Error'),
                message: __('Failed to import preferences: {0}', [error.message]),
                indicator: 'red'
            });
            return 0;
        }
    }
    
    /**
     * Set up automatic save listeners
     */
    setupAutoSaveListeners() {
        // Listen for column width changes
        $(document).on('column-width-changed', (e, data) => {
            if (data.doctype_name && data.fieldname && data.width) {
                const updates = {};
                updates[data.fieldname] = { width: data.width };
                this.updateColumnPreferences(data.doctype_name, updates);
            }
        });
        
        // Listen for column visibility changes
        $(document).on('column-visibility-changed', (e, data) => {
            if (data.doctype_name && data.fieldname && typeof data.visible !== 'undefined') {
                const updates = {};
                updates[data.fieldname] = { visible: data.visible };
                this.updateColumnPreferences(data.doctype_name, updates);
            }
        });
        
        // Listen for column order changes
        $(document).on('column-order-changed', (e, data) => {
            if (data.doctype_name && data.column_order) {
                const updates = {};
                data.column_order.forEach((fieldname, index) => {
                    updates[fieldname] = { order: index };
                });
                this.updateColumnPreferences(data.doctype_name, updates);
            }
        });
        
        // Listen for column pinning changes
        $(document).on('column-pinned-changed', (e, data) => {
            if (data.doctype_name && data.fieldname) {
                const updates = {};
                updates[data.fieldname] = { pinned: data.pinned };
                this.updateColumnPreferences(data.doctype_name, updates);
            }
        });
        
        // Listen for filter changes
        $(document).on('filters-changed', (e, data) => {
            if (data.doctype_name && data.filters) {
                this.updateFilterPreferences(data.doctype_name, {
                    active_filters: data.filters
                });
            }
        });
        
        // Listen for pagination changes
        $(document).on('pagination-changed', (e, data) => {
            if (data.doctype_name) {
                const updates = {};
                if (data.page_size) updates.page_size = data.page_size;
                if (data.current_page) updates.current_page = data.current_page;
                this.updatePaginationPreferences(data.doctype_name, updates);
            }
        });
    }
    
    /**
     * Get default preferences structure
     */
    getDefaultPreferences(doctype_name) {
        return {
            columns: {},
            filters: {
                active_filters: [],
                saved_filters: [],
                quick_filters: {}
            },
            pagination: {
                page_size: 20,
                current_page: 1
            },
            sorting: {
                field: 'modified',
                order: 'desc'
            },
            view_settings: {
                show_statistics: true,
                compact_view: false,
                auto_refresh: false,
                refresh_interval: 30
            },
            last_updated: frappe.datetime.now(),
            version: '1.0'
        };
    }
    
    /**
     * Cache management methods
     */
    setCache(key, value) {
        this.cache.set(key, {
            value: value,
            timestamp: Date.now()
        });
    }
    
    getFromCache(key) {
        const cached = this.cache.get(key);
        if (cached && (Date.now() - cached.timestamp) < this.cache_ttl) {
            return cached.value;
        }
        return null;
    }
    
    invalidateCache(key) {
        this.cache.delete(key);
    }
    
    clearCache() {
        this.cache.clear();
    }
    
    setupCacheCleanup() {
        // Clean up expired cache entries every 5 minutes
        setInterval(() => {
            const now = Date.now();
            for (const [key, cached] of this.cache.entries()) {
                if ((now - cached.timestamp) >= this.cache_ttl) {
                    this.cache.delete(key);
                }
            }
        }, 300000); // 5 minutes
    }
    
    /**
     * Enable/disable auto-save
     */
    setAutoSave(enabled) {
        this.auto_save_enabled = enabled;
        console.log('Auto-save', enabled ? 'enabled' : 'disabled');
    }
    
    /**
     * Set auto-save delay
     */
    setAutoSaveDelay(delay) {
        this.auto_save_delay = delay;
        console.log('Auto-save delay set to', delay, 'ms');
    }
    
    /**
     * Get preference summary
     */
    async getPreferenceSummary() {
        try {
            const response = await frappe.call({
                method: 'column_management.api.preference_manager.get_preference_summary'
            });
            
            if (response.message && response.message.success) {
                return response.message.summary;
            } else {
                throw new Error(response.message?.error || 'Failed to get preference summary');
            }
            
        } catch (error) {
            console.error('Error getting preference summary:', error);
            return [];
        }
    }
    
    /**
     * Bulk update multiple preference types
     */
    async bulkUpdatePreferences(doctype_name, updates) {
        try {
            const response = await frappe.call({
                method: 'column_management.api.preference_manager.bulk_update_preferences',
                args: {
                    updates: {
                        doctype_name: doctype_name,
                        ...updates
                    }
                }
            });
            
            if (response.message && response.message.success) {
                // Clear cache
                const cache_key = `prefs_${doctype_name}`;
                this.invalidateCache(cache_key);
                
                console.log('Bulk update completed for', doctype_name);
                return response.message.results;
            } else {
                throw new Error(response.message?.error || 'Failed to bulk update preferences');
            }
            
        } catch (error) {
            console.error('Error in bulk update preferences:', error);
            return null;
        }
    }
    
    // Synchronization and Backup Methods
    
    /**
     * Synchronize preferences across multiple sessions
     */
    async syncPreferencesAcrossSessions(doctype_name) {
        try {
            const response = await frappe.call({
                method: 'column_management.api.preference_manager.sync_preferences_across_sessions',
                args: {
                    doctype_name: doctype_name
                }
            });
            
            if (response.message && response.message.success) {
                console.log('Preferences synchronized for', doctype_name);
                
                // Clear cache to force refresh
                const cache_key = `prefs_${doctype_name}`;
                this.invalidateCache(cache_key);
                
                return true;
            } else {
                throw new Error(response.message?.error || 'Failed to synchronize preferences');
            }
            
        } catch (error) {
            console.error('Error synchronizing preferences:', error);
            return false;
        }
    }
    
    /**
     * Create a backup of user preferences
     */
    async createPreferenceBackup(doctype_name = null, backup_type = 'manual', description = null) {
        try {
            const response = await frappe.call({
                method: 'column_management.api.preference_manager.create_preference_backup',
                args: {
                    doctype_name: doctype_name,
                    backup_type: backup_type,
                    description: description
                }
            });
            
            if (response.message && response.message.success) {
                frappe.msgprint({
                    title: __('Success'),
                    message: __('Backup created successfully'),
                    indicator: 'green'
                });
                
                return response.message.backup_name;
            } else {
                throw new Error(response.message?.error || 'Failed to create backup');
            }
            
        } catch (error) {
            console.error('Error creating backup:', error);
            frappe.msgprint({
                title: __('Error'),
                message: __('Failed to create backup: {0}', [error.message]),
                indicator: 'red'
            });
            return null;
        }
    }
    
    /**
     * Restore preferences from a backup
     */
    async restorePreferenceBackup(backup_name) {
        try {
            const response = await frappe.call({
                method: 'column_management.api.preference_manager.restore_preference_backup',
                args: {
                    backup_name: backup_name
                }
            });
            
            if (response.message && response.message.success) {
                // Clear all cache
                this.clearCache();
                
                frappe.msgprint({
                    title: __('Success'),
                    message: __('Restored {0} preferences successfully', [response.message.restored_count]),
                    indicator: 'green'
                });
                
                // Refresh current page to show restored preferences
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
                
                return response.message.restored_count;
            } else {
                throw new Error(response.message?.error || 'Failed to restore backup');
            }
            
        } catch (error) {
            console.error('Error restoring backup:', error);
            frappe.msgprint({
                title: __('Error'),
                message: __('Failed to restore backup: {0}', [error.message]),
                indicator: 'red'
            });
            return 0;
        }
    }
    
    /**
     * Get list of preference backups
     */
    async getPreferenceBackups(doctype_name = null, limit = 10) {
        try {
            const response = await frappe.call({
                method: 'column_management.api.preference_manager.get_preference_backups',
                args: {
                    doctype_name: doctype_name,
                    limit: limit
                }
            });
            
            if (response.message && response.message.success) {
                return response.message.backups;
            } else {
                throw new Error(response.message?.error || 'Failed to get backups');
            }
            
        } catch (error) {
            console.error('Error getting backups:', error);
            return [];
        }
    }
    
    /**
     * Delete a preference backup
     */
    async deletePreferenceBackup(backup_name) {
        try {
            const response = await frappe.call({
                method: 'column_management.api.preference_manager.delete_preference_backup',
                args: {
                    backup_name: backup_name
                }
            });
            
            if (response.message && response.message.success) {
                frappe.msgprint({
                    title: __('Success'),
                    message: __('Backup deleted successfully'),
                    indicator: 'green'
                });
                
                return true;
            } else {
                throw new Error(response.message?.error || 'Failed to delete backup');
            }
            
        } catch (error) {
            console.error('Error deleting backup:', error);
            frappe.msgprint({
                title: __('Error'),
                message: __('Failed to delete backup: {0}', [error.message]),
                indicator: 'red'
            });
            return false;
        }
    }
    
    /**
     * Reset preferences to default configuration with backup
     */
    async resetToDefaultConfiguration(doctype_name) {
        try {
            const response = await frappe.call({
                method: 'column_management.api.preference_manager.reset_to_default_configuration',
                args: {
                    doctype_name: doctype_name
                }
            });
            
            if (response.message && response.message.success) {
                // Clear cache
                const cache_key = `prefs_${doctype_name}`;
                this.invalidateCache(cache_key);
                
                frappe.msgprint({
                    title: __('Success'),
                    message: __('Preferences reset to defaults successfully. Backup created: {0}', [response.message.backup_name]),
                    indicator: 'green'
                });
                
                return response.message.default_preferences;
            } else {
                throw new Error(response.message?.error || 'Failed to reset to defaults');
            }
            
        } catch (error) {
            console.error('Error resetting to defaults:', error);
            frappe.msgprint({
                title: __('Error'),
                message: __('Failed to reset preferences: {0}', [error.message]),
                indicator: 'red'
            });
            return null;
        }
    }
    
    /**
     * Get synchronization status
     */
    async getSyncStatus(doctype_name) {
        try {
            const response = await frappe.call({
                method: 'column_management.api.preference_manager.get_sync_status',
                args: {
                    doctype_name: doctype_name
                }
            });
            
            if (response.message && response.message.success) {
                return response.message.sync_status;
            } else {
                throw new Error(response.message?.error || 'Failed to get sync status');
            }
            
        } catch (error) {
            console.error('Error getting sync status:', error);
            return {
                is_synced: false,
                last_sync: null,
                sync_hash: null,
                error: error.message
            };
        }
    }
    
    /**
     * Force sync all sessions
     */
    async forceSyncAllSessions() {
        try {
            const response = await frappe.call({
                method: 'column_management.api.preference_manager.force_sync_all_sessions'
            });
            
            if (response.message && response.message.success) {
                frappe.msgprint({
                    title: __('Success'),
                    message: __('Synchronized {0} preferences across all sessions', [response.message.synced_count]),
                    indicator: 'green'
                });
                
                return response.message.synced_count;
            } else {
                throw new Error(response.message?.error || 'Failed to force sync');
            }
            
        } catch (error) {
            console.error('Error force syncing:', error);
            frappe.msgprint({
                title: __('Error'),
                message: __('Failed to sync preferences: {0}', [error.message]),
                indicator: 'red'
            });
            return 0;
        }
    }
    
    /**
     * Get preference statistics
     */
    async getPreferenceStatistics() {
        try {
            const response = await frappe.call({
                method: 'column_management.api.preference_manager.get_preference_statistics'
            });
            
            if (response.message && response.message.success) {
                return response.message.statistics;
            } else {
                throw new Error(response.message?.error || 'Failed to get statistics');
            }
            
        } catch (error) {
            console.error('Error getting statistics:', error);
            return {
                preference_count: 0,
                backup_count: 0,
                backup_types: {},
                latest_backup: null
            };
        }
    }
    
    /**
     * Set up real-time synchronization listeners
     */
    setupRealtimeSync() {
        // Listen for preference sync updates from other sessions
        frappe.realtime.on('preference_sync_update', (data) => {
            if (data.user === frappe.session.user) {
                console.log('Received preference sync update for', data.doctype_name);
                
                // Update cache with new preferences
                const cache_key = `prefs_${data.doctype_name}`;
                this.setCache(cache_key, data.preferences);
                
                // Trigger custom event for UI updates
                $(document).trigger('preferences-synced', {
                    doctype_name: data.doctype_name,
                    preferences: data.preferences,
                    sync_timestamp: data.sync_timestamp
                });
            }
        });
        
        console.log('Real-time sync listeners set up');
    }
    
    /**
     * Show backup management dialog
     */
    showBackupManagementDialog(doctype_name = null) {
        const dialog = new frappe.ui.Dialog({
            title: __('Preference Backup Management'),
            fields: [
                {
                    fieldtype: 'Section Break',
                    label: __('Create Backup')
                },
                {
                    fieldname: 'backup_doctype',
                    fieldtype: 'Data',
                    label: __('DocType'),
                    default: doctype_name,
                    read_only: doctype_name ? 1 : 0
                },
                {
                    fieldname: 'backup_description',
                    fieldtype: 'Small Text',
                    label: __('Description')
                },
                {
                    fieldtype: 'Section Break',
                    label: __('Existing Backups')
                },
                {
                    fieldname: 'backup_list',
                    fieldtype: 'HTML',
                    label: __('Backups')
                }
            ],
            primary_action_label: __('Create Backup'),
            primary_action: async (values) => {
                const backup_name = await this.createPreferenceBackup(
                    values.backup_doctype || null,
                    'manual',
                    values.backup_description
                );
                
                if (backup_name) {
                    dialog.hide();
                }
            }
        });
        
        // Load and display existing backups
        this.getPreferenceBackups(doctype_name).then(backups => {
            let html = '<div class="backup-list">';
            
            if (backups.length === 0) {
                html += '<p class="text-muted">' + __('No backups found') + '</p>';
            } else {
                backups.forEach(backup => {
                    html += `
                        <div class="backup-item" style="border: 1px solid #ddd; padding: 10px; margin: 5px 0; border-radius: 3px;">
                            <div class="backup-header" style="display: flex; justify-content: space-between; align-items: center;">
                                <strong>${backup.doctype_name}</strong>
                                <small class="text-muted">${frappe.datetime.str_to_user(backup.created_at)}</small>
                            </div>
                            <div class="backup-details">
                                <span class="badge badge-${backup.backup_type === 'manual' ? 'primary' : 'secondary'}">${backup.backup_type}</span>
                                ${backup.description ? '<p class="text-muted small">' + backup.description + '</p>' : ''}
                            </div>
                            <div class="backup-actions" style="margin-top: 5px;">
                                <button class="btn btn-xs btn-success restore-backup" data-backup="${backup.name}">
                                    ${__('Restore')}
                                </button>
                                <button class="btn btn-xs btn-danger delete-backup" data-backup="${backup.name}">
                                    ${__('Delete')}
                                </button>
                            </div>
                        </div>
                    `;
                });
            }
            
            html += '</div>';
            
            dialog.fields_dict.backup_list.$wrapper.html(html);
            
            // Add event listeners for backup actions
            dialog.fields_dict.backup_list.$wrapper.find('.restore-backup').on('click', async (e) => {
                const backup_name = $(e.target).data('backup');
                await this.restorePreferenceBackup(backup_name);
                dialog.hide();
            });
            
            dialog.fields_dict.backup_list.$wrapper.find('.delete-backup').on('click', async (e) => {
                const backup_name = $(e.target).data('backup');
                if (confirm(__('Are you sure you want to delete this backup?'))) {
                    const success = await this.deletePreferenceBackup(backup_name);
                    if (success) {
                        $(e.target).closest('.backup-item').remove();
                    }
                }
            });
        });
        
        dialog.show();
    }
}

// Create global instance
window.column_management_preference_manager = new PreferenceManager();

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PreferenceManager;
}