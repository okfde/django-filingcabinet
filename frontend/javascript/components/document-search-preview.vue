<template>
  <a :href="pageAnchor" class="media search-preview-page border-top border-light text-white" @click.prevent="navigate">
    <img :src="imageUrl" alt="" class="w-25 d-flex img-fluid">
    <div class="media-body ml-2">
      <h6>Page {{ page.number }} - {{ matches.count }} matches</h6>
    </div>
  </a>
</template>

<script>

export default {
  name: 'document-search-preview',
  props: ['page', 'matches'],
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
    navigate () {
      this.$emit('navigate', this.page.number)
    }
  }
}
</script>

<style lang="scss" scoped>
.search-preview-page {
  cursor: pointer;
  text-decoration: none;
  height: 90px;
  padding: 8px 0;
  margin-bottom: 9px;
}
</style>
