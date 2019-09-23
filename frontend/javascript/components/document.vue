<template>
  <div class="document">
    <div class="toolbar">
      <document-toolbar
        :document="document"
        :searcher="searcher"
        :preferences="preferences"
        @navigate="navigate"
        @search="search"
        @updatepreferences="updatePreferences"
        :current-page="currentPage"
      ></document-toolbar>
      <document-searchbar
        v-if="searcher"
        :searcher="searcher"
        @clearsearch="searcher=null"
      ></document-searchbar>
    </div>
    <div class="row">
      <div class="col-md-3 col-2 py-2"
        :class="{'bg-dark': !searcher, 'bg-secondary': !!searcher}"
        ref="sidebarContainer"
      >
        <div class="sidebar" :class="{'preview': !searcher, 'search': !!searcher}">
          <document-search-sidebar
            v-if="searcher"
            :document="document"
            :pages="pagesWithMatches"
            @navigate="navigate"
          ></document-search-sidebar>
          <document-preview-sidebar
            v-else
            :document="document"
            @navigate="navigate"
          ></document-preview-sidebar>
        </div>
      </div>
      <div class="col-md-9 col-10 document-pages-container" ref="documentContainer">
        <document-pages
          :document="document"
          :preferences="preferences"
        ></document-pages>
      </div>
    </div>
  </div>
</template>

<script>
import Vue from 'vue'

import DocumentPages from './document-pages.vue'
import DocumentPreviewSidebar from './document-preview-sidebar.vue'
import DocumentSearchSidebar from './document-search-sidebar.vue'
import DocumentToolbar from './document-toolbar.vue'
import DocumentSearchbar from './document-searchbar.vue'

import docsearch from '../lib/docsearch.js'

import {getData} from '../lib/utils.js'

export default {
  name: 'document',
  props: {
    documentUrl: {
      type: String
    },
    documentPreview: {
      type: Object,
    },
    page: {
      type: Number,
      default: null
    },
    config: {
      type: Object,
      default: () => ({})
    }
  },
  components: {
    DocumentToolbar,
    DocumentSearchbar,
    DocumentPages,
    DocumentPreviewSidebar,
    DocumentSearchSidebar
  },
  data () {
    let doc = this.documentPreview
    this.pageTemplate = decodeURI(this.documentPreview.page_template)
    doc.pages = this.processPages([
      ...doc.pages,
      ...Array(doc.num_pages - doc.pages.length)
    ])
    return {
      preferences: {
        showText: false,
      },
      document: doc,
      searcher: null,
      searchIndex: null,
      currentPage: this.getLocationHashPage() || this.page || 1
    }
  },
  created () {
    getData(this.documentUrl).then((doc) => {
      docsearch.addDocuments(doc.pages)
      doc.pages = this.processPages(doc.pages)
      this.document = doc
    })
  },
  mounted () {
    window.addEventListener('resize', () => {
      console.log('resize')
      Vue.set(this.document, 'pages', this.processPages(this.document.pages))
    })
  },
  computed: {
    i18n () {
      return this.config.i18n
    },
    pages () {
      if (this.document !== null) {
        return this.document.pages
      }
    },
    pagesWithMatches () {
      if (this.searcher === null) {
        return []
      }
      var resultPages = []
      var lastPage = null
      this.searcher.results.forEach((r) => {
        if (lastPage !== null && r.number === lastPage.number) {
          lastPage.count += 1
          lastPage.results.push(r)
        } else {
          lastPage = {
            number: r.number,
            count: 1,
            results: [r]
          }
          resultPages.push(lastPage)
        }
      })
      return resultPages
    }
  },
  methods: {
    getLocationHashPage () {
      let match = document.location.hash.match(/page-(\d+)/)
      if (match !== null) {
        return parseInt(match[1], 10)
      }
      return null
    },
    processPages (pages) {
      return pages.map((p, index) => {
        if (p === undefined) {
          return {
            normalSize: 1000,
            smallSize: 255,
            number: index + 1,
          }
        }

        let normalWidth = 700
        if (this.$refs.documentContainer) {
          normalWidth = Math.min(this.$refs.documentContainer.clientWidth - 30, normalWidth)
        }
        console.log('Setting page width to', normalWidth)
        let smallWidth = 180
        if (this.$refs.sidebarContainer) {
          smallWidth = Math.min(this.$refs.sidebarContainer.clientWidth - 30, smallWidth)
        }
        let ratio = p.height / p.width
        p.normalSize = Math.ceil(normalWidth * ratio) + 60
        p.smallSize = Math.ceil(smallWidth * ratio) + 40
        p.image_url = this.pageTemplate.replace(/\{page\}/, p.number)
        return p
      })
    },
    navigateSidebar (number) {
      let offset = this.document.pages.filter((p) => p.number < number)
        .map((p) => p.smallSize)
        .reduce((a, v) => a + v, 0)

      const sidebar = this.$refs.sidebarContainer.querySelector(
        '.document-preview-pages'
      )
      let top = sidebar.offsetTop
      sidebar.scrollTo(0, offset)
    },
    navigate ({number, source}) {
      this.currentPage = number
      let offset = this.document.pages.filter((p) => p.number < number)
        .map((p) => p.normalSize)
        .reduce((a, v) => a + v, 0)
      let top = this.$refs.documentContainer.offsetTop
      window.scrollTo(0, top + offset)
      if (source !== 'sidebar') {
        this.navigateSidebar(number)
      }
    },
    search (term) {
      console.log('searching for term', term)
      this.searcher = docsearch.searchDocuments(term)
      this.searcher.done(() => {
        console.log('search done')
      })
      this.$nextTick(() => this.searcher.start())
    },
    clearSearch () {
      this.searcher = null
      this.searchIndex = null
    },
    updatePreferences (update) {
      for (let key in update) {
        Vue.set(this.preferences, key, update[key])
      }
    }
  }
}
</script>

<style lang="scss">
.toolbar {
  position: sticky;
  top: 0;
  z-index: 30;
}
.sidebar {
  height: 100vh;
  overflow: auto;
  top: 50px;
  position: sticky;
}
.sidebar.search {
  top: 90px;
}
.document-pages-container {
  padding-right: 0;
  border-right: 15px solid #343a40;
  border-bottom: 15px solid #343a40;
}
</style>
