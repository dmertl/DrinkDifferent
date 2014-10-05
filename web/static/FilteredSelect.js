/**
 * A utility to create a select element whose options are populated based on the value of another select element.
 *
 * Uses a map of filter value -> dictionary of optionValue: optionTitle. When filter is changed the new value is looked
 * up in the map. If present the filtered selected is emptied and updated with the options from the map. If the filter
 * has no value or the map is missing, the filtered select will only have a "---" option.
 */
FilteredSelect = function($) {
    /**
     * Select element doing the filtering.
     *
     * @type {jQuery}
     */
    var filter;
    /**
     * Select element being filtered.
     *
     * @type {jQuery}
     */
    var filtered;
    /**
     * Map of filter value -> dictionary of optionValue: optionTitle
     * @type {Object}
     */
    var map = {};

    /**
     * Updated the filtered select element with the corresponding values from the map.
     */
    var updateFilteredSelect = function() {
        var val = filter.val();
        filtered.empty();
        if(val && map.hasOwnProperty(val)) {
            var options = map[val];
            $.each(options, function(value, name) {
                filtered.append($('<option />').val(value).html(name))
            });
        } else {
            //Log an error that selected value was missing in map
            if(val) {
                console.error('(S5.FilteredSelect) Value "' + val + '" is not set in option map.');
            }
            filtered.append($('<option value="">---</option>'));
        }
        //Trigger change event
        filtered.trigger('change');
    };

    /**
     * Initialize filtered select.
     *
     * @param {HTMLElement|jQuery} filterElement   Element doing the filtering.
     * @param {HTMLElement|jQuery} filteredElement Element being filtered.
     * @param {Object}             optionMap       Map of filter element value to dictionary of options for filtered.
     * @param {string=}            filteredValue   Initial value for filtered select (optional).
     */
    var init = function(filterElement, filteredElement, optionMap, filteredValue) {
        filter = $(filterElement);
        filtered = $(filteredElement);
        map = optionMap;
        //When filter changes update the options in filtered
        filter.on('change', function() {
            updateFilteredSelect();
        });
        //Trigger initial update of filtered select
        updateFilteredSelect();
        //Set filtered select value if provided
        if(filteredValue) {
            filtered.val(filteredValue);
        }
    };

    return {
        init: init
    };

}(jQuery);
