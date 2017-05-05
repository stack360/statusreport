$(function(){
  $('#calendar').fullCalendar({
    header: {
      left: 'prev,next',
      center: 'title',
      right: 'month,agendaWeek,agendaDay,listWeek'
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

})
