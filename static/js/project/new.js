$(function(){
  $('#members-select').select2({
    theme: 'bootstrap',
    width: '100%'
  });

  $('#save-btn').click(function(){
    $('#members-input').val($('#members-select').val().join(','))
    $('#project-form').submit()
  })
})
