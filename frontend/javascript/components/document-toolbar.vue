<template>
  <div class="row py-2 bg-dark">
    <div v-if="!isSmallScreen && preferences.showSidebarToggle" class="col-auto">
      <div class="btn-group" role="group">
        <button type="button"
          class="btn btn-sm btn-secondary" :class="{'active': preferences.showSidebar}"
          :disabled="!!searcher"
          @click="toggleShowSidebar"
        >
          <i class="fa" :class="{'fa-toggle-left': preferences.showSidebar, 'fa-toggle-right': !preferences.showSidebar}"></i>
        </button>
      </div>
    </div>
    <div class="col-auto">
      <div class="input-group input-group-sm">
        <input type="number" class="page-number-input form-control bg-light form-control-sm"
          v-model="page"
          min="1"
          :max="document.num_pages"
          @change="submitChange"
        >
        <div class="input-group-append">
          <span class="input-group-text">/ {{ document.num_pages }}</span>
        </div>
      </div>
    </div>
    <div v-if="preferences.showTextToggle" class="col-auto">
      <div class="btn-group" role="group">
        <button type="button"
          class="btn btn-sm btn-secondary"
          :class="{'btn-light': preferences.showText}"
          @click="toggleShowText"
        >
          <i class="fa fa-file-text"></i>
          <span class="sr-only">{{ i18n.show_text }}</span>
        </button>
      </div>
    </div>
    <div v-if="preferences.showZoom" class="col-auto ml-auto">
      <div class="btn-group" role="group">
        <button type="button"
          class="btn btn-sm btn-secondary"
          :disabled="!canZoomOut"
          @click="$emit('zoomout')"
        >
          <i class="fa fa-search-minus"></i>
        </button>
        <button type="button"
          class="btn btn-sm btn-secondary"
          :disabled="!canZoomIn"
          @click="$emit('zoomin')"
        >
          <i class="fa fa-search-plus"></i>
        </button>
      </div>
    </div>
    <div v-if="!isSmallScreen && preferences.showSearch" class="col-auto ml-2">
      <div class="input-group input-group-sm">
        <input type="text" class="search-input form-control form-control-sm"
          v-model="search"
          @keydown.enter="runSearch"
        >
        <div class="input-group-append">
          <button class="btn btn-outline-light" @click="runSearch">
            {{ i18n.search }}
          </button>
        </div>
      </div>
    </div>
    <div v-if="preferences.showAnnotationsToggle" class="col-auto">
      <div class="btn-group" role="group">
        <button type="button"
          class="btn btn-sm btn-secondary"
          :class="{'btn-light': preferences.showAnnotations}"
          @click="toggleShowAnnotations"
        >
          <i class="fa fa-commenting-o"></i>
        </button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'document-toolbar',
  props: ['document', 'searcher', 'preferences', 'currentPage',
          'zoom', 'defaultSearch', 'isSmallScreen'],
  data () {
    return {
      search: this.defaultSearch || '',
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
    runSearch () {
      this.$emit('search', this.search)
    },
    toggleShowText () {
      this.$emit('updatepreferences', {showText: !this.preferences.showText})
    },
    toggleShowSidebar () {
      this.$emit('updatepreferences', {showSidebar: !this.preferences.showSidebar})
    },
    toggleShowAnnotations () {
      this.$emit('updatepreferences', {showAnnotations: !this.preferences.showAnnotations})
    }
  }
}
</script>

<style lang="scss">
.page-number-input {
  width: 70px !important;
}
</style>
