$(function(){
  $('.change-logo-btn').click(function(){
    // prepare project_id for modal
    var pid = $(this).data('project_id');
    $('#project-id-input').val(pid);

    // prepare img_src for modal
    var url = $(this).data('img_src')
    $('#change-logo-current').attr('src', url);

    // show modal
    $('#change-logo-modal').modal('show');
  });

  $('#change-logo-save-btn').click(function(){
    $('#change-logo-form').submit();
  })

  // masonry with three columns
  var width = $('.container').innerWidth();
  $('.card-masonry').masonry({
    // options
    itemSelector: '.card',
    gutter:15
  });

})
