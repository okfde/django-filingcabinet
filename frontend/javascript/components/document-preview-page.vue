<template>
  <a :href="pageAnchor" class="document-preview-page" @click.prevent="navigate">
    <picture>
      <source
        v-for="format in imageFormats"
        :key="format"
        :srcset="imageUrl.replace(/\.png/, '.png.' + format)"
        :type="'image/' + format" />
      <img
        v-if="page.image_url"
        v-show="imageLoaded"
        ref="image"
        :src="imageUrl"
        alt=""
        class="img-fluid page-image"
        @load="onImageLoad" />
    </picture>
    <div v-if="!imageLoaded" class="spinner-grow" role="status">
      <span class="visually-hidden">{{ i18n.loading }}</span>
    </div>
    <p>
      {{ page.number }}
    </p>
  </a>
</template>

<script>
export default {
  name: 'DocumentPreviewPage',
  props: {
    page: {
      type: Object,
      required: true
    },
    imageFormats: {
      type: Array,
      default: () => []
    }
  },
  data() {
    return {
      imageLoaded: false
    }
  },
  computed: {
    i18n() {
      return this.$root.config.i18n
    },
    imageUrl() {
      return this.page.image_url.replace(/\{size\}/, 'small')
    },
    pageAnchor() {
      return `#page-${this.page.number}`
    },
    imageSources() {
      return this.supportedFormats.map((format) => {
        let srcset = this.imageSrcSet
        srcset = srcset.replace(/\.png/g, `.png.${format}`)
        return {
          srcset,
          type: `image/${format}`
        }
      })
    }
  },
  beforeDestroy() {
    if (this.page.image_url && !this.imageLoaded && this.$refs.image) {
      // Cancel image download on destroy
      this.$refs.image.setAttribute('src', '')
    }
  },
  methods: {
    onImageLoad() {
      this.imageLoaded = true
    },
    navigate() {
      this.$emit('navigate', this.page.number)
    }
  }
}
</script>

<style lang="scss">
.document-preview-page {
  display: block;
  text-align: center;
  padding: 0 0.5rem;
}
.document-preview-page .page-image {
  border: 1px solid #aaa;
  margin: 0 auto;
}
.document-preview-page p,
.document-preview-page p:hover {
  text-align: center;
  color: #fff;
  text-decoration: none;
}
</style>
