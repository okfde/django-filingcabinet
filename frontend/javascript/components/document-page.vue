<template>
  <div :id="pageId" class="page">
    <img v-if="page.image_url" v-show="imageLoaded" ref="image" @load="onImageLoad" :src="imageUrl" alt="" class="img-fluid page-image"/>
    <div v-if="!imageLoaded" class="spinner-grow" role="status">
      <span class="sr-only">Loading...</span>
    </div>
    <p>
      {{ page.number }}
    </p>
  </div>
</template>

<script>

export default {
  name: 'document-page',
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
      return this.page.image_url.replace(/\{size\}/, 'normal')
    },
    pageId () {
      return `page-${this.page.number}`
    }
  },
  methods: {
    onImageLoad () {
      this.imageLoaded = true
    }
  }
}
</script>

<style lang="scss">
.page {
  text-align: center;
}
.page-image {
  border: 1px solid #aaa;
  margin-bottom: 0.25rem;
}
</style>
