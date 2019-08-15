<template>
  <div class="document">
    <document-toolbar
      :document="document"
      @navigate="navigate"
      :current-page="currentPage"
    ></document-toolbar>
    <div class="row">
      <div class="col-md-3 col-2 py-2 bg-dark" ref="sidebarContainer">
        <document-preview-sidebar
          :document="document"
          @navigate="navigate"
        ></document-preview-sidebar>
      </div>
      <div class="col-md-9 col-10 document-pages-container" ref="documentContainer">
        <document-pages :document="document"></document-pages>
      </div>
    </div>
  </div>
</template>

<script>
import Vue from 'vue'

import DocumentPages from './document-pages.vue'
import DocumentPreviewSidebar from './document-preview-sidebar.vue'
import DocumentToolbar from './document-toolbar.vue'

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
    }
  },
  components: {
    DocumentToolbar,
    DocumentPages,
    DocumentPreviewSidebar
  },
  data () {
    let doc = this.documentPreview
    doc.pages = this.processPages([
      ...doc.pages,
      ...Array(doc.num_pages - doc.pages.length)
    ])
    return {
      document: doc,
      currentPage: this.getLocationHashPage() || this.page || 1
    }
  },
  created () {
    getData(this.documentUrl).then((doc) => {
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
    previewPages () {

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
        return p
      })
    },
    navigateSidebar (number) {
      let offset = this.document.pages.filter((p) => p.number < number)
        .map((p) => p.smallSize)
        .reduce((a, v) => a + v, 0)
      let top = this.$refs.sidebarContainer.offsetTop
      window.setTimeout(() => {
        this.$refs.sidebarContainer.scrollTo(0, top + offset)
      }, 200)
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
    }
  }
}
</script>

<style lang="scss">
.document-pages-container {
  padding-right: 0;
  border-right: 15px solid #343a40;
  border-bottom: 15px solid #343a40;
}
</style>
