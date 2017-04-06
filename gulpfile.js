var gulp = require('gulp'),
  sass = require('gulp-sass'),
  autoprefixer = require('gulp-autoprefixer'),
  minifycss = require('gulp-minify-css'),
  rename = require('gulp-rename'),
  shell = require('gulp-shell');

var staticRoot = 'static/';
var cssRoot = staticRoot +'css';
var sassRoot = staticRoot + 'sass';

gulp.task('styles', function() {
  gulp.src(sassRoot+'/*.scss')
    .pipe(sass({
      style: 'expanded',
      "sourcemap=none": true
    }))
    .pipe(autoprefixer('last 2 version', 'safari 5', 'ie 8', 'ie 9', 'opera 12.1'))
    .pipe(gulp.dest(cssRoot))
    .pipe(rename({
      suffix: '.min'
    }))
    .pipe(minifycss())
    .pipe(gulp.dest(cssRoot));
});

gulp.task('watch', function() {
  gulp.watch(sassRoot+'/**', ['styles']);
});

gulp.task('default', ['styles', 'watch'], function() {});
