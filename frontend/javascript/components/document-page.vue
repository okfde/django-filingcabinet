<template>
  <div>
    <div :id="pageId" class="page">
      <img v-if="page.image_url" v-show="imageLoaded" ref="image" @load="onImageLoad" :src="imageUrl" alt="" class="img-fluid page-image"/>
      <div class="page-text" v-if="showText">
        <pre :style="textContainerStyle">
          {{ page.content }}
        </pre>
      </div>
      <div v-if="!imageLoaded" class="spinner-grow" role="status">
        <span class="sr-only">Loading...</span>
      </div>
      <template v-if="showAnnotations && imageLoaded">
        <page-annotation-overlay v-for="annotation in annotations"
          :key="annotation.id"
          :page="page"
          :annotation="annotation"
          :current-annotation="currentAnnotation"
          @currentannotation="$emit('currentannotation', $event)"
        >
        </page-annotation-overlay>
      </template>
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
  props: ['page', 'annotations', 'showText', 'showAnnotations', 'currentAnnotation'],
  components: {
    PageAnnotationOverlay
  },
  data () {
    return {
      imageLoaded: false,
      ratio: null,
    }
  },
  mounted () {
    this.updateRatio()
  },
  beforeDestroy () {
    if (this.page.image_url && !this.imageLoaded) {
      // Cancel image download on destroy
      this.$refs.image.setAttribute('src', "")
    }
  },
  computed: {
    i18n () {
      return this.config.i18n
    },
    imageUrl () {
      return this.page.image_url.replace(/\{size\}/, 'normal')
    },
    pageId () {
      return `page-${this.page.number}`
    },
    textContainerStyle () {
      if (!this.imageLoaded) {
        return {}
      }
      return {
        width: this.$refs.image.width + 'px',
        height: this.$refs.image.height + 'px',
      }
    }
  },
  methods: {
    onImageLoad () {
      this.imageLoaded = true
      this.updateRatio()
    },
    updateRatio () {
      if (!this.$refs.image) {
        return
      }
      this.ratio = this.$refs.image.width / this.page.width
    }
  },
}
</script>

<style lang="scss" scoped>
.page {
  text-align: center;
  position: relative;
}
.page-image {
  border: 1px solid #aaa;
  margin-bottom: 0.25rem;
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
.annotation {
  position: absolute;

}
</style>
