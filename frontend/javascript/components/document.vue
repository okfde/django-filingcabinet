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
        :search-index="searchIndex"
        :pages="pagesWithMatches"
        @movesearchindex="moveSearchIndex"
        @clearsearch="searcher=null"
      ></document-searchbar>
    </div>
    <div class="row">
      <div class="col-md-3 col-2 py-2"
        :class="{'bg-dark': !searcher, 'bg-secondary': !!searcher}"
        ref="sidebarContainer"
        v-if="preferences.showSidebar || searcher"
      >
        <div class="sidebar" :class="{'preview': !searcher, 'search': !!searcher}">
          <document-search-sidebar
            v-if="searcher"
            :document="document"
            :pages="pagesWithMatches"
            :current-page="currentPage"
            @navigate="navigate"
          ></document-search-sidebar>
          <document-preview-sidebar
            v-else
            :document="document"
            @navigate="navigate"
          ></document-preview-sidebar>
        </div>
      </div>
      <div class="col document-pages-container bg-light" :class="{'annotations-hidden': !preferences.showAnnotations}" ref="documentContainer">
        <document-pages
          :document="document"
          :annotations="annotations"
          :current-annotation="currentAnnotation"
          :preferences="preferences"
          @currentpage="updateCurrentPage"
          @currentannotation="updateCurrentAnnotation"
        ></document-pages>
      </div>
      <div v-if="preferences.showAnnotations" class="col-3 col-md-4 bg-light annotation-sidebar">
        <annotation-sidebar
          :document="document"
          :annotations="annotations"
          :current-annotation="currentAnnotation"
          @currentannotation="$emit('currentannotation', $event)"
        >
        </annotation-sidebar>
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
import AnnotationSidebar from './document-annotation-sidebar.vue'

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
    DocumentSearchSidebar,
    AnnotationSidebar
  },
  mounted () {
    this.$root.config = this.config
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
        showSidebar: true,
        showAnnotations: true,
      },
      document: doc,
      searcher: null,
      searchIndex: null,
      currentPage: this.getLocationHashPage() || this.page || 1,
      annotations: {},
      currentAnnotation: null
    }
  },
  created () {
    getData(this.documentUrl).then((doc) => {
      doc.pages = this.processPages(doc.pages)
      this.document = doc
    })
    getData(`${this.config.urls.pageAnnotationApiUrl}?document=${this.document.id}`).then((results) => {
      let annotations = {}
      results.objects.forEach((a) => {
        if (annotations[a.number] === undefined) {
          annotations[a.number] = []
        }
        annotations[a.number].push(a)
      })
      this.annotations = annotations
    })
  },
  mounted () {
    window.addEventListener('resize', () => {
      console.log('resize')
      this.resize()
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
    resize () {
      Vue.set(this.document, 'pages', this.processPages(this.document.pages))
    },
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
      if (this.searcher !== null) {
        return
      }
      let offset = this.document.pages.filter((p) => p.number < number)
        .map((p) => p.smallSize)
        .reduce((a, v) => a + v, 0)

      let sidebarContainer = this.$refs.sidebarContainer
      if (!sidebarContainer) {
        return
      }
      const sidebar = sidebarContainer.querySelector(
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
      if (source !== 'sidebar' && source !== 'search') {
        this.navigateSidebar(number)
      }
    },
    search (term) {
      console.log('searching for term', term)
      this.searcher = {
        term: term,
        done: false,
        results: []
      }
      let searchUrl = `${this.config.urls.pageApiUrl}?document=${this.document.id}&q=${encodeURIComponent(term)}`
      getData(searchUrl).then((response) => {
        this.searcher.response = response
        this.searcher.done = true
        this.searcher.results = response.objects
        if (this.searcher.results.length > 0) {
          this.searchIndex = 0
          this.navigate({
            number: this.searcher.results[0].number,
            source: 'search'
          })
        }
        let pages = {}
        let pageCount = 0
        response.objects.forEach((p) => {
          if (pages[p.number] === undefined) {
            pages[p.number] = true
            pageCount += 1
          }
        })
        this.searcher.pageCount = pageCount
      })
    },
    moveSearchIndex (move) {
      this.searchIndex += move
      let page = this.pagesWithMatches[this.searchIndex]
      this.navigate({
        number: page.number,
        source: 'search'
      })
    },
    clearSearch () {
      this.searcher = null
    },
    updatePreferences (update) {
      for (let key in update) {
        Vue.set(this.preferences, key, update[key])
      }
      if (update.showSidebar !== undefined || update.showAnnotations !== undefined) {
        window.setTimeout(() => {
          this.resize()
        }, 5)
      }
    },
    updateCurrentPage ({start, end}) {
      let currentIndex = start + Math.floor((end - start) / 2)
      this.currentPage = this.document.pages[currentIndex].number
      this.navigateSidebar(this.currentPage)
    },
    updateCurrentAnnotation (annotationId) {
      this.currentAnnotation = annotationId
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
  border-bottom: 15px solid #343a40;
  border-right: 0px;
  &.annotations-hidden {
    padding-right: 0 !important;
    border-right: 15px solid #343a40;
  }
}
.annotation-sidebar {
  padding-left: 0 !important;
  border-right: 15px solid #343a40;
  border-bottom: 15px solid #343a40;
}
</style>
