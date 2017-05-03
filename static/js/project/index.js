$(function(){
  $('.change-logo-btn').click(function(){
    var pid = $(this).data('project_id');
    // prepare value for modal
    $('#project-id-input').val(pid);
    var url = $(this).data('img_src')
    $('#change-logo-current').attr('src', url);
    $('#change-logo-modal').modal('show');
  });

  $('#change-logo-save-btn').click(function(){
    $('#change-logo-form').submit();
  })
})
