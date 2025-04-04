<template>
  <div class="row py-2 bg-dark toolbar-row">
    <div
      v-if="preferences.showSidebarToggle || preferences.showOutlineToggle"
      class="col-auto px-1 px-sm-2"
    >
      <div class="btn-group" role="group">
        <button
          v-if="preferences.showSidebarToggle"
          type="button"
          class="btn btn-sm btn-secondary"
          :class="{ active: preferences.showSidebar }"
          :disabled="!!searcher"
          @click="toggleShowSidebar"
        >
          <i
            class="fa"
            :class="{
              'fa-toggle-left': preferences.showSidebar,
              'fa-toggle-right': !preferences.showSidebar
            }"
          />
        </button>
        <button
          v-if="preferences.showOutlineToggle"
          type="button"
          class="btn btn-sm btn-secondary"
          :class="{ active: preferences.showOutline }"
          @click="toggleShowOutline"
        >
          <i class="fa fa-list-ul" />
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
        />
        <span class="d-none d-sm-inline input-group-text"
          >/ {{ document.num_pages }}</span
        >
      </div>
    </div>
    <div
      v-if="preferences.showTextToggle"
      class="col col-md-auto ps-0 pe-1 px-sm-2"
    >
      <div class="btn-group" role="group">
        <button
          class="btn btn-sm btn-secondary"
          :class="{ 'btn-light': preferences.showDocumentProperties }"
          @click="showInfo"
          :title="i18n.info"
          data-bs-toggle="tooltip"
        >
          <i class="fa fa-info-circle" />
          <span class="visually-hidden">{{ i18n.info }}</span>
        </button>
        <button
          type="button"
          class="btn btn-sm btn-secondary"
          :class="{ 'btn-light': preferences.showText }"
          @click="toggleShowText"
          :title="i18n.showText"
          data-bs-toggle="tooltip"
        >
          <i class="fa fa-file-text" />
          <span class="visually-hidden">{{ i18n.showText }}</span>
        </button>
        <a
          v-if="!document.properties._hide_download"
          :href="document.file_url"
          rel="noopener"
          class="btn btn-sm btn-secondary"
          @click="download"
          :title="i18n.downloadPDF"
          data-bs-toggle="tooltip"
        >
          <i class="fa fa-download" />
          <span class="visually-hidden">{{ i18n.downloadPDF }}</span>
        </a>
        <CopyButton
          class="btn btn-sm btn-secondary"
          :copy-text="document.site_url"
          :title="i18n.copyDocumentLink"
        >
          <i class="fa fa-link" />
          <span class="visually-hidden">{{ i18n.copyDocumentLink }}</span>
        </CopyButton>
      </div>
    </div>
    <div v-if="preferences.showZoom" class="col col-md-auto px-1 px-sm-2">
      <div class="btn-group" role="group">
        <button
          type="button"
          class="btn btn-sm btn-secondary"
          :disabled="!canZoomOut"
          @click="$emit('zoomout')"
          :title="i18n.zoomOut"
          data-bs-toggle="tooltip"
        >
          <i class="fa fa-search-minus" />
          <span class="visually-hidden">{{ i18n.zoomOut }}</span>
        </button>
        <button
          type="button"
          class="btn btn-sm btn-secondary"
          :disabled="!canZoomIn"
          @click="$emit('zoomin')"
          :title="i18n.zoomIn"
          data-bs-toggle="tooltip"
        >
          <i class="fa fa-search-plus" />
          <span class="visually-hidden">{{ i18n.zoomIn }}</span>
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
        :class="{ 'btn-light': preferences.showSearchbar }"
        @click="toggleShowSearchbar"
        :title="i18n.showSearchbar"
        data-bs-toggle="tooltip"
      >
        <i class="fa fa-search" />
        <span class="visually-hidden">{{ i18n.showSearchbar }}</span>
      </button>
    </div>
    <div
      v-if="preferences.showAnnotationsToggle"
      class="col-auto px-1 px-sm-2 text-end"
    >
      <div class="btn-group" role="group">
        <button
          type="button"
          class="btn btn-sm btn-secondary"
          :class="{ 'btn-light': preferences.showAnnotations }"
          @click="toggleShowAnnotations"
        >
          <i class="fa fa-commenting-o" />
          <span
            v-if="
              !preferences.showAnnotations &&
              annotationCount &&
              annotationCount > 0
            "
            class="badge text-bg-light rounded-pill bg-annotation-count"
          >
            {{ annotationCount }}
            <span class="visually-hidden">{{ i18n.annotations }}</span>
          </span>
          <span v-if="!preferences.showAnnotations" class="visually-hidden">{{
            i18n.showAnnotations
          }}</span>
          <span v-else class="visually-hidden">{{ i18n.hideAnnotations }}</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { Tooltip } from 'bootstrap'
