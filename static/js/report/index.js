$(function(){
  var width = $('.container').innerWidth();
  $('.card-masonry').masonry({
    // options
    itemSelector: '.card',
    gutter: 20
  });
})
