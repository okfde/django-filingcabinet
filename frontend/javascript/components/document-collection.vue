<template>
  <div>
    <div ref="toolbar" class="collection-toolbar">
      <div class="row py-2 bg-dark">
        <div class="col-4 col-md-3 d-flex gap-2" role="group">
          <template v-if="document">
            <button
              type="button"
              class="btn btn-sm btn-secondary"
              @click="clearDocument"
            >
              {{ i18n.backToCollection }}
            </button>
          </template>

          <template v-else>
            <button
              v-if="currentDirectory"
              type="button"
              class="btn btn-sm btn-secondary"
              :title="i18n.upOneDir"
              data-bs-toggle="tooltip"
              @click="selectDirectory(parentDirectory)"
            >
              <i class="fa fa-toggle-up" />
              <span class="visually-hidden">{{ i18n.upOneDir }}</span>
            </button>

            <a
              v-if="zipDownload"
              :href="zipDownload"
              class="btn btn-sm btn-secondary"
              :title="i18n.downloadZIP"
              data-bs-toggle="tooltip"
            >
              <i class="fa fa-download" />
              <span class="visually-hidden">{{ i18n.downloadZIP }}</span>
            </a>

            <CopyButton
              v-if="config.deepUrls"
              :title="i18n.copyCollectionLink"
              :copy-text="queryUrl.toString()"
            >
              <i class="fa fa-link" />
              <span class="visually-hidden">{{ i18n.copyCollectionLink }}</span>
            </CopyButton>
          </template>
        </div>

        <div class="col-auto order-md-3 ms-auto">
          <span class="text-white d-inline-block text-truncate">
            <template v-if="document">
              {{ collection.title }}
            </template>
            <template v-else>
              {{ documentCount }} {{ i18n.documents }}
            </template>
          </span>
        </div>
        <div class="col-10 col-md order-md-2 text-center">
          <h4 class="text-white text-truncate mb-0">
            <template v-if="document">
              {{ document.title }}
            </template>
            <template v-else>
              {{ collection.title }}
            </template>
          </h4>
        </div>

        <div
          v-if="!document && allowToggleSearch"
          class="col-auto order-md-4 ms-auto"
        >
          <button
            v-if="!showSearch"
            type="button"
            class="ms-2 btn btn-sm btn-secondary"
            @click="enableSearch"
          >
            <i class="fa fa-search" />
            <span class="visually-hidden">{{ i18n.search }}</span>
          </button>
          <button
            v-else
            type="button"
            class="ms-2 btn btn-sm btn-secondary"
            @click="clearSearch"
          >
            <i class="fa fa-close" />
            <span class="visually-hidden">{{ i18n.clear }}</span>
          </button>
        </div>
      </div>
      <DocumentCollectionSearchbar
        v-if="showSearch && !document"
        :searcher="searcher"
        :directory="currentDirectory"
        :show-search-feed="showSearchFeed"
        :filters="settings.filters"
        @clearsearch="clearSearch"
        @search="search"
      />
    </div>
    <div v-if="document" class="collection-document">
      <div class="row">
        <div class="col-12 px-0">
          <DocumentViewer
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
      <template v-if="searcher.term">
        <DocumentCollectionSearchResults
          v-for="result in searcher.results"
          :key="result.document.id"
          :document="result.document"
          :pages="result.pages"
          @navigate="navigate"
        />
      </template>
      <template v-else>
        <div class="row bg-secondary">
          <div class="col px-0">
            <DocumentPreviewGrid
              :documents="searcher.documents"
              @navigate="navigate"
            />
          </div>
        </div>
      </template>
      <div v-if="searcher.done && searcher.response.meta.next">
        <div class="row bg-secondary justify-content-center">
          <div class="col-auto px-0 pb-5">
            <button
              class="btn btn-secondary my-3"
              @click="loadMoreSearchResults"
            >
              {{ i18n.loadMore }}
            </button>
          </div>
        </div>
      </div>
    </div>
    <div v-show="!document && !searcher" class="document-collection">
      <div class="row text-bg-secondary">
        <div class="col px-0">
          <nav
            class="px-3 my-2 text-white d-flex gap-2"
            v-if="currentDirectory"
          >
            <ol class="breadcrumb">
              <li class="breadcrumb-item">
                <a
                  href="#!"
                  @click.prevent="selectDirectory()"
                  :title="i18n.toRoot"
                  data-bs-toggle="tooltip"
                >
                  <i class="fa fa-folder" />
                  <span class="visually-hidden">{{ i18n.toRoot }}</span>
                </a>
              </li>
              <li
                v-for="(directory, i) in directoryStack"
                :key="directory.id"
                class="breadcrumb-item"
                :class="{ active: i === directoryStack.length - 1 }"
              >
                <a href="#!" @click.prevent="selectDirectory(directory)">
                  {{ directory.name }}
                </a>
              </li>
            </ol>
          </nav>

          <div
            class="d-flex px-3 dir-description"
            v-if="currentDirectory?.description"
          >
            <i class="fa fa-info-circle mt-1 me-2"></i>
            <div v-html="currentDirectory.description" />
          </div>

          <div class="list-group list-group-flush">
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
          <DocumentPreviewGrid
            :documents="documents"
            @navigate="navigate"
            @loadmore="loadMoreDocuments"
          />
          <div
            v-if="shouldPaginate && canPaginate"
            class="col-auto px-0 pb-5 text-center"
          >
            <button
              class="btn btn-secondary my-3"
              @click.prevent="() => loadMoreDocuments()"
            >
              {{ i18n.loadMore }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { Tooltip } from 'bootstrap'
import { nextTick } from 'vue'

import DocumentCollectionSearchbar from './document-collection-searchbar.vue'
import DocumentCollectionSearchResults from './document-collection-searchresults.vue'
import DocumentPreviewGrid from './document-preview-grid.vue'
import DocumentViewer from './document-viewer.vue'

import { getData } from '../lib/utils.js'
import CopyButton from './copy-button.vue'

const DOCUMENTS_API_LIMIT = 50
const MAX_SCROLL_DOCS = DOCUMENTS_API_LIMIT * 100

function getIDFromURL(s) {
  const parts = s.split('/')
  return parseInt(parts[parts.length - 2], 10)
}

export default {
  name: 'DocumentCollection',
  components: {
    DocumentPreviewGrid,
    DocumentViewer,
    DocumentCollectionSearchbar,
    DocumentCollectionSearchResults,
    CopyButton
  },
  props: {
    documentCollection: {
      type: Object,
      default: () => ({
        documents: [],
        directories: []
      })
    },
    config: {
      type: Object,
      default: () => ({})
    }
  },
  data() {
    const documents = []
    const directories = []
    let collection = {
      documents,
      directories
    }
    let directoryStack = []
    let currentDirectory = null
    const document = null
    if (this.documentCollection) {
      collection = this.documentCollection
      directoryStack = collection.directory_stack
      currentDirectory = collection.current_directory
      if (currentDirectory) directoryStack.push(currentDirectory)
    }

    const shouldPaginate = collection.document_directory_count > MAX_SCROLL_DOCS
    const settings = collection.settings || {}
    const preferences = settings.preferences || {}
    return {
      document,
      collection,
      settings,
      showSearch: preferences.showSearch ?? false,
      allowToggleSearch: preferences.allowToggleSearch ?? true,
      showSearchFeed: preferences.showSearchFeed ?? false,
      searcher: null,
      documentPage: 1,
      currentDirectory,
      directoryStack,
      shouldPaginate,
      documents: this.makeDocuments(collection, shouldPaginate),
      directories: collection.directories,
      documentOffsets: this.makeOffsets(collection, shouldPaginate),
      lastOffset: 0,
      documentsUri: collection.documents_uri || null
    }
  },
  computed: {
    i18n() {
      return this.config.i18n
    },
    collectionIndex() {
      const documents = this.documents
      const collectionIndex = {}
      documents.forEach((d, i) => {
        if (d !== null) {
          collectionIndex[d.id] = i
        }
      })
      return collectionIndex
    },
    docDefaults() {
      return {
        maxHeight: '90vh'
      }
    },
    collectionAuth() {
      if (!this.collection.listed && this.collection.uid) {
        return ['uid', this.collection.uid]
      }
      return undefined
    },
    canPaginate() {
      return (
        this.collection.document_directory_count >
        this.lastOffset + DOCUMENTS_API_LIMIT
      )
    },
    documentCount() {
      return new Intl.NumberFormat(document.documentElement.lang, {
        style: 'decimal'
      }).format(this.collection.document_count)
    },
    zipDownload() {
      if (this.collection?.zip_download_url) {
        if (this.currentDirectory) {
          return `${this.collection.zip_download_url}?directory=${this.currentDirectory.id}`
        }

        return this.collection.zip_download_url
      }

      return false
    },
    parentDirectory() {
      return this.directoryStack[this.directoryStack.length - 2]
    },
    queryParams() {
      const params = new URLSearchParams()

      if (this.currentDirectory)
        params.append('directory', this.currentDirectory.id)

      if (this.document) params.append('document', this.document.id)

      return params
    },
    queryUrl() {
      const url = new URL(window.location.href)
      url.search = this.queryParams
      return url
    }
  },
  created() {
    const queryParams = new URLSearchParams(window.location.search)

    if (queryParams.has('document')) {
      this.document = this.collection.documents.find(
        (d) => d.id === parseInt(queryParams.get('document'), 10)
      )

      if (!this.document) {
        getData(
          `${this.config.urls.documentApiUrl}${queryParams.get('document')}/`
        ).then((doc) => {
          this.document = doc
        })
      }
    }

    if (!this.documentCollection.id && this.documentCollection.resource_uri) {
      this.getCollectionData()
    }
  },
  mounted() {
    if (
      this.documents.length >= 0 &&
      this.documents[0] === null &&
      this.documentsUri
    ) {
      this.loadMoreDocuments(0)
    }

    this.updateTooltips()
  },
  methods: {
    getCollectionData() {
      const url = new URL(
        this.documentCollection.resource_uri,
        window.location.origin
      )
      const params = new URLSearchParams(url.search)

      if (this.collectionAuth) params.append(...this.collectionAuth)

      this.documents = []
      this.directories = []
      params.append(
        'directory',
        this.currentDirectory ? this.currentDirectory.id : ''
      )
      url.search = params

      return getData(url).then((docCollection) => {
        this.collection = docCollection
        this.documentsUri = docCollection.documents_uri
        this.documentOffsets = this.makeOffsets(docCollection)
        this.documents = this.makeDocuments(docCollection)
        this.directories = docCollection.directories
        this.directoryStack = this.collection.directory_stack
        if (this.currentDirectory)
          this.directoryStack.push(this.currentDirectory)
        if (!this.settings) {
          this.settings = docCollection.settings
        }
      })
    },
    makeOffsets(collection) {
      const offsetSteps = collection.documents.length / DOCUMENTS_API_LIMIT
      const documentOffsets = new Set()
      for (let i = 0; i < offsetSteps; i += 1) {
        documentOffsets.add(i)
      }
      return documentOffsets
    },
    makeDocuments(collection, shouldPaginate = false) {
      if (this.shouldPaginate || shouldPaginate) {
        return collection.documents
      }
      const colDocs = collection.documents || []
      return [
        ...colDocs,
        ...new Array(collection.document_directory_count - colDocs.length).fill(
          null
        )
      ]
    },
    loadMoreDocuments(offset) {
      if (offset === undefined) {
        offset = this.lastOffset + DOCUMENTS_API_LIMIT
      }
      offset = offset - (offset % DOCUMENTS_API_LIMIT)
      if (this.shouldPaginate) {
        if (offset === this.lastOffset) {
          return
        }
        this.documents = []
        this.lastOffset = offset
        nextTick(() => this.goTop())
        return this.getDocuments(offset)
      }
      const offsetStep = offset / DOCUMENTS_API_LIMIT
      if (!this.documentOffsets.has(offsetStep)) {
        this.documentOffsets.add(offsetStep)
        this.getDocuments(offset)
      }
    },
    getDocuments(offset) {
      if (this.abortController) {
        this.documentOffsets.delete(this.lastOffset)
        this.abortController.abort()
      }
      this.abortController = new AbortController()
      this.lastOffset = offset
      const url = new URL(this.documentsUri, window.location.origin)
      const params = new URLSearchParams(url.search)

      if (this.collectionAuth) params.append(...this.collectionAuth)

      params.append(
        'directory',
        this.currentDirectory ? this.currentDirectory.id : '-'
      )
      params.append('offset', offset)
      params.append('limit', DOCUMENTS_API_LIMIT)
      url.search = params

      this.documentOffset = offset + DOCUMENTS_API_LIMIT
      getData(url, {}, this.abortController.signal).then((result) => {
        if (!result) {
          return
        }
        this.abortController = null
        if (this.shouldPaginate) {
          this.documents = result.objects
        } else {
          this.documents = [
            ...this.documents.slice(0, offset),
            ...result.objects,
            ...this.documents.slice(offset + result.objects.length)
          ]
        }
      })
    },
    navigate({ document, page }) {
      this.document = document
      this.documentPage = page || 1
      nextTick(() => this.goTop())
    },
    clearDocument() {
      this.document = null
      nextTick(() => this.goTop())
    },
    goTop() {
      window.scrollTo(0, this.$refs.toolbar.offsetTop)
    },
    enableSearch() {
      this.showSearch = true
      this.document = null
    },
    clearSearch() {
      this.searcher = null
      if (this.allowToggleSearch) {
        this.showSearch = false
      }
    },
    search({ term, filters }) {
      this.document = null
      console.log('searching for term', term, 'with filters', filters)
      let hasSearch = false
      if (term) {
        hasSearch = true
      }
      for (const value of filters.values()) {
        if (value) {
          hasSearch = true
        }
      }
      if (!hasSearch) {
        this.searcher = null
        return
      }
      this.searcher = {
        term,
        filters,
        url: this.getSearchUrl({ term, filters }),
        done: false,
        results: [],
        documents: []
      }
      getData(this.searcher.url).then((response) =>
        this.documentsReceived(response)
      )
    },
    getSearchUrl({ term, filters }) {
      const baseUrl = this.collection.pages_uri
      const url = new URL(baseUrl, window.location.origin)
      const params = new URLSearchParams(url.search)

      if (term) {
        params.append('q', term)
      } else {
        params.append('number', '1')
      }
      if (this.currentDirectory) {
        params.append('directory', this.currentDirectory.id)
      }
      for (const [key, value] of filters.entries()) {
        if (value) {
          if (typeof value === 'object') {
            for (const urlKey in value) {
              if (value[urlKey]) {
                params.append(urlKey, value[urlKey])
              }
            }
          } else {
            params.append(key, value)
          }
        }
      }

      url.search = params
      return url.toString()
    },
    documentsReceived(response) {
      this.searcher.response = response
      const missingDocs = []
      response.objects.forEach((p) => {
        const docId = getIDFromURL(p.document)
        const document = this.collection.documents[this.collectionIndex[docId]]
        if (document === undefined) {
          missingDocs.push(docId)
        }
      })
      if (missingDocs.length > 0) {
        const url = new URL(
          this.collection.documents_uri,
          window.location.origin
        )
        const params = new URLSearchParams(url.search)
        params.append('ids', missingDocs.join(','))
        url.search = params

        getData(url).then((docsResponse) => {
          this.setSearchResults(response.objects, docsResponse.objects)
        })
      } else {
        this.setSearchResults(response.objects, [])
      }
    },
    setSearchResults(results, resultDocuments) {
      const docsWithPages = []
      const docs = {}
      let docCount = 0
      const docIndex = {}
      const searcherDocs = []
      resultDocuments.forEach((d, i) => (docIndex[d.id] = i))
      results.forEach((p) => {
        const docId = getIDFromURL(p.document)
        const docResult = {
          image: p.image.replace(/\{size\}/, 'small'),
          number: p.number,
          query_highlight: p.query_highlight
        }
        if (docs[p.document] === undefined) {
          let document = this.collection.documents[this.collectionIndex[docId]]
          if (document === undefined) {
            document = resultDocuments[docIndex[docId]]
            if (document === undefined) {
              // Ignore documents that are not or no longer in the collection
              // but somewhow still in the search index
              return
            }
          }
          searcherDocs.push(document)
          docs[p.document] = docCount
          docCount += 1
          docsWithPages.push({
            document,
            pages: [docResult]
          })
        } else {
          docsWithPages[docs[p.document]].pages.push(docResult)
        }
      })
      this.searcher.documents = searcherDocs
      this.searcher.results = docsWithPages
      this.searcher.docCount = docCount
      this.searcher.done = true
    },
    loadMoreSearchResults() {
      this.searcher.done = false
      getData(this.searcher.response.meta.next).then((response) =>
        this.documentsReceived(response)
      )
    },
    selectDirectory(directory) {
      this.currentDirectory = directory
      this.getCollectionData()
    },
    updateHistoryState() {
      if (this.config.deepUrls) {
        window.history.replaceState(
          {},
          '',
          this.queryParams.size == 0
            ? window.location.pathname
            : `?${this.queryParams}`
        )
      }
    },
    updateTooltips() {
      this.$el
        .querySelectorAll("[data-bs-toggle='tooltip']")
        .forEach((el) => Tooltip.getOrCreateInstance(el))
    }
  },
  watch: {
    currentDirectory() {
      this.updateHistoryState()
      this.updateTooltips()
    },
    document() {
      this.updateHistoryState()
    }
  },
  provide() {
    return { config: this.config, i18n: this.config.i18n }
  }
}
</script>

<style lang="scss" scoped>
@import 'bootstrap/scss/functions';
@import 'bootstrap/scss/mixins';
@import 'bootstrap/scss/variables';

.dir-description :deep(a) {
  --#{$prefix}link-color-rgb: var(--#{$prefix}light-rgb);
  --#{$prefix}link-hover-color-rgb: var(--#{$prefix}light-rgb);
  text-decoration: underline;
}
</style>
