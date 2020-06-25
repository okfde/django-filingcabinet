<template>
  <div
    ref="document"
    class="document"
    :style="documentStyle"
  >
    <div
      ref="toolbar"
      class="toolbar"
    >
      <document-toolbar
        v-if="preferences.showToolbar"
        :document="document"
        :pdf-document="pdfDocument"
        :searcher="searcher"
        :preferences="preferences"
        :current-page="currentPage"
        :zoom="zoom"
        :is-small-screen="isSmallScreen"
        :annotation-count="annotationCount"
        @navigate="navigate"
        @updatepreferences="updatePreferences"
        @zoomin="zoomIn"
        @zoomout="zoomOut"
      />
      <document-searchbar
        v-if="preferences.showSearchbar"
        :searcher="searcher"
        :search-index="searchIndex"
        :pages="pagesWithMatches"
        :default-search="preferences.defaultSearch"
        @search="search"
        @movesearchindex="moveSearchIndex"
      />
    </div>
    <div class="row">
      <div
        v-if="preferences.showSidebar || searcher"
        ref="sidebarContainer"
        class="col-md-3 col-2 px-0"
        :class="{'bg-dark': !searcher, 'bg-secondary': !!searcher}"
      >
        <div
          class="sidebar"
          :class="{'preview': !searcher, 'search': !!searcher}"
          :style="sidebarStyle"
        >
          <div
            class="sidebar-content"
            :style="sidebarContentStyle"
          >
            <document-search-sidebar
              v-if="searcher"
              :document-pages="document.pages"
              :pages="pagesWithMatches"
              :current-page="currentPage"
              :height="sidebarContentHeight"
              @navigate="navigate"
            />
            <document-outline-sidebar
              v-else-if="preferences.showOutline"
              :outline="document.outline"
              :height="sidebarContentHeight"
              @navigate="navigate"
            />
            <document-preview-sidebar
              v-else
              :pages="document.pages"
              :height="sidebarContentHeight"
              @navigate="navigate"
              @navigatesidebar="navigateSidebar(currentPage)"
            />
          </div>
        </div>
      </div>
      <div
        ref="documentContainer"
        class="col document-pages-container bg-light"
        :class="{'annotations-hidden': !preferences.showAnnotations, '-sm': isSmallScreen}"
      >
        <document-pages
          :document="document"
          :pages="document.pages"
          :pdf-document="pdfDocument"
          :annotations="annotations"
          :current-annotation="currentAnnotation"
          :preferences="preferences"
          :active-annotation-form="activeAnnotationForm"
          :width="documentContainerWidth"
          :height="documentViewHeight"
          :can-annotate="canAnnotate"
          @initialized="pagesInitialized"
          @currentpage="updateCurrentPage"
          @currentannotation="updateCurrentAnnotation"
          @activateannotationform="activateAnnotationForm"
          @navigate="navigate"
        />
      </div>
    </div>
  </div>
</template>

<script>
import Vue from 'vue'

import DocumentPages from './document-pages.vue'
import DocumentPreviewSidebar from './document-preview-sidebar.vue'
import DocumentOutlineSidebar from './document-outline-sidebar.vue'
import DocumentSearchSidebar from './document-search-sidebar.vue'
import DocumentToolbar from './document-toolbar.vue'
import DocumentSearchbar from './document-searchbar.vue'

import {getData, postData} from '../lib/utils.js'

const MAX_PDF_SIZE = 1024 * 1024 * 5

function range(size, startAt = 0) {
    return [...Array(size).keys()].map(i => i + startAt);
}

function getPageRange (pageRangeStr) {
  if (!pageRangeStr) {
    return null
  }
  let parts = pageRangeStr.split(',')
  let pages = []
  parts.forEach(part => {
    part = part.trim()
    if (part.indexOf('-') !== -1) {
      let startStop = part.split('-')
      let start = parseInt(startStop[0], 10)
      let stop = parseInt(startStop[1], 10)
      pages = [
        ...pages,
        ...range(stop - start + 1, start)
      ]
    } else {
      pages.push(parseInt(part, 10))
    }
  })
  return pages
}

function getScroll (d) {
  return d.querySelector('.document-pages .scroller')
}

