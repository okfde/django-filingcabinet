<template>
  <div class="row py-2 bg-dark toolbar-row">
    <div
      v-if="preferences.showSidebarToggle || preferences.showOutlineToggle"
      class="col-auto px-1 px-sm-2"
    >
      <div
        class="btn-group"
        role="group"
      >
        <button
          v-if="preferences.showSidebarToggle"
          type="button"
          class="btn btn-sm btn-secondary"
          :class="{'active': preferences.showSidebar}"
          :disabled="!!searcher"
          @click="toggleShowSidebar"
        >
          <i
            class="fa"
            :class="{'fa-toggle-left': preferences.showSidebar, 'fa-toggle-right': !preferences.showSidebar}"
          />
        </button>
        <button
          v-if="preferences.showOutlineToggle"
          type="button"
          class="btn btn-sm btn-secondary"
          :class="{'active': preferences.showOutline}"
          @click="toggleShowOutline"
        >
          <i
            class="fa fa-list-ul"
          />
        </button>
      </div>
    </div>
    <div
      v-if="preferences.showPageNumberInput"
      class="col col-md-auto pe-0 ps-1 px-sm-2"
    >
      <div class="input-group input-group-sm">
        <input
          v-model="page"
          type="number"
          class="page-number-input form-control bg-light form-control-sm"
          min="1"
          :max="document.num_pages"
          @change="submitChange"
        >
        <span class="d-none d-sm-inline input-group-text">/ {{ document.num_pages }}</span>
      </div>
    </div>
    <div
      v-if="preferences.showTextToggle"
      class="col col-md-auto ps-0 pe-1 px-sm-2"
    >
      <div
        class="btn-group"
        role="group"
      >
        <button
          class="btn btn-sm btn-secondary"
          :class="{'btn-light': preferences.showDocumentProperties}"
          @click="showInfo"
        >
          <i class="fa fa-info-circle" />
          <span class="visually-hidden">{{ i18n.info }}</span>
        </button>
        <button
          type="button"
          class="btn btn-sm btn-secondary"
          :class="{'btn-light': preferences.showText}"
          @click="toggleShowText"
        >
          <i class="fa fa-file-text" />
          <span class="visually-hidden">{{ i18n.show_text }}</span>
        </button>
        <button
          class="btn btn-sm btn-secondary"
          @click="download"
        >
          <i class="fa fa-download" />
          <span class="visually-hidden">{{ i18n.downloadPDF }}</span>
        </button>
      </div>
    </div>
    <div
      v-if="preferences.showZoom"
      class="col col-md-auto px-1 px-sm-2"
    >
      <div
        class="btn-group"
        role="group"
      >
        <button
          type="button"
          class="btn btn-sm btn-secondary"
          :disabled="!canZoomOut"
          @click="$emit('zoomout')"
        >
          <i class="fa fa-search-minus" />
        </button>
        <button
          type="button"
          class="btn btn-sm btn-secondary"
          :disabled="!canZoomIn"
          @click="$emit('zoomin')"
        >
          <i class="fa fa-search-plus" />
        </button>
      </div>
    </div>
    <div
      v-if="preferences.showSearch"
      class="col col-sm-auto px-1 px-sm-2 ms-auto text-end"
    >
      <button
        type="button"
        class="btn btn-sm btn-secondary"
        :class="{'btn-light': preferences.showSearchbar}"
        @click="toggleShowSearchbar"
      >
        <i class="fa fa-search" />
      </button>
    </div>
    <div
      v-if="preferences.showAnnotationsToggle"
      class="col-auto px-1 px-sm-2 text-end"
    >
      <div
        class="btn-group"
        role="group"
      >
        <button

          type="button"
          class="btn btn-sm btn-secondary"
          :class="{'btn-light': preferences.showAnnotations}"
          @click="toggleShowAnnotations"
        >
          <i class="fa fa-commenting-o" />
          <span
            v-if="!preferences.showAnnotations && annotationCount && annotationCount > 0"
            class="badge text-bg-light rounded-pill bg-annotation-count"
          >
            {{ annotationCount }}
          </span>
        </button>
      </div>
    </div>
  </div>
</template>

<script>

import { triggerDownload } from "../lib/utils.js"

export default {
  name: 'DocumentToolbar',
  props: [
    'document', 'searcher', 'preferences', 'currentPage',
    'zoom', 'isSmallScreen', 'annotationCount', 'pdfDocument'
  ],
  data () {
    return {
      storedPage: this.currentPage
    }
  },
  computed: {
    i18n () {
      return this.$root.config.i18n
    },
    page: {
      get () {
        return this.currentPage
      },
      set (number) {
        if (number > this.document.num_pages) {
          number = this.document.num_pages
        }
        if (number < 1) {
          number = 1
        }
        this.storedPage = number
      }
    },
    canZoomIn () {
      return this.zoom < 3
    },
    canZoomOut () {
      return this.zoom > 1
    },
  },
  methods: {
    submitChange () {
      this.navigate(this.storedPage)
    },
    navigate (number) {
      this.$emit('navigate', {
        number: number,
        source: 'toolbar'
      })
    },
    toggleShowText () {
      this.$emit('updatepreferences', {showText: !this.preferences.showText})
    },
    toggleShowSidebar () {
      if (this.preferences.showSidebar) {
        if (this.preferences.showOutline) {
          this.$emit('updatepreferences', {showOutline: !this.preferences.showOutline})
        }
      }
      this.$emit('updatepreferences', {showSidebar: !this.preferences.showSidebar})
    },
    toggleShowSearchbar () {
      if (this.preferences.showSearchbar) {
        this.$emit('clearsearch')
      } else {
        this.$emit('updatepreferences', {showSearchbar: true})
      }
    },
    toggleShowOutline () {
      if (!this.preferences.showSidebar) {
        this.$emit('updatepreferences', {showSidebar: true})
      }
      this.$emit('updatepreferences', {showOutline: !this.preferences.showOutline})
    },
    toggleShowAnnotations () {
      this.$emit('updatepreferences', {showAnnotations: !this.preferences.showAnnotations})
    },
    download () {
      let filename = this.document.slug
      if (filename.length === 0) {
        filename = `${this.document.id}.pdf`
      } else {
        filename = `${filename}.pdf`
      }
      if (this.pdfDocument) {
        this.pdfDocument.getData().then((data) => {
          const blob = new Blob([data], { type: "application/pdf" });
          const blobUrl = URL.createObjectURL(blob);
          triggerDownload(blobUrl, filename)
        }).catch(() => this.downloadByUrl(filename))
      } else {
        this.downloadByUrl(filename)
      }
    },
    downloadByUrl (filename) {
      triggerDownload(this.document.file_url, filename)
    },
    showInfo () {
      this.$emit('showinfo')
    }
  }
}
</script>

<style lang="scss" scoped>
.toolbar-row {
  position: relative;
  z-index: 30;
}
.page-number-input {
  max-width: 70px;
  text-align: right;
}
.bg-annotation-count {
  position: absolute !important;
  top: -5px !important;
  right: -5px !important;
}
</style>
