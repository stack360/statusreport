$(function(){
  $('#team-create-save-btn').click(function(){
    $('#members-input').val($('#members-select').val());
    $('#team-create-form').submit();
  })

  $('#invite-members-save-btn').click(function(){
    $('#invite-members-input').val($('#invite-members-select').val());
    $('#invite-members-form').submit();
  })

})
