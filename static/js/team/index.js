$(function(){
  $('#team-create-save-btn').click(function(){
    $('#members-input').val($('#members-select').val());
    $('#team-create-form').submit();
  })
})
