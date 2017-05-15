/*
     select-all / select-none Plugin for Select2
*/
$.fn.select2.amd.define('select2/selectAllAdapter', [
    'select2/utils',
    'select2/dropdown',
    'select2/dropdown/attachBody'
], function (Utils, Dropdown, AttachBody) {

    function SelectAll() { }
    SelectAll.prototype.render = function (decorated) {
        var self = this,
            $rendered = decorated.call(this),
            $selectAll = $(
                '<button class="btn btn-sm btn-secondary" type="button" style="margin-left:6px;"><i class="fa fa-check-square-o"></i> Select All</button>'
            ),
            $unselectAll = $(
                '<button class="btn btn-sm btn-secondary" type="button" style="margin-left:6px;"><i class="fa fa-square-o"></i> Unselect All</button>'
            ),
            $btnContainer = $('<div style="margin-top:5px;margin-bottom:8px;">').append($selectAll).append($unselectAll);
        if (!this.$element.prop("multiple")) {
            // this isn't a multi-select -> don't add the buttons!
            return $rendered;
        }
        $rendered.find('.select2-dropdown').prepend($btnContainer);
        $selectAll.on('click', function (e) {
            var $results = $rendered.find('.select2-results__option[aria-selected=false]');
            $results.each(function () {
                self.trigger('select', {
                    data: $(this).data('data')
                });
            });
            self.trigger('close');
        });
        $unselectAll.on('click', function (e) {
            var $results = $rendered.find('.select2-results__option[aria-selected=true]');
            $results.each(function () {
                self.trigger('unselect', {
                    data: $(this).data('data')
                });
            });
            self.trigger('close');
        });
        return $rendered;
    };

    return Utils.Decorate(
        Utils.Decorate(
            Dropdown,
            AttachBody
        ),
        SelectAll
    );

});

// ready function
$(function () {
  // global initialization for tooltip
  $('[data-toggle="tooltip"]').tooltip()

  // timestamp to fromNow
  $('.timestamp').each(function(){
    var m = moment( $(this).text(), 'MM/DD/YYYY hh:mm' );
    $(this).text( m.fromNow() )
  });

  // global initialization for multiple select2
  $('.select2-multi').select2({
    theme: 'bootstrap',
    width: '100%',
    closeOnSelect: false,
    dropdownAdapter: $.fn.select2.amd.require('select2/selectAllAdapter')
  });

  $('[data-bg-color]').each(function(){
    var color = $(this).data('bg-color');
    $(this).css('background', color);
  })

})
