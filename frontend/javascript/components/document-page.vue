<template>
  <div class="page" :style="">
    <img v-show="imageLoaded" ref="image" @load="onImageLoad" :src="imageUrl" alt="" class="img-fluid page-image"/>
    <div v-if="!imageLoaded" class="spinner-grow" role="status">
      <span class="sr-only">Loading...</span>
    </div>
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
    if (!this.imageLoaded) {
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
  border: 1px solid black;
  text-align: center;
}
</style>
