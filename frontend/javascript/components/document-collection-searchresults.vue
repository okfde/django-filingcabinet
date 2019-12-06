<template>
  <div class="document-preview-grid">
    <div class="row bg-secondary pt-3">
      <div class="col-12">
        <h4 class="text-white">{{ document.title }}</h4>
      </div>
    </div>
    <div class="row bg-secondary">
      <div v-for="page in pages" class="col-sm-4 col-md-3" :key="page.number">
        <document-preview
          :document="document"
          :page="page.number"
          :highlight="page.query_highlight"
          :image="page.image"
          @navigate="navigate"
        />
      </div>
    </div>
  </div>
</template>

<script>

import 'intersection-observer'

import DocumentPreview from './document-preview.vue'

export default {
  name: 'document-collection-searchresult',
  props: ['document', 'pages'],
  components: {
    DocumentPreview,
  },
  computed: {
    i18n () {
      return this.config.i18n
    },
  },
  methods: {
    navigate (docAndPage) {
      this.$emit('navigate', docAndPage)
    }
  }
}
</script>

<style lang="scss">

</style>
