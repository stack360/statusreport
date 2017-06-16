$(function(){
  $('.tag-editor').tagEditor({
    initialTags: [],
    delimiter: ', ', /* space and comma */
    placeholder: ''
  });

  $('#invite-btn').click(function(){
    var emails = $('#email-input').val();
    $('#email-input').val();
    $('#invite-modal').modal('hide');
    $.post('/invite', {emails:emails}, function(data){
      swal("Invitation Sent!", "", "success");
    })
    .fail(function() {
      swal("Invitation not sent", "Something went wrong ...", "error");
    });
  })
})
