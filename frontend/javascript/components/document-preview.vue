<template>
  <a :href="document.site_url" class="preview-doc" target="_blank">
    <img v-if="imageUrl" v-show="imageLoaded" ref="image" @load="onImageLoad" :src="imageUrl" alt="" class="img-fluid page-image"/>
    <div v-if="!imageLoaded" class="spinner-grow" role="status">
      <span class="sr-only">Loading...</span>
    </div>
    <p>
      {{ document.title }}
    </p>
  </a>
</template>

<script>

export default {
  name: 'document-preview',
  props: ['document'],
  data () {
    return {
      imageLoaded: false
    }
  },
  beforeDestroy () {
    if (this.document.cover_image && !this.imageLoaded) {
      // Cancel image download on destroy
      this.$refs.image.setAttribute('src', "")
    }
  },
  computed: {
    i18n () {
      return this.config.i18n
    },
    imageUrl () {
      return this.document.cover_image
    },
  },
  methods: {
    onImageLoad () {
      this.imageLoaded = true
    }
  }
}
</script>

<style lang="scss" scoped>
.preview-doc {
  display: block;
  text-align: center;
}
.preview-doc .page-image {
  border: 1px solid #aaa;
  margin: 0 auto;
}
.preview-doc p, .preview-doc p:hover {
  text-align: center;
  color: #fff;
  text-decoration: none;
}
</style>
