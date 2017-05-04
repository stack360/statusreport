$(function(){
  // masonry with 2 columns
  var width = $('.container').innerWidth();
  $('.card-masonry').masonry({
    itemSelector: '.card',
    gutter: 20
  });
})