export default {
  name: 'Document',
  components: {
    DocumentToolbar,
    DocumentSearchbar,
    DocumentPages,
    DocumentPreviewSidebar,
    DocumentSearchSidebar,
    DocumentOutlineSidebar,
  },
  props: {
    documentUrl: {
      type: String,
      required: true
    },
    documentPreview: {
      type: Object,
      default: null
    },
    page: {
      type: Number,
      default: 1
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
  data () {
    let doc = this.documentPreview
    if (doc !== null) {
      this.pageTemplate = decodeURI(this.documentPreview.page_template)
      doc.pages = doc.pages || []
      doc.pages = [
        ...Array(this.page - 1),
        ...doc.pages,
        ...Array(doc.num_pages - doc.pages.length - (this.page - 1))
      ]
    }
    let preferences = {
      showToolbar: true,
      showTextToggle: true,
      showZoom: true,
      showSearch: true,
      showSidebarToggle: true,
      showOutlineToggle: doc.outline.length > 0,
      showAnnotationsToggle: null,
      showText: false,
      showSidebar: true,
      showOutline: false,
      showAnnotations: false,
      maxHeight: null,
      defaultSearch: null,
      defaultZoom: 1,
      pageRange: null,
      showSearchbar: false,
      showPageNumberInput: true
    }
    Object.assign(preferences, this.defaults)
    let pageRange = getPageRange(preferences.pageRange)
    if (pageRange) {
      preferences.showPageNumberInput = false
    }
    return {
      annotationCount: 0,
      preferences: preferences,
      zoom: preferences.defaultZoom,
      document: doc,
      pdfDocument: null,
      searcher: null,
      searchIndex: null,
      currentPage: 1,
      pageRange: pageRange,
      targetPage: this.getLocationHashPage() || this.page || 1,
      annotations: {},
      hasAnnotations: false,
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
        this.config.settings.canWrite || this.document.allow_annotation
      )
    },
    showAnnotations () {
      return this.hasAnnotations || this.canAnnotate
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
      if (this.isFramed) {
        if (this.toolbarHeight) {
          return {
            height: (this.documentHeight - this.toolbarHeight) + 'px'
          }
        }
      } else {
        if (this.toolbarHeight) {
          return {
            height: (window.innerHeight - this.toolbarHeight) + 'px'
          }
        }
      }
      return {
        height: '90vh'
      }
    },
    sidebarContentHeight () {
      return this.sidebarContentStyle.height
    },
    documentViewHeight () {
      if (this.isFramed) {
        return (this.documentHeight - this.toolbarHeight) + 'px'
      }
      return null
    }
  },
  created () {
    let el = document.querySelector('[name=csrfmiddlewaretoken]')
    if (el !== null) {
      this.$root.csrfToken = el.value
    }
    this.document.pages = this.processPages(this.document.pages)
    this.resizing = true
    getData(this.documentUrl).then((doc) => {
      this.pageTemplate = decodeURI(doc.page_template)
      this.document = doc
      this.document.loaded = true
      Vue.set(this.document, 'pages',  this.processPages(doc.pages, true))
      this.willResize()
      if (this.document.file_size <= MAX_PDF_SIZE) [
        this.loadPDF()
      ]
    })
    getData(`${this.config.urls.pageAnnotationApiUrl}?document=${this.document.id}`).then((results) => {
      let annotations = {}
      results.objects.forEach((a) => {
        if (annotations[a.number] === undefined) {
          annotations[a.number] = []
        }
        annotations[a.number].push(a)
        this.hasAnnotations = true
      })
      this.annotationCount = results.objects.length
      this.annotations = annotations
      if (this.preferences.showAnnotationsToggle === null) {
        // Only show annotation toggle if explicitly set (non-null)
        // and we either have annotations or can annotate
        Vue.set(
          this.preferences, 'showAnnotationsToggle',
          this.hasAnnotations || this.canAnnotate
        )
      }
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
            console.log('scrolling to ', scrollRatio)
            if (this.isFramed) {
              let d = getScroll(this.$refs.document)
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
      // if (this.isSmallScreen) {
      //   this.preferences.showSidebar = false
      //   this.preferences.showSidebarToggle = false
      // }
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
        let pageAvailableWidth = this.documentContainerWidth
        if (this.preferences.showAnnotations) {
          pageAvailableWidth = pageAvailableWidth / 12 * 7
        }
        normalWidth = Math.min(pageAvailableWidth, normalWidth)
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

      let processedPages = pages.map((p, index) => {
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
      if (this.pageRange === null) {
        return processedPages
      }
      let pageMap = {}
      this.pageRange.forEach((p) => pageMap[p] = true)
      return processedPages.filter((p) => !!pageMap[p.number])
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
        '.document-preview-pages .scroller'
      )
      if (sidebar) {
        sidebar.scrollTo(0, offset)
      }
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

      const barOffset = this.$refs.toolbar.clientHeight
      offset -= barOffset
      if (this.isFramed) {
        getScroll(this.$refs.document).scrollTo(0, offset)
      } else {
        let top = this.$refs.documentContainer.offsetTop
        window.scrollTo(0, top + offset)
      }
      this.currentPage = number
      console.log('navigate scroll', offset)
      if (source === 'toolbar') {
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
          let d = getScroll(this.$refs.document)
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
    },
    loadPDF () {
      import('pdfjs-dist').then((PDFJS) => {
        this.$root.PDFJS = PDFJS
        this.$root.PDFJS.GlobalWorkerOptions.workerSrc = this.config.resources.pdfjsWorker
        console.log('Loaded PDFJS', this.config.resources.pdfjsWorker, this.$root.PDFJS)
        console.log('Loading PDF', this.document.file_url)
        let loadingTask = this.$root.PDFJS.getDocument({
          url: this.document.file_url,
          isEvalSupported: false
        })
        loadingTask.promise.then(pdfDocument => {
          this.pdfDocument = pdfDocument
        })
      }).catch((err) =>{
        console.log(err)
      })
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
.document-pages-container {
  position: relative;
}
</style>
