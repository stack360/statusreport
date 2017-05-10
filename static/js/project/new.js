$(function(){
  $('#save-btn').click(function(){
    $('#members-input').val($('#members-select').val().join(','))
    $('#project-form').submit()
  })
})
