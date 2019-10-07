<template>
  <div class="document-collection">
    <document-preview-grid
      :documents="collection.documents"
    ></document-preview-grid>
  </div>
</template>

<script>
import Vue from 'vue'

import DocumentPreviewGrid from './document-preview-grid.vue'

import {getData} from '../lib/utils.js'

export default {
  name: 'document',
  props: {
    documentCollectionUrl: {
      type: String
    },
    documentCollectionPreview: {
      type: Object
    },
    config: {
      type: Object,
      default: () => ({})
    }
  },
  components: {
    DocumentPreviewGrid,
  },
  data () {
    return {
      collection: this.documentCollectionPreview || {
        documents: []
      },
    }
  },
  created () {
    getData(this.documentCollectionUrl).then((docCollection) => {
      this.collection = docCollection
    })
  },
  mounted () {
  },
  computed: {
    i18n () {
      return this.config.i18n
    },
  },
  methods: {

  }
}
</script>

<style lang="scss">

</style>
