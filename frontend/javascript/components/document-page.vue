<template>
  <div class="page-wrapper" ref="pageWrapper">
    <div :id="pageId" class="page" :style="pageStyle">
      <img v-if="page.image_url" v-show="imageLoaded" ref="image"
        @load="onImageLoad"
        :src="imageUrl"
        :alt="pageLabel"
        :style="{'width': page.zoomedWidth + 'px'}"
        class="page-image"
        draggable="false"
        :class="{'annotation-form': showAnnotationForm}"
        />
      <div class="page-text" v-if="showText && !showAnnotationForm">
        <pre :style="imageOverlayStyle">
          {{ page.content }}
        </pre>
      </div>
      <div v-if="!imageLoaded" class="spinner-grow" role="status">
        <span class="sr-only">{{ i18n.loading }}</span>
      </div>
      <div v-if="showAnnotationForm"
        class="annotation-rect-container" :style="imageOverlayStyle"
        @mousedown="mouseDown"
        @mousemove="mouseMove"
        @mouseup="mouseUp"
        >
        <div v-if="annotationRect" :style="annotationRectStyle" class="annotation-rect"></div>
      </div>
      <div v-if="showAnnotations && imageLoaded && !showAnnotationForm && annotationsWithRect.length"
        class="annotation-overlay-container" :style="imageOverlayStyle">
        <page-annotation-overlay v-for="annotation in annotationsWithRect"
          :key="annotation.id"
          :page="page"
          :annotation="annotation"
          :current-annotation="currentAnnotation"
          @currentannotation="$emit('currentannotation', $event)"
        >
        </page-annotation-overlay>
      </div>
    </div>
    <p class="page-number">
      {{ page.number }}
    </p>
  </div>
</template>

<script>

import PageAnnotationOverlay from './document-page-annotationoverlay.vue'

export default {
  name: 'document-page',
  props: [
    'page', 'annotations', 'showText', 'showAnnotations',
    'currentAnnotation', 'annotationForm', 'width'
  ],
  components: {
    PageAnnotationOverlay
  },
  data () {
    return {
      imageLoaded: false,
      annotationRect: null,
      annotating: false,
    }
  },
  beforeDestroy () {
    if (this.page.image_url && !this.imageLoaded && this.$refs.image) {
      // Cancel image download on destroy
      this.$refs.image.setAttribute('src', "")
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
    imageUrl () {
      return this.page.image_url.replace(/\{size\}/, this.imageSize)
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
    imageDimensions () {
      return {
        width: this.page.zoomedWidth,
        height: Math.round(this.page.zoomedWidth / this.page.width * this.page.height)
      }
    },
    imageOverlayStyle () {
      return {
        width: this.imageDimensions.width + 'px',
        height: this.imageDimensions.height + 'px',
      }
    },
    imageInfo () {
      return {
        ratioX: this.page.width / this.imageDimensions.width,
        ratioY: this.page.height / this.imageDimensions.height,
      }
    },
    pageStyle () {
      return {
        width: this.width + 'px'
      }
    }
  },
  methods: {
    onImageLoad () {
      this.imageLoaded = true
      const image = this.$refs.image
    },
    mouseDown (e) {
      if (!this.annotationForm) { return }
      const image = this.$refs.image
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
    }
  },
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
.page-image {
  border: 1px solid #aaa;
  margin-bottom: 0.25rem;
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
    white-space: normal;
    text-align: left;
    margin: 0 auto;
    overflow: auto;
    background-color: rgba(255, 255, 255, 0.9);
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
}
.annotation-rect-container {
  cursor: crosshair;
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
