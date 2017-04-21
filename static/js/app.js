$(function(){

  var mc = $('.masonry-container');
  mc.masonry({
    columnWidth: '.item',
    itemSelector: '.item'
  })

  // item
  $('.item').mouseenter(function() {
    $(this).find('.actions').fadeIn(500);
  });

  $('.item').mouseleave(function() {
    $(this).find('.actions').fadeOut(200);
  });

});
