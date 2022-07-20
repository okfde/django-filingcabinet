<template>
  <div class="document-preview-grid">
    <div class="row bg-secondary pt-3">
      <div class="col-12">
        <h4 class="text-white">
          {{ document.title }}
          <small
            v-if="documentPublicationDate"
            class="badge bg-dark"
          >
            {{ documentPublicationDate }}
          </small>
        </h4>
      </div>
    </div>
    <div class="row bg-secondary">
      <div
        v-for="page in pages"
        :key="page.number"
        class="col-sm-4 col-md-3"
      >
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
  name: 'DocumentCollectionSearchresult',
  components: {
    DocumentPreview,
  },
  props: ['document', 'pages'],
  computed: {
    i18n () {
      return this.config.i18n
    },
    documentPublicationDate () {
      if (!this.document.published_at) {
        return null
      }
      return new Intl.DateTimeFormat().format(new Date(this.document.published_at))
    }
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
