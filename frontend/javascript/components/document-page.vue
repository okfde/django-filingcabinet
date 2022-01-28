<template>
  <div class="row justify-content-center">
    <div :class="{'col-8': showAnnotations, 'col-auto': !showAnnotations}">
      <div class="page-wrapper">
        <div
          :id="pageId"
          class="page"
        > 
          <picture
            v-if="page.image_url"
            v-show="!imageLoaded"
          >
            <source
              v-for="format in supportedFormats"
              :key="format"
              :srcset="previewImageUrl + '.' + format"
              :type="'image/' + format"
            >
            <img
              :src="previewImageUrl"
              :alt="pageLabel"
              :style="{'width': page.zoomedWidth + 'px', height: imageHeight + 'px'}"
              class="page-image-placeholder"
              draggable="false"
              loading="lazy"
            >
          </picture>
          <picture>
            <source
              v-for="pic in imageSources"
              :key="pic.type"
              :srcset="pic.srcset"
              :type="pic.type"
            >
            <img
              v-if="page.image_url"
              v-show="imageLoaded"
              ref="image"
              :src="imageUrl"
              :srcset="imageSrcSet"
              :alt="pageLabel"
              :style="{'width': page.zoomedWidth + 'px'}"
              class="page-image"
              draggable="false"
              :class="{'annotation-form': showAnnotationForm}"
              @load="onImageLoad"
            >
          </picture>
          <div
            class="pdf-layer"
            :style="imageOverlayStyle"
          >
            <div
              ref="textLayer"
              class="text-layer"
              :style="imageOverlayStyle"
            />
            <div
              ref="annotationLayer"
              class="annotation-layer"
              :style="imageOverlayStyle"
            />
          </div>

          <div
            v-if="showText && !showAnnotationForm"
            class="page-text"
          >
            <pre :style="imageOverlayStyle">
              {{ page.content }}
            </pre>
          </div>
          <div
            v-if="showAnnotationForm"
            class="annotation-rect-container"
            :style="imageOverlayStyle"
            @mousedown="mouseDown"
            @mousemove="mouseMove"
            @mouseup="mouseUp"
          >
            <div
              v-if="annotationRect"
              :style="annotationRectStyle"
              class="annotation-rect"
            />
          </div>
          <div
            v-if="showAnnotations && imageLoaded && !showText && !showAnnotationForm && annotationsWithRect.length"
            class="annotation-overlay-container"
            :style="imageOverlayStyle"
          >
            <page-annotation-overlay
              v-for="annotation in annotationsWithRect"
              :key="annotation.id"
              :page="page"
              :annotation="annotation"
              :current-annotation="currentAnnotation"
              @currentannotation="annotationRectClicked"
            />
          </div>
        </div>
        <p class="page-number">
          {{ page.number }}
        </p>
      </div>
    </div>

    <div
      v-if="showAnnotations"
      class="col-4 bg-light annotation-sidebar"
    >
      <page-annotations
        :annotations="annotations"
        :page="page"
        :current-annotation="currentAnnotation"
        :can-annotate="canAnnotate"
        :active-annotation-form="annotationForm"
        @currentannotation="$emit('currentannotation', $event)"
        @activateannotationform="$emit('activateannotationform', $event)"
        @deleteannotation="$emit('deleteannotation', $event)"
      />
    </div>
  </div>
</template>

<script>

import PageAnnotations from './document-annotations.vue'
import PageAnnotationOverlay from './document-page-annotationoverlay.vue'

import {FilingcabinetLinkService} from '../lib/pdfjs-utils.js'

const PAGE_SIZES = {
  'small': 180,
  'normal': 700,
  'large': 1000,
}


