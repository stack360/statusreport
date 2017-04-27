$(function(){
  // fadein item
  $('.item').mouseenter(function() {
    $(this).find('.actions').fadeIn(500);
  });

  $('.item').mouseleave(function() {
    $(this).find('.actions').fadeOut(200);
  });

});
