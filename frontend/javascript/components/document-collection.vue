<template>
  <div>
    <div class="collection-toolbar">
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
          <button v-if="!showSearch" type="button"
            class="ml-2 btn btn-sm btn-secondary"
            @click="enableSearch"
          >
            <i class="fa fa-search"></i>
          </button>
          <button v-else type="button"
            class="ml-2 btn btn-sm btn-secondary"
            @click="clearSearch"
          >
          <i class="fa fa-close"></i>
        </button>
        </div>
      </div>
      <document-collection-searchbar
        v-if="showSearch && !document"
        :searcher="searcher"
        @search="search"
      />
    </div>
    <div v-if="document" class="collection-document">
      <div class="row">
        <div class="col-12 px-0">
          <document
            :document-url="document.resource_uri"
            :document-preview="document"
            :page="documentPage"
            :config="config"
            :defaults="docDefaults"
          ></document>
        </div>
      </div>
    </div>
    <div v-if="!document && searcher">
      <document-collection-search-results
        v-for="result in searcher.results"
        :key="result.document.id"
        :document="result.document"
        :pages="result.pages"
        @navigate="navigate"
      />
    </div>
    <div v-show="!document && !searcher" class="document-collection">
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
import DocumentCollectionSearchbar from './document-collection-searchbar.vue'
import DocumentCollectionSearchResults from './document-collection-searchresults.vue'
import Document from './document.vue'

import {getData} from '../lib/utils.js'

function getIDFromURL (s) {
  const parts = s.split('/')
  return parseInt(parts[parts.length - 2], 10)
}

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
    Document,
    DocumentCollectionSearchbar,
    DocumentCollectionSearchResults,
  },
  data () {
    return {
      document: null,
      collection: this.documentCollectionPreview || {
        documents: []
      },
      showSearch: false,
      searcher: null,
      documentPage: 1,
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
    collectionIndex () {
      const documents = this.collection.documents
      const collectionIndex = {}
      documents.forEach((d, i) => {
        collectionIndex[d.id] = i
      })
      return collectionIndex
    },
    docDefaults () {
      return {
        maxHeight: '90vh'
      }
    }
  },
  methods: {
    navigate ({document, page}) {
      this.document = document
      this.documentPage = page || 1
    },
    enableSearch () {
      this.showSearch = true
      this.document = null
    },
    clearSearch () {
      this.searcher = null
      this.showSearch = false
    },
    search (term) {
      this.document = null
      console.log('searching for term', term)
      this.searcher = {
        term: term,
        done: false,
        results: []
      }
      let searchUrl = `${this.config.urls.pageApiUrl}?collection=${this.collection.id}&q=${encodeURIComponent(term)}`
      getData(searchUrl).then((response) => {
        this.searcher.response = response
        this.searcher.done = true
        const docsWithPages = []
        let docs = {}
        let docCount = 0
        response.objects.forEach((p, i) => {
          const docId = getIDFromURL(p.document)
          let document = this.collection.documents[this.collectionIndex[docId]]
          let docResult = {
            image: p.image,
            number: p.number,
            query_highlight: p.query_highlight
          }
          if (docs[p.document] === undefined) {
            docs[p.document] = docCount
            docCount += 1
            docsWithPages.push({
              document: document,
              pages: [docResult]
            })
          } else {
            docsWithPages[docs[p.document]].pages.push(docResult)
          }

        })
        this.searcher.results = docsWithPages
        Vue.set(this.searcher, 'docCount', docCount)
      })
    },
  }
}
</script>

<style lang="scss">

</style>
