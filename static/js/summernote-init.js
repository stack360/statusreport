$(function(){
  config = {
    height: 400,
    toolbar: [
    ['style', ['style']],
    ['font', ['bold', 'italic', 'underline']],
    ['fontsize', ['fontsize']],

    ['color', ['color']],
    ['para', ['ul', 'ol', 'paragraph']],
    ['table', ['table']],
    ['insert', ['link', 'hr']]
    //['view', ['codeview']]
    ]
  };

  $('#done-textarea').summernote(config);
  $('#todo-textarea').summernote(config);

  $('#save-btn').click(function(){
    $('#todo-input').val($('#todo-textarea').summernote('code'));
    $('#done-input').val($('#done-textarea').summernote('code'));
    if ($('#project-input').length >0){
      $('#projects-input').val($('.projects-checkbox :checked').map(function(){return $(this).val();}).get().join());
    }
    $('form').submit();
  });

  $('#draft-btn').click(function(){
    $('#todo-input').val($('#todo-textarea').summernote('code'));
    $('#done-input').val($('#done-textarea').summernote('code'));
    $('#draft-input').val('True');
    $('form').submit();
  });
})
