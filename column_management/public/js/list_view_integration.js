/**
 * List View Integration - Integrates preference management with Frappe List Views
 * Copyright (c) 2024, ERPNext Column Management Team
 */

frappe.provide('column_management.list_view');

column_management.list_view = {

    /**
     * Initialize list view integration
     */
    init: function () {
        // Wait for preference manager to be available
        if (typeof window.column_management_preference_manager === 'undefined') {
            setTimeout(() => this.init(), 100);
            return;
        }

        this.preference_manager = window.column_management_preference_manager;
        this.setup_list_view_hooks();
        console.log('List view integration initialized');
    },

    /**
     * Set up hooks for list view events
     */
    setup_list_view_hooks: function () {
        const self = this;

        // Hook into list view rendering
        const original_render = frappe.views.ListView.prototype.render;
        frappe.views.ListView.prototype.render = function () {
            const result = original_render.apply(this, arguments);

            // Restore preferences after rendering
            if (this.doctype) {
                self.restore_list_view_preferences(this);
            }

            return result;
        };

        // Hook into column width changes
        $(document).on('mouseup', '.list-row-col', function (e) {
            const $col = $(this);
            const $list_view = $col.closest('.frappe-list');

            if ($list_view.length) {
                const doctype = $list_view.data('doctype');
                const fieldname = $col.data('fieldname');
                const width = $col.width();

                if (doctype && fieldname && width) {
                    // Trigger column width change event
                    $(document).trigger('column-width-changed', {
                        doctype_name: doctype,
                        fieldname: fieldname,
                        width: width
                    });
                }
            }
        });

        // Hook into filter changes
        const original_set_filter = frappe.views.ListView.prototype.set_filter;
        frappe.views.ListView.prototype.set_filter = function (fieldname, operator, value) {
            const result = original_set_filter.apply(this, arguments);

            // Trigger filter change event
            if (this.doctype) {
                $(document).trigger('filters-changed', {
                    doctype_name: this.doctype,
                    filters: this.get_filters_for_args()
                });
            }

            return result;
        };

        // Hook into pagination changes
        const original_set_page = frappe.views.ListView.prototype.set_page;
        frappe.views.ListView.prototype.set_page = function (page) {
            const result = original_set_page.apply(this, arguments);

            // Trigger pagination change event
            if (this.doctype) {
                $(document).trigger('pagination-changed', {
                    doctype_name: this.doctype,
                    current_page: this.start / this.page_length + 1,
                    page_size: this.page_length
                });
            }

            return result;
        };

        // Hook into page length changes
        const original_set_page_length = frappe.views.ListView.prototype.set_page_length;
        frappe.views.ListView.prototype.set_page_length = function (page_length) {
            const result = original_set_page_length.apply(this, arguments);

            // Trigger pagination change event
            if (this.doctype) {
                $(document).trigger('pagination-changed', {
                    doctype_name: this.doctype,
                    current_page: this.start / this.page_length + 1,
                    page_size: this.page_length
                });
            }

            return result;
        };
    },

    /**
     * Restore list view preferences
     */
    restore_list_view_preferences: async function (list_view) {
        try {
            const preferences = await this.preference_manager.getUserPreferences(list_view.doctype);

            if (preferences) {
                // Restore column preferences
                this.restore_column_preferences(list_view, preferences.columns);

                // Restore filter preferences
                this.restore_filter_preferences(list_view, preferences.filters);

                // Restore pagination preferences
                this.restore_pagination_preferences(list_view, preferences.pagination);

                // Restore sorting preferences
                this.restore_sorting_preferences(list_view, preferences.sorting);

                console.log('Restored preferences for', list_view.doctype);
            }

        } catch (error) {
            console.error('Error restoring list view preferences:', error);
        }
    },

    /**
     * Restore column preferences
     */
    restore_column_preferences: function (list_view, column_prefs) {
        if (!column_prefs || typeof column_prefs !== 'object') {
            return;
        }

        try {
            // Apply column widths
            for (const fieldname in column_prefs) {
                const pref = column_prefs[fieldname];

                if (pref.width) {
                    const $col = list_view.$result.find(`[data-fieldname="${fieldname}"]`);
                    if ($col.length) {
                        $col.css('width', pref.width + 'px');
                    }
                }

                // Apply column visibility
                if (typeof pref.visible !== 'undefined') {
                    const $col = list_view.$result.find(`[data-fieldname="${fieldname}"]`);
                    if ($col.length) {
                        if (pref.visible) {
                            $col.show();
                        } else {
                            $col.hide();
                        }
                    }
                }
            }

        } catch (error) {
            console.error('Error restoring column preferences:', error);
        }
    },

    /**
     * Restore filter preferences
     */
    restore_filter_preferences: function (list_view, filter_prefs) {
        if (!filter_prefs || !filter_prefs.active_filters) {
            return;
        }

        try {
            // Apply saved filters
            const active_filters = filter_prefs.active_filters;

            if (Array.isArray(active_filters) && active_filters.length > 0) {
                // Clear existing filters first
                list_view.filter_area.clear();

                // Apply each filter
                active_filters.forEach(filter => {
                    if (filter.fieldname && filter.operator && filter.value) {
                        list_view.filter_area.add(
                            list_view.doctype,
                            filter.fieldname,
                            filter.operator,
                            filter.value
                        );
                    }
                });

                // Refresh the list
                list_view.refresh();
            }

        } catch (error) {
            console.error('Error restoring filter preferences:', error);
        }
    },

    /**
     * Restore pagination preferences
     */
    restore_pagination_preferences: function (list_view, pagination_prefs) {
        if (!pagination_prefs) {
            return;
        }

        try {
            // Apply page size
            if (pagination_prefs.page_size && pagination_prefs.page_size !== list_view.page_length) {
                list_view.page_length = pagination_prefs.page_size;

                // Update page length selector if it exists
                const $page_length_select = list_view.$paging_area.find('.list-paging-area select');
                if ($page_length_select.length) {
                    $page_length_select.val(pagination_prefs.page_size);
                }
            }

            // Apply current page (but don't navigate automatically to avoid confusion)
            // The user can navigate manually if needed

        } catch (error) {
            console.error('Error restoring pagination preferences:', error);
        }
    },

    /**
     * Restore sorting preferences
     */
    restore_sorting_preferences: function (list_view, sorting_prefs) {
        if (!sorting_prefs) {
            return;
        }

        try {
            // Apply sorting
            if (sorting_prefs.field && sorting_prefs.order) {
                const sort_by = sorting_prefs.field;
                const sort_order = sorting_prefs.order;

                // Update list view sort settings
                list_view.sort_by = sort_by;
                list_view.sort_order = sort_order;

                // Update sort selector if it exists
                const $sort_selector = list_view.$sort_selector;
                if ($sort_selector && $sort_selector.length) {
                    $sort_selector.find('select').val(sort_by);
                    $sort_selector.find('.sort-order').removeClass('fa-sort-asc fa-sort-desc');
                    $sort_selector.find('.sort-order').addClass(
                        sort_order === 'asc' ? 'fa-sort-asc' : 'fa-sort-desc'
                    );
                }
            }

        } catch (error) {
            console.error('Error restoring sorting preferences:', error);
        }
    },

    /**
     * Save current list view state as preferences
     */
    save_current_state: async function (doctype) {
        try {
            const list_view = frappe.views.list_view[doctype];
            if (!list_view) {
                return;
            }

            // Collect current state
            const preferences = {
                columns: this.collect_column_preferences(list_view),
                filters: this.collect_filter_preferences(list_view),
                pagination: this.collect_pagination_preferences(list_view),
                sorting: this.collect_sorting_preferences(list_view),
                view_settings: this.collect_view_settings(list_view)
            };

            // Save preferences
            await this.preference_manager.saveUserPreferences(doctype, preferences);

            console.log('Saved current state for', doctype);

        } catch (error) {
            console.error('Error saving current state:', error);
        }
    },

    /**
     * Collect column preferences from current list view
     */
    collect_column_preferences: function (list_view) {
        const column_prefs = {};

        try {
            list_view.$result.find('.list-row-col').each(function () {
                const $col = $(this);
                const fieldname = $col.data('fieldname');

                if (fieldname) {
                    column_prefs[fieldname] = {
                        visible: $col.is(':visible'),
                        width: $col.width(),
                        order: $col.index()
                    };
                }
            });

        } catch (error) {
            console.error('Error collecting column preferences:', error);
        }

        return column_prefs;
    },

    /**
     * Collect filter preferences from current list view
     */
    collect_filter_preferences: function (list_view) {
        const filter_prefs = {
            active_filters: [],
            saved_filters: [],
            quick_filters: {}
        };

        try {
            // Get active filters
            if (list_view.filter_area && list_view.filter_area.get) {
                const filters = list_view.filter_area.get();
                filter_prefs.active_filters = filters.map(filter => ({
                    fieldname: filter[1],
                    operator: filter[2],
                    value: filter[3]
                }));
            }

        } catch (error) {
            console.error('Error collecting filter preferences:', error);
        }

        return filter_prefs;
    },

    /**
     * Collect pagination preferences from current list view
     */
    collect_pagination_preferences: function (list_view) {
        const pagination_prefs = {};

        try {
            pagination_prefs.page_size = list_view.page_length || 20;
            pagination_prefs.current_page = Math.floor(list_view.start / list_view.page_length) + 1;

        } catch (error) {
            console.error('Error collecting pagination preferences:', error);
        }

        return pagination_prefs;
    },

    /**
     * Collect sorting preferences from current list view
     */
    collect_sorting_preferences: function (list_view) {
        const sorting_prefs = {};

        try {
            sorting_prefs.field = list_view.sort_by || 'modified';
            sorting_prefs.order = list_view.sort_order || 'desc';

        } catch (error) {
            console.error('Error collecting sorting preferences:', error);
        }

        return sorting_prefs;
    },

    /**
     * Collect view settings from current list view
     */
    collect_view_settings: function (list_view) {
        const view_settings = {};

        try {
            // Collect various view settings
            view_settings.show_statistics = true; // Default
            view_settings.compact_view = false; // Default
            view_settings.auto_refresh = false; // Default
            view_settings.refresh_interval = 30; // Default

        } catch (error) {
            console.error('Error collecting view settings:', error);
        }

        return view_settings;
    }
};

// Initialize when DOM is ready
$(document).ready(function () {
    column_management.list_view.init();
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = column_management.list_view;
}