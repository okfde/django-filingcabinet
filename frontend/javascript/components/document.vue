<template>
  <div class="document" ref="document" :style="documentStyle">
    <div class="toolbar" ref="toolbar">
      <document-toolbar
        v-if="preferences.showToolbar"
        :document="document"
        :searcher="searcher"
        :preferences="preferences"
        :current-page="currentPage"
        :default-search="preferences.defaultSearch"
        :zoom="zoom"
        :is-small-screen="isSmallScreen"
        @navigate="navigate"
        @search="search"
        @updatepreferences="updatePreferences"
        @zoomin="zoomIn"
        @zoomout="zoomOut"
      ></document-toolbar>
      <document-searchbar
        v-if="searcher"
        :searcher="searcher"
        :search-index="searchIndex"
        :pages="pagesWithMatches"
        @movesearchindex="moveSearchIndex"
        @clearsearch="clearSearch"
      ></document-searchbar>
    </div>
    <div class="row">
      <div class="col-md-3 col-2 px-0"
        :class="{'bg-dark': !searcher, 'bg-secondary': !!searcher}"
        ref="sidebarContainer"
        v-if="preferences.showSidebar || searcher"
      >
        <div class="sidebar"
          :class="{'preview': !searcher, 'search': !!searcher}"
          :style="sidebarStyle">
          <div class="sidebar-content" :style="sidebarContentStyle">
            <document-search-sidebar
              v-if="searcher"
              :document-pages="document.pages"
              :pages="pagesWithMatches"
              :current-page="currentPage"
              @navigate="navigate"
            ></document-search-sidebar>
            <document-preview-sidebar
              v-else
              :pages="document.pages"
              @navigate="navigate"
              @navigatesidebar="navigateSidebar(currentPage)"
            ></document-preview-sidebar>
          </div>
        </div>
      </div>
      <div class="col document-pages-container bg-light"
        :class="{'annotations-hidden': !preferences.showAnnotations, '-sm': isSmallScreen}"
        ref="documentContainer">
        <document-pages
          :document="document"
          :pages="document.pages"
          :annotations="annotations"
          :current-annotation="currentAnnotation"
          :preferences="preferences"
          :active-annotation-form="activeAnnotationForm"
          :width="documentContainerWidth"
          @initialized="pagesInitialized"
          @currentpage="updateCurrentPage"
          @currentannotation="updateCurrentAnnotation"
          @activateannotationform="activateAnnotationForm"
        ></document-pages>
      </div>
      <div v-if="preferences.showAnnotations" class="col-4 bg-light annotation-sidebar">
        <annotation-sidebar
          :document="document"
          :annotations="annotations"
          :current-annotation="currentAnnotation"
          :can-annotate="canAnnotate"
          :active-annotation-form="activeAnnotationForm"
          @currentannotation="updateCurrentAnnotation"
          @activateannotationform="activateAnnotationForm"
          @deleteannotation="deleteAnnotation"
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

