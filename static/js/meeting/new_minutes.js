$(function(){
  var btns = [
        'formatting',
        'btnGrp-semantic',
        'removeformat',
        'link',
        'btnGrp-justify',
        'btnGrp-lists'
    ];
  $('#minutes-textarea').trumbowyg({
    btns: btns
  });

  $('#save-btn').click(function(){
    $('#minutes-input').val($('#minutes-textarea').trumbowyg('html'))
    $('#minutes-form').submit();
  });
})
