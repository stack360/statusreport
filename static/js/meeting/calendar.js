$(function(){
  // initialize modal for meeting creation
  $('#create-meeting-btn').click(function(){
    $('#meeting-modal').modal('show');

  });

  // initialize date picker for date input
  $('#date-input').datepicker({
    autoclose: true,
    todayHighlight: true,
    startDate: new Date()
  });

  // initialize time picker
  $('#time-input').clockpicker({
    autoclose: true
  });

  // initialize select2
  $('#user-select').select2({
    theme: 'bootstrap',
    width: '100%',
    closeOnSelect: false,
    dropdownAdapter: $.fn.select2.amd.require('select2/selectAllAdapter')
  });

  // initialize full calendar
  $('#calendar').fullCalendar({
    header: {
      left: 'month,agendaWeek,agendaDay,listWeek',
      center: 'title',
      right: 'prev,next'
    },
    navLinks: true, // can click day/week names to navigate views
    editable: true,
    eventLimit: true, // allow "more" link when too many events
    eventSources:[{
      url: '/meeting/source'
    }],
    eventClick:function(calEvent, jsEvent, view) {
      console.log(calEvent.title);
      console.log(jsEvent);
      console.log(view.name);
    }
  });

  // bind form save event
  $('#meeting-save-btn').click(function(){
    $('#user-input').val( $('#user-select').val().join(',') )
    $('#meeting-form').submit();
  })

})
