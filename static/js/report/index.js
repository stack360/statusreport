$(function(){
  // masonry with 2 columns
  var width = $('.container').innerWidth();
  $('.card-masonry').masonry({
    itemSelector: '.card',
    gutter: 20
  });


  $('.filter').change(function(){
    var user_filter = $('#user-filter').val();
    var project_filter = $('#project-filter').val();
    var time_filter = $('#time-filter').val();
    var params = [
      project_filter ? 'project='+project_filter : '',
      user_filter ? 'user='+user_filter : '',
      time_filter ? 'time='+time_filter : ''
    ]
    params = params.filter(Boolean);
    var querystr = '?'+params.join('&');
    window.location.href= window.location.pathname + querystr;

  })
})
