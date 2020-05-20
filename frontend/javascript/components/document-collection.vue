<template>
  <div>
    <div
      ref="toolbar"
      class="collection-toolbar"
    >
      <div class="row py-2 bg-dark">
        <div class="col-4">
          <div
            v-if="document"
            class="btn-group"
            role="group"
          >
            <button
              type="button"
              class="btn btn-sm btn-secondary"
              @click="clearDocument"
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
          <button
            v-if="!showSearch"
            type="button"
            class="ml-2 btn btn-sm btn-secondary"
            @click="enableSearch"
          >
            <i class="fa fa-search" />
          </button>
          <button
            v-else
            type="button"
            class="ml-2 btn btn-sm btn-secondary"
            @click="clearSearch"
          >
            <i class="fa fa-close" />
          </button>
        </div>
      </div>
      <document-collection-searchbar
        v-if="showSearch && !document"
        :searcher="searcher"
        @search="search"
      />
    </div>
    <div
      v-if="document"
      class="collection-document"
    >
      <div class="row">
        <div class="col-12 px-0">
          <document
            :document-url="document.resource_uri"
            :document-preview="document"
            :page="documentPage"
            :config="config"
            :defaults="docDefaults"
          />
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
    <div
      v-show="!document && !searcher"
      class="document-collection"
    >
      <div class="list-group list-group-flush">
        <button
          v-if="currentDirectory != null"
          type="button"
          class="list-group-item list-group-item-action list-group-item-dark text-center"
          @click="selectDirectory()"
        >
          <i class="fa fa-arrow-left float-left" />
          {{ currentDirectory.name }}
        </button>
        <button
          v-for="directory in directories"
          :key="directory.id"
          type="button"
          class="list-group-item list-group-item-action list-group-item-secondary"
          @click="selectDirectory(directory)"
        >
          {{ directory.name }}
        </button>
      </div>
      <document-preview-grid
        :documents="documents"
        @navigate="navigate"
      />
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
  name: 'DocumentCollection',
  components: {
    DocumentPreviewGrid,
    Document,
    DocumentCollectionSearchbar,
    DocumentCollectionSearchResults,
  },
  props: {
    documentCollectionUrl: {
      type: String,
      required: true
    },
    documentCollectionPreview: {
      type: Object,
      default: () => ({
        documents: [], directories: []
      })
    },
    config: {
      type: Object,
      default: () => ({})
    }
  },
  data () {
    return {
      document: null,
      collection: this.documentCollectionPreview || {
        documents: [], directories: []
      },
      showSearch: false,
      searcher: null,
      documentPage: 1,
      currentDirectory: null,
      directoryStack: [],
      documents: [],
      directories: []
    }
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
  created () {
    this.getCollectionData()
  },
  mounted () {
  },
  methods: {
    getCollectionData () {
      const url = `${this.documentCollectionUrl}?directory=${this.currentDirectory ? this.currentDirectory.id : ''}`
      getData(url).then((docCollection) => {
        this.collection = docCollection
        this.documents = docCollection.documents
        this.directories = docCollection.directories
      })
    },
    navigate ({document, page}) {
      this.document = document
      this.documentPage = page || 1
      window.scrollTo(0, this.$refs.toolbar.offsetTop)
    },
    clearDocument () {
      this.document = null
      window.scrollTo(0, this.$refs.toolbar.offsetTop)
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
        response.objects.forEach((p) => {
          const docId = getIDFromURL(p.document)
          let document = this.collection.documents[this.collectionIndex[docId]]
          let docResult = {
            image: p.image.replace(/\{size\}/, 'small'),
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
    selectDirectory (directory) {
      if (directory) {
        this.directoryStack.push(directory)
      } else {
        this.directoryStack.pop()
      }
      this.currentDirectory = this.directoryStack[this.directoryStack.length - 1] || null
      this.getCollectionData()
    }
  }
}
</script>

<style lang="scss">

</style>