import { triggerDownload } from '../lib/utils.js'
import CopyButton from './copy-button.vue'

export default {
  name: 'DocumentToolbar',
  props: {
    document: {
      type: Object,
      required: true
    },
    searcher: {
      type: Object,
      default: null
    },
    preferences: {
      type: Object,
      required: true
    },
    currentPage: {
      type: Number,
      required: true
    },
    zoom: {
      type: Number,
      required: true
    },
    isSmallScreen: {
      type: Boolean,
      default: true
    },
    annotationCount: {
      type: Number,
      default: 0
    },
    pdfDocument: {
      type: Object,
      default: null
    }
  },
  emits: [
    'clearsearch',
    'navigate',
    'showinfo',
    'updatepreferences',
    'zoomin',
    'zoomout'
  ],
  components: { CopyButton },
  data() {
    return {
      storedPage: this.currentPage
    }
  },
  computed: {
    i18n() {
      return this.$root.config.i18n
    },
    page: {
      get() {
        return this.currentPage
      },
      set(number) {
        if (number > this.document.num_pages) {
          number = this.document.num_pages
        }
        if (number < 1) {
          number = 1
        }
        this.storedPage = number
      }
    },
    canZoomIn() {
      return this.zoom < 3
    },
    canZoomOut() {
      return this.zoom > 1
    }
  },
  methods: {
    submitChange() {
      this.navigate(this.storedPage)
    },
    navigate(number) {
      this.$emit('navigate', {
        number,
        source: 'toolbar'
      })
    },
    toggleShowText() {
      this.$emit('updatepreferences', { showText: !this.preferences.showText })
    },
    toggleShowSidebar() {
      if (this.preferences.showSidebar) {
        if (this.preferences.showOutline) {
          this.$emit('updatepreferences', {
            showOutline: !this.preferences.showOutline
          })
        }
      }
      this.$emit('updatepreferences', {
        showSidebar: !this.preferences.showSidebar
      })
    },
    toggleShowSearchbar() {
      if (this.preferences.showSearchbar) {
        this.$emit('clearsearch')
      } else {
        this.$emit('updatepreferences', { showSearchbar: true })
      }
    },
    toggleShowOutline() {
      if (!this.preferences.showSidebar) {
        this.$emit('updatepreferences', { showSidebar: true })
      }
      this.$emit('updatepreferences', {
        showOutline: !this.preferences.showOutline
      })
    },
    toggleShowAnnotations() {
      this.$emit('updatepreferences', {
        showAnnotations: !this.preferences.showAnnotations
      })
    },
    download(e) {
      if (e) {
        e.preventDefault()
      }
      let filename = this.document.slug
      if (filename.length === 0) {
        filename = `${this.document.id}.pdf`
      } else {
        filename = `${filename}.pdf`
      }
      if (this.pdfDocument) {
        this.pdfDocument
          .getData()
          .then((data) => {
            const blob = new Blob([data], { type: 'application/pdf' })
            const blobUrl = URL.createObjectURL(blob)
            triggerDownload(blobUrl, filename)
          })
          .catch(() => this.downloadByUrl(filename))
      } else {
        this.downloadByUrl(filename)
      }
    },
    downloadByUrl(filename) {
      triggerDownload(this.document.file_url, filename)
    },
    showInfo() {
      this.$emit('showinfo')
    }
  },
  mounted() {
    this.$el.querySelectorAll("[data-bs-toggle='tooltip']").forEach((el) => {
      new Tooltip(el)
    })
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
