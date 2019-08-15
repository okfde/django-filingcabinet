<template>
  <a :href="pageAnchor" class="preview-page" @click.prevent="navigate">
    <img v-if="page.image_url" v-show="imageLoaded" ref="image" @load="onImageLoad" :src="imageUrl" alt="" class="img-fluid page-image"/>
    <div v-if="!imageLoaded" class="spinner-grow" role="status">
      <span class="sr-only">Loading...</span>
    </div>
    <p>
      {{ page.number }}
    </p>
  </a>
</template>

<script>

export default {
  name: 'document-preview-page',
  props: ['page'],
  data () {
    return {
      imageLoaded: false
    }
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
      return this.page.image_url.replace(/\{size\}/, 'small')
    },
    pageAnchor () {
      return `#page-${this.page.number}`
    }
  },
  methods: {
    onImageLoad () {
      this.imageLoaded = true
    },
    navigate () {
      this.$emit('navigate', this.page.number)
    }
  }
}
</script>

<style lang="scss" scoped>
.preview-page {
  display: block;
  text-align: center;
}
.preview-page .page-image {
  border: 1px solid #aaa;
  margin: 0 auto;
}
.preview-page p, .preview-page p:hover {
  text-align: center;
  color: #fff;
  text-decoration: none;
}
</style>
