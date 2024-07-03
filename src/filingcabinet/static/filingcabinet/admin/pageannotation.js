window.django.jQuery(function () {
  var $ = window.django.jQuery
  var left = null
  var top = null
  var pageRect = $('#page_rect')
  var image = $('#page_image')
  var naturalWidth = image[0].naturalWidth
  var naturalHeight = image[0].naturalHeight
  function loaded() {
    naturalWidth = image[0].naturalWidth
    naturalHeight = image[0].naturalHeight
  }
  if (image[0].complete) {
    loaded()
  } else {
    image.on('load', loaded)
  }
  image.on('mousedown', function (e) {
    if (left !== null) {
      var offsetWidth = image[0].offsetWidth
      var offsetHeight = image[0].offsetHeight
      var ratioX = naturalWidth / offsetWidth
      var ratioY = naturalHeight / offsetHeight
      $('#id_left').val(Math.round(left * ratioX))
      $('#id_top').val(Math.round(top * ratioY))
      var w = Math.round((e.offsetX - left) * ratioX)
      var h = Math.round((e.offsetY - top) * ratioY)
      $('#id_width').val(w)
      $('#id_height').val(h)

      left = null
      top = null
      return
    }
    left = e.offsetX
    top = e.offsetY
    pageRect.css('left', left)
    pageRect.css('top', top)
    pageRect.css('width', left)
    pageRect.css('height', top)
  })
  image.on('mousemove', function (e) {
    if (left === null) {
      return
    }
    pageRect.css('width', e.offsetX - left)
    pageRect.css('height', e.offsetY - top)
  })
})


window.django.jQuery(function () {
  var $ = window.django.jQuery

  var image = $('#annotation_image')
  if (image.length === 0) {
    return
  }

  function drawHighlightRects() {
    image.parent().find('div').remove()
    highlights.forEach(function(h) {
      var div = $('<div>').css({
        position: 'absolute',
        'pointer-events': 'none',
        'background-color': h.color,
        left: h.left / ratioX,
        top: h.top / ratioY,
        width: h.width / ratioX,
        height: h.height / ratioY
      })
      image.parent().append(div)
    })
  }

  var highlightJson = $('#id_highlight').val()
  var highlights = []
  if (highlightJson.length) {
    highlights = JSON.parse(highlightJson)
  }
  var currentHighlight = null

  var naturalWidth = image[0].naturalWidth
  var naturalHeight = image[0].naturalHeight
  var ratioX, ratioY

  function loaded() {
    naturalWidth = image[0].naturalWidth
    naturalHeight = image[0].naturalHeight
    var offsetWidth = image[0].offsetWidth
    var offsetHeight = image[0].offsetHeight
    ratioX = naturalWidth / offsetWidth
    ratioY = naturalHeight / offsetHeight
    drawHighlightRects()
  }
  if (image[0].complete) {
    loaded()
  } else {
    image.on('load', loaded)
  }

  image.on('mousedown', function (e) {
    if (currentHighlight !== null) {
      var w = Math.round((e.offsetX - currentHighlight.left) * ratioX)
      var h = Math.round((e.offsetY - currentHighlight.top) * ratioY)
      var color = $('#annotationcolor').val()
      highlights.push({
        left: Math.round(currentHighlight.left * ratioX),
        top: Math.round(currentHighlight.top * ratioY),
        width: w,
        height: h,
        color: color,
        type: 'highlight'
      })
      $('#id_highlight').val(JSON.stringify(highlights))
      currentHighlight = null
      drawHighlightRects()
      return
    }
    currentHighlight = {
      left: e.offsetX,
      top: e.offsetY  
    }
  })
})
