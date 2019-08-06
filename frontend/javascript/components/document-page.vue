<template>
  <div class="page">
    <img :src="imageUrl" alt="" class="img-fluid page-image"/>
  </div>
</template>

<script>

export default {
  name: 'document-page',
  props: ['page'],
  components: {

  },
  created () {
  },
  computed: {
    i18n () {
      return this.config.i18n
    },
    imageUrl () {
      return this.page.image_url.replace(/\{size\}/, 'normal')
    }
  }
}
</script>

<style lang="scss">
.page {
  border: 1px solid black;
  height: 100px;
  padding: 0 12px;
  display: flex;
  align-items: center;

}
.page-image {
  height: 100px;
}
</style>
