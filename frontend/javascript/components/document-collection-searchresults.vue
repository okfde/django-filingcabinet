<template>
  <div class="document-preview-grid">
    <div class="row bg-secondary pt-3">
      <div class="col-12">
        <h4 class="text-white">
          {{ document.title }}
          <small v-if="documentPublicationDate" class="badge text-bg-dark">
            {{ documentPublicationDate }}
          </small>
        </h4>
      </div>
    </div>
    <div class="row bg-secondary">
      <div v-for="page in pages" :key="page.number" class="col-sm-4 col-md-3">
        <DocumentPreview
          :document="document"
          :page="page.number"
          :highlight="page.query_highlight"
          :image="page.image"
          @navigate="navigate" />
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
    DocumentPreview
  },
  props: {
    document: {
      type: Object,
      required: true
    },
    pages: {
      type: Array,
      required: true
    }
  },
  emits: ['navigate'],
  computed: {
    i18n() {
      return this.config.i18n
    },
    dtf() {
      return new Intl.DateTimeFormat(document.documentElement.lang, {
        year: 'numeric',
        month: 'numeric',
        day: 'numeric'
      })
    },
    documentPublicationDate() {
      if (!this.document.published_at) {
        return null
      }
      return this.dtf.format(new Date(this.document.published_at))
    }
  },
  methods: {
    navigate(docAndPage) {
      this.$emit('navigate', docAndPage)
    }
  }
}
</script>

<style lang="scss"></style>