export default {
  name: 'DocumentPage',
  components: {
    PageAnnotationOverlay,
    PageAnnotations
  },
  props: {
    page: {
      type: Object,
      required: true
    },
    annotations: {
      type: Array,
      required: true
    },
    showText: {
      type: Boolean,
      required: true
    },
    showAnnotations: {
      type: Boolean,
      required: true
    },
    currentAnnotation: {
      type: Object,
      default: null
    },
    annotationForm: {
      type: Object,
      default: null
    },
    canAnnotate: {
      type: Boolean,
      default: false
    },
    pdfDocument: {
      type: Object,
      default: null
    },
    supportedFormats: {
      type: Array,
      default: () => []
    }
  },
  data () {
    return {
      imageLoaded: false,
      textLoaded: false,
      annotationRect: null,
      annotating: false,
    }
  },
  computed: {
    i18n () {
      return this.$root.config.i18n
    },
    annotationsWithRect () {
      return this.annotations.filter((a) => a.left !== null)
    },
    imageSize () {
      if (this.page.zoomedWidth <= 700) {
        return 'normal'
      } else if (this.page.zoomedWidth <= 1000) {
        return 'large'
      }
      return 'original'
    },
    imageSizeRetina () {
      if (this.page.zoomedWidth <= 1400) {
        return 'normal'
      } else if (this.page.zoomedWidth <= 1000) {
        return 'large'
      }
      return 'original'
    },
    imageUrl () {
      return this.page.image_url.replace(/\{size\}/, this.imageSize)
    },
    previewImageUrl () {
      return this.page.image_url.replace(/\{size\}/, "small")
    },
    imageSources () {
      return this.supportedFormats.map(format => {
        let srcset = this.imageSrcSet
        srcset = srcset.replace(/\.png/g, `.png.${format}`)
        return {
          srcset: srcset,
          type: `image/${format}`
        }
      })
    },
    imageSrcSet () {
      let srcset = []
      for (let size in PAGE_SIZES) {
        srcset.push(`${this.page.image_url.replace(/\{size\}/, size)} ${PAGE_SIZES[size]}w`)
      }
      return srcset.join(', ')
    },
    pageId () {
      return `page-${this.page.number}`
    },
    pageLabel () {
      return this.page.number
    },
    showAnnotationForm () {
      if (this.annotationForm === null) { return false }
      return this.annotationForm.number === this.page.number
    },
    annotationRectStyle () {
      if (!this.annotationRect) {
        return {}
      }
      return {
        left: this.annotationRect.left + 'px',
        top: this.annotationRect.top + 'px',
        width: this.annotationRect.width + 'px',
        height: this.annotationRect.height + 'px',
      }
    },
    imageHeight () {
      return this.page.height / this.page.width * this.page.zoomedWidth
    },
    imageDimensions () {
      return {
        width: this.page.zoomedWidth,
        height: this.imageHeight
      }
    },
    imageOverlayStyle () {
      return {
        width: this.imageDimensions.width + 'px',
        height: (this.imageDimensions.height - 1) + 'px',
      }
    },
    imageInfo () {
      return {
        ratioX: this.page.width / this.imageDimensions.width,
        ratioY: this.page.height / this.imageDimensions.height,
      }
    },
    zoomedWidth () {
      return this.page.zoomedWidth
    }
  },
  watch: {
    pdfDocument: function (pdfDocument) {
      if (this.textLoaded) { return }
      this.loadText(pdfDocument)
    },
    zoomedWidth: function () {
      console.log('width changed')
      if (this.pdfPage && this.pdfTextContent) {
        this.renderText(this.pdfPage, this.pdfTextContent, this.pdfAnnotations)
      }
    }
  },
  mounted () {
    console.log('mounting', this.page.number)
    if (this.pdfDocument) {
      this.$nextTick(function () {
        this.loadText(this.pdfDocument)
      })
    }
  },
  beforeDestroy () {
    if (this.page.image_url && !this.imageLoaded && this.$refs.image) {
      // Cancel image download on destroy
      this.$refs.image.setAttribute('src', "")
    }
  },
  destroyed () {
    this.destroyed = true
  },
  methods: {
    onImageLoad () {
      this.imageLoaded = true
    },
    mouseDown (e) {
      if (!this.annotationForm) { return }
      this.annotationRect = null
      this.annotationRect = this.makeRect(e)
      this.annotating = true
    },
    makeRect (e) {
      if (this.annotationRect === null) {
        return {
          left: e.offsetX,
          top: e.offsetY,
          width: 1,
          height: 1
        }
      }
      let left = e.offsetX
      let top = e.offsetY
      let width, height
      if (left < this.annotationRect.left) {
        width = this.annotationRect.left - left
      } else {
        width = left - this.annotationRect.left
        left = this.annotationRect.left
      }
      if (top < this.annotationRect.top) {
        height = this.annotationRect.top - top
      } else {
        height = top - this.annotationRect.top
        top = this.annotationRect.top
      }
      return {
        left,
        top,
        width,
        height,
      }
    },
    mouseMove (e) {
      if (!this.annotationForm) { return }
      if (!this.annotating) { return }
      this.annotationRect = this.makeRect(e)
    },
    mouseUp (e) {
      if (!this.annotationForm) { return }
      if (!this.annotating) { return }
      this.annotating = false
      this.annotationRect = this.makeRect(e)
      if (this.annotationRect.width < 5 || this.annotationRect.height < 5) {
        this.annotationRect = null
        this.$emit('activateannotationform',  {
          left: null, top: null, width: null, height: null
        })
      } else {
        this.$emit('activateannotationform', {
          left: Math.round(this.annotationRect.left * this.imageInfo.ratioX),
          top: Math.round(this.annotationRect.top * this.imageInfo.ratioY),
          width: Math.round(this.annotationRect.width * this.imageInfo.ratioX),
          height: Math.round(this.annotationRect.height * this.imageInfo.ratioY),
        })
      }
    },
    annotationRectClicked (annotationId) {
      this.$emit('currentannotation', annotationId)
      if (annotationId) {
        let el = document.querySelector('#sidebar-annotation-' + annotationId)
        if (el) {
          el.scrollIntoView({
            behavior: 'smooth'
          })
        }
      }
    },
    loadText (pdfDocument) {
      this.textLoaded = true
      pdfDocument.getPage(this.page.number).then((pdfPage) => {
        if (this.destroyed) { return }
        this.pdfPage = pdfPage
        Promise.all([
          pdfPage.getTextContent(),
          pdfPage.getAnnotations({ intent: 'display' })
        ]).then(([content, annotations]) => {
          if (this.destroyed) { return }
          this.pdfAnnotations = annotations
          this.pdfTextContent = content
          this.renderText(this.pdfPage, this.pdfTextContent, this.pdfAnnotations)
        })
      }).catch((err) => {
        console.error(err)
      })
    },
    renderText (pdfPage, pdfTextContent, pdfAnnotations) {
      if (this.destroyed) { return }
      let viewport = pdfPage.getViewport({
        scale: this.page.zoomedWidth / pdfPage.view[2]
      })
      // Rendering text layer as HTML.
      this.$refs.textLayer.innerHTML = ""
      console.log('Rendering content', pdfTextContent)
      const readableStream = pdfPage.streamTextContent({
        normalizeWhitespace: true,
        includeMarkedContent: true
      });
      this.$root.PDFJS.renderTextLayer({
        textContent: pdfTextContent,
        textContentStream: readableStream,
        container: this.$refs.textLayer,
        viewport,
        enhanceTextSelection: true
      })
      
      if (pdfAnnotations.length === 0) {
        return
      }
      const linkService = new FilingcabinetLinkService({
        externalLinkTarget: 2,
        externalLinkRel: "noopener nofollow noreferrer",
        externalLinkEnabled: true,
      })
      linkService.setDocument(this.pdfDocument)
      // Set shim viewer to navigate
      linkService.setViewer({
        scrollPageIntoView: (options) => {
          this.$emit('navigate', {
            number: options.pageNumber,
            source: 'link'
          })
        }
      })
      const parameters = {
        viewport: viewport.clone({ dontFlip: true }),
        div: this.$refs.annotationLayer,
        annotations: pdfAnnotations,
        page: this.pdfPage,
        // imageResourcesPath: this.imageResourcesPath,
        renderInteractiveForms: false,
        linkService: linkService,
        // downloadManager: this.downloadManager,
      };
      if (this.$refs.annotationLayer.querySelector('section')) {
        this.$root.PDFJS.AnnotationLayer.update(parameters)
      } else {
        this.$root.PDFJS.AnnotationLayer.render(parameters);
      }
    }
  }
}
</script>