import {getData, postData} from '../lib/utils.js'

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
    },
    defaults: {
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
  data () {
    let doc = this.documentPreview
    this.pageTemplate = decodeURI(this.documentPreview.page_template)
    doc.pages = [
      ...Array(this.page - 1),
      ...doc.pages,
      ...Array(doc.num_pages - doc.pages.length - (this.page - 1))
    ]
    let preferences = {
      showToolbar: true,
      showTextToggle: true,
      showZoom: true,
      showSearch: true,
      showSidebarToggle: true,
      showAnnotationsToggle: true,
      showText: false,
      showSidebar: true,
      showAnnotations: false,
      maxHeight: null,
      defaultSearch: null,
      defaultZoom: 1
    }
    Object.assign(preferences, this.defaults)
    return {
      preferences: preferences,
      zoom: preferences.defaultZoom,
      document: doc,
      searcher: null,
      searchIndex: null,
      currentPage: 1,
      targetPage: this.getLocationHashPage() || this.page || 1,
      annotations: {},
      currentAnnotation: null,
      activeAnnotationForm: null,
      resizing: false,
      documentContainerWidth: null,
      sidebarContainerWidth: null,
      documentHeight: null,
      toolbarHeight: null,
      isSmallScreen: true,
      isMediumScreen: true,
    }
  },
  created () {
    this.document.pages = this.processPages(this.document.pages)
    this.resizing = true
    getData(this.documentUrl).then((doc) => {
      this.document = doc
      this.document.loaded = true
      Vue.set(this.document, 'pages',  this.processPages(doc.pages, true))
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
    this.calcResponsive()
    window.addEventListener('resize', () => {
      console.log('resize')
      this.resize()
    })
    if (this.preferences.defaultSearch) {
      this.search(this.preferences.defaultSearch)
    }
    let el = document.querySelector('[name=csrfmiddlewaretoken]')
    if (el !== null) {
      this.$root.csrfToken = el.value
    }
  },
  computed: {
    i18n () {
      return this.config.i18n
    },
    processedPages () {
      return this.document.pages // = this.processPages(this.document.pages)
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
    },
    isFramed () {
      return !!this.preferences.maxHeight
    },
    canAnnotate () {
      return this.$root.csrfToken && (
        this.config.settings.isOwner || this.document.allow_annotation
      )
    },
    documentStyle () {
      if (this.isFramed) {
        return {
          height: this.preferences.maxHeight,
          overflow: 'auto',
          padding: '0 15px'
        }
      }
      return {}
    },
    sidebarStyle () {
      return {
        top: (this.toolbarHeight || 0) + 'px'
      }
    },
    sidebarContentStyle () {
      if (!this.isFramed) {
        return {
          height: '100vh'
        }
      }
      if (this.documentHeight && this.toolbarHeight) {
        return {
          height: (this.documentHeight - this.toolbarHeight) + 'px'
        }
      }
      return {
        height: '100vh'
      }
    }
  },
  methods: {
    resize (scrollRatio) {
      console.log('resize called', scrollRatio)
      this.resizing = true
      Vue.nextTick(() => {
        this.calcResponsive()
        Vue.set(this.document, 'pages', this.processPages(this.document.pages))
        Vue.nextTick(() => {
          if (scrollRatio) {
            let top = this.$refs.documentContainer.offsetTop
            console.log('scrolling to ', scrollRatio)
            if (this.isFramed) {
              let d = this.$refs.document
              d.scrollTo(0, Math.round(d.scrollHeight * scrollRatio))
            } else {
              window.scrollTo(0, Math.round(document.documentElement.scrollHeight * scrollRatio))
            }
          }
          this.resizing = false
        })
      })
    },
    pagesInitialized () {
      if (this.targetPage !== this.currentPage) {
        this.navigate({number: this.targetPage, source: 'mounted', force: true})
      }
    },
    calcResponsive () {
      if (this.$refs.document) {
        this.isMediumScreen = this.$refs.document.clientWidth < 960
        this.isSmallScreen = this.$refs.document.clientWidth < 600
      }
      if (this.$refs.documentContainer) {
        this.documentContainerWidth = this.$refs.documentContainer.clientWidth - 30 // - padding
      }
      if (this.$refs.sidebarContainer) {
        this.sidebarContainerWidth = this.$refs.sidebarContainer.clientWidth
      }
      if (this.$refs.toolbar) {
        this.toolbarHeight = this.$refs.toolbar.clientHeight
      }
      if (this.$refs.document) {
        this.documentHeight = this.$refs.document.clientHeight
      }
      if (this.isSmallScreen) {
        this.preferences.showSidebar = false
        this.preferences.showSidebarToggle = false
      }
    },
    getLocationHashPage () {
      let match = document.location.hash.match(/page-(\d+)/)
      if (match !== null) {
        return parseInt(match[1], 10)
      }
      return null
    },
    processPages (pages, rerun) {
      let normalWidth = 700
      if (this.documentContainerWidth) {
        normalWidth = Math.min(this.documentContainerWidth, normalWidth)
      }
      let zoomedWidth = normalWidth * this.zoom
      if (!rerun && this.lastZoomedWidth === zoomedWidth) {
        return pages
      }
      this.lastZoomedWidth = zoomedWidth
      console.log('Setting page width to', zoomedWidth, 'normal:', normalWidth)
      let smallWidth = 180
      if (this.sidebarContainerWidth) {
        smallWidth = Math.min(this.sidebarContainerWidth, smallWidth)
      }

      return pages.map((p, index) => {
        if (p === undefined || p.width === undefined) {
          return {
            zoomedWidth: zoomedWidth,
            normalSize: 1000,
            smallSize: 255,
            number: index + 1,
          }
        }
        p.image_url = this.pageTemplate.replace(/\{page\}/, p.number)
        let ratio = p.height / p.width
        Vue.set(p, 'zoomedWidth', zoomedWidth)
        Vue.set(p, 'normalSize', Math.ceil(zoomedWidth * ratio) + 60)
        Vue.set(p, 'smallSize', Math.ceil(smallWidth * ratio) + 40)
        return p
      })
    },
    navigateSidebar (number) {
      if (this.searcher !== null) {
        return
      }
      let offset = this.processedPages.filter((p) => p.number < number)
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
    navigate ({number, source, searchIndex, force}) {
      if (number === this.currentPage && !force) {
        console.log('Not Navigate', this.currentPage, number, source)
        return
      }
      console.log('Navigate from', this.currentPage, 'to', number, source, force)
      let offset = this.processedPages.filter((p) => p.number < number)
        .map((p) => p.normalSize)
        .reduce((a, v) => a + v, 0)
      let top = this.$refs.documentContainer.offsetTop
      if (this.isFramed) {
        this.$refs.document.scrollTo(0, offset)
      } else {
        window.scrollTo(0, top + offset)
      }
      this.currentPage = number
      console.log('navigate scroll', offset)
      if (source !== 'sidebar' && source !== 'search') {
        this.navigateSidebar(number)
      }
      if (searchIndex !== undefined) {
        this.searchIndex = searchIndex
      }
    },
    search (term) {
      console.log('searching for term', term)
      if (this.isMediumScreen && this.preferences.showAnnotations) {
        Vue.set(this.preferences, 'showAnnotations', false)
      }
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
      this.willResize()
    },
    moveSearchIndex (move) {
      this.searchIndex += move
      let page = this.pagesWithMatches[this.searchIndex]
      this.navigate({
        number: page.number,
        source: 'search',
      })
    },
    clearSearch () {
      this.searcher = null
      this.willResize()
    },
    zoomIn () {
      this.zoom = Math.min(3, this.zoom + 0.5)
      this.willResize(true)
    },
    zoomOut () {
      this.zoom = Math.max(1, this.zoom - 0.5)
      this.willResize(true)
    },
    updatePreferences (update) {
      for (let key in update) {
        Vue.set(this.preferences, key, update[key])
      }
      if (this.isMediumScreen) {
        if (update.showSidebar && this.preferences.showAnnotations) {
          Vue.set(this.preferences, 'showAnnotations', false)
        } else if (update.showAnnotations && this.preferences.showSidebar) {
          Vue.set(this.preferences, 'showSidebar', false)
        }
      }
      if (update.showSidebar !== undefined || update.showAnnotations !== undefined) {
        this.willResize(true)
      }
    },
    willResize (preserveScroll) {
      this.resizing = true
      let scrollRatio = null
      if (preserveScroll) {
        if (this.isFramed) {
          let d = this.$refs.document
          if (d) {
            scrollRatio = d.scrollTop / d.scrollHeight
          }
        } else {
          let h = document.documentElement, 
            b = document.body,
            st = 'scrollTop',
            sh = 'scrollHeight';

          scrollRatio = (h[st]||b[st]) / ((h[sh]||b[sh]));
        }
      }
        
      this.resize(scrollRatio)
    },
    updateCurrentPage ({start, end}) {
      if (this.resizing || !this.document.loaded) {
        return
      }

      let currentIndex
      let diff = end - start
      if (diff <= 2) {
        // top of page, default to top
        currentIndex = start
      } else {
        currentIndex = start + Math.floor(diff / 2)
      }
      let page = this.document.pages[currentIndex].number
      if (page !== this.currentPage) {
        this.currentPage = page
        this.navigateSidebar(this.currentPage)
      }
    },
    updateCurrentAnnotation (annotationId) {
      this.currentAnnotation = annotationId
    },
    activateAnnotationForm (info) {
      if (info === null) {
        this.activeAnnotationForm = null
        return
      }
      let obj = this.activeAnnotationForm || {}
      Object.assign(obj, info)
      this.activeAnnotationForm = obj
      if (!this.activeAnnotationForm.ready) {
        return
      }
      postData(
        this.config.urls.pageAnnotationApiUrl, 
        {
          document: this.document.id,
          page_number: this.activeAnnotationForm.number,
          ...this.activeAnnotationForm,
        },
        this.$root.csrfToken
      ).then((data) => {
        if (data.status === 'success') {
          let annotation = data.annotation
          Vue.set(this.annotations, annotation.number, [
            ...(this.annotations[annotation.number] || []),
            annotation
          ])
          this.currentAnnotation = annotation.id
        }
      })
    },
    deleteAnnotation(annotation) {
      if (window.confirm(this.i18n.deleteAnnotation)) {
        let pageAnnotations = this.annotations[annotation.number].filter((a) => a.id !== annotation.id)
        Vue.set(this.annotations, annotation.number, pageAnnotations)
        let url = `${this.config.urls.pageAnnotationApiUrl}${annotation.id}/?document=${this.document.id}`
        postData(url, {}, this.$root.csrfToken, 'DELETE')
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
  position: sticky;
}
.sidebar-content {
  overflow: auto;
}
.annotation-sidebar {
  padding-left: 0 !important;
}
</style>
