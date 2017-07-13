$(function(){

  $('#members-select').change(function(){
    var selected_members = $('#members-select').val();
    $('#coordinator-select').html('<option value="">Please Select Coordinator</option>');
    for (i in selected_members) {
      var member = selected_members[i];
      var fullname = $('option[value="'+member+'"]').text();
      $('#coordinator-select').append('<option value="'+member+'"> '+fullname+'</option>')
    }
  });
  $('#save-btn').click(function(){
    $('#members-input').val($('#members-select').val().join(','))
    $('#coordinator-input').val($('#coordinator-select').val())
    $('#project-form').submit()
  })
})
