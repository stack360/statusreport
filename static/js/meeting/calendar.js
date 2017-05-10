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
  $('.time-input').clockpicker({
    autoclose: true
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
      var attendees = calEvent.attendees.join(', ');
      var date = calEvent.start_time.split('T')[0];
      var start_time = calEvent.start_time.split('T')[1];
      var end_time = calEvent.end_time.split('T')[1];

      $('#date-span').text(date);
      $('#start-time-span').text(start_time);
      $('#end-time-span').text(end_time);
      $('#topic-td').text(calEvent.topic);
      $('#project-td').text(calEvent.project);
      $('#attendees-td').text(attendees)

      $('#meeting-show-modal').modal('show');
    }
  });

  // bind form save event
  $('#meeting-save-btn').click(function(){
    $('#attendee-input').val( $('#attendee-select').val().join(',') )
    $('#meeting-form').submit();
  })

})
