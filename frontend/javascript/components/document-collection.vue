<template>
  <div>
    <div class="toolbar">
      <div class="row py-2 bg-dark">
        <div class="col-4">
          <div v-if="document" class="btn-group" role="group">
            <button type="button"
              class="btn btn-sm btn-secondary"
              @click="document = null"
            >
              {{ i18n.backToCollection }}
            </button>
          </div>
        </div>
        <div class="col-4 mr-auto ml-auto text-center">
          <h4 class="text-white text-truncate mb-0">
            <template v-if="document">
              {{ document.title }}
            </template>
            <template v-else>
              {{ collection.title }}
            </template>
          </h4>
        </div>
        <div class="col-4 text-right">
          <span class="text-muted">
            <template v-if="document">
              {{ collection.title }}
            </template>
            <template v-else>
              {{ collection.documents.length }} {{ i18n.documents }}
            </template>
          </span>
        </div>
      </div>
    </div>
    <div v-if="document" class="document">
      <document
        :document-url="document.resource_uri"
        :document-preview="document"
        :config="config"
      ></document>
    </div>
    <div v-show="!document" class="document-collection">
      <document-preview-grid
        :documents="collection.documents"
        @navigate="navigate"
      ></document-preview-grid>
    </div>
  </div>
</template>

<script>
import Vue from 'vue'

import DocumentPreviewGrid from './document-preview-grid.vue'
import Document from './document.vue'

import {getData} from '../lib/utils.js'

export default {
  name: 'document-collection',
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
    Document
  },
  data () {
    return {
      document: null,
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
    navigate (doc) {
      this.document = doc
    }
  }
}
</script>

<style lang="scss">

</style>