<style lang="scss" scoped>
.page-wrapper {
  text-align: center;
  margin: 0 auto;
}
.page {
  position: relative;
  overflow: auto;
  left: 50%;
  transform: translateX(-50%)
}
.page-image-placeholder {
  filter: blur(5px);
}
.page-image {
  border: 1px solid #aaa;
  pointer-events: none;
}
.annotation-form {
  border: 1px solid #D52E83;
}
.page-text {
  position: absolute;
  top: 1px;
  width: 100%;
  pre {
    white-space: pre-wrap;
    text-align: left;
    margin: 0 auto;
    overflow: auto;
    padding: 15px;
    font-family: sans-serif;
    background-color: rgba(255, 255, 255, 0.95);
    color: #333;
    font-family: 'Courier New', Courier, monospace;
  }
}
.page-number {
  text-align: center;
}
.annotation-overlay-container, .annotation-rect-container {
  height: 100%;
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  margin: 0 auto;
}
.annotation-rect-container {
  cursor: crosshair;
}
.annotation-sidebar {
  padding-left: 0 !important;
}
.annotation {
  position: absolute;
}
.annotation-rect {
  position: absolute;
  border: 3px solid #FCED00;
  pointer-events: none;
}
</style>
<style lang="css">
/*
  Needs to be non scoped because it's dynamically inserted
  and uses the > selector
 */
.pdf-layer {
  position: absolute;
  left: 0;
  top: 0;
  right: 0;
  bottom: 0;
  height: 100%;
  margin: 0 auto;
}

.text-layer {
  position: absolute;
  left: 0;
  top: 0;
  right: 0;
  bottom: 0;
  overflow: hidden;
  text-align: initial;
  opacity: 0.2;
  line-height: 1.0;
  /* left: 50%;
  transform: translateX(-50%) */
  height: 100%;
  margin: 0 auto;
}
.text-layer > div, .text-layer > span, .textLayer > br {
  color: transparent;
  position: absolute;
  white-space: pre;
  cursor: text;
  transform-origin: 0% 0%;
}

.annotation-layer section {
  position: absolute;
}
.annotation-layer .linkAnnotation > a {
  position: absolute;
  font-size: 1em;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
}
</style>
