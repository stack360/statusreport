$(function(){
  var btns = [
        'formatting',
        'btnGrp-semantic',
        'removeformat',
        'link',
        'btnGrp-justify',
        'btnGrp-lists'
    ];
  $('#digest-textarea').trumbowyg({
    btns: btns
  });

  $('#save-btn').click(function(){
    $('#digest-input').val($('#digest-textarea').trumbowyg('html'));
    $('#digest-form').submit();
  });
})
