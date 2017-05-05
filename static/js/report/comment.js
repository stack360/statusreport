$(function(){
  var btns = [
        'formatting',
        'btnGrp-semantic',
        'removeformat',
        'link',
        'btnGrp-justify',
        'btnGrp-lists'
    ];
  $('#comment-textarea').trumbowyg({
    btns: btns
  });

  $('#comment-btn').click(function(){
    $('#comment-input').val($('#comment-textarea').trumbowyg('html'));
    $('#comment-form').submit();
  });
})
