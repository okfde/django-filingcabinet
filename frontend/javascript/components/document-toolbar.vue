<template>
  <div class="row py-2 bg-dark">
    <div class="col-auto">
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
          @change="navigate"
          @keydown.enter="navigate"
        >
        <div class="input-group-append">
          <span class="input-group-text">/ {{ document.num_pages }}</span>
        </div>
      </div>
    </div>
    <div class="col-auto">
      <div class="btn-group" role="group">
        <button type="button"
          class="btn btn-sm btn-secondary" :class="{'active': preferences.showText}"
          @click="toggleShowText"
        >
          <i class="fa fa-file-text"></i>
        </button>
      </div>
    </div>
    <div class="col-auto ml-auto">
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
    <div class="col-auto">
      <div class="btn-group" role="group">
        <button type="button"
          class="btn btn-sm btn-secondary" :class="{'active': preferences.showAnnotations}"
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
  props: ['document', 'searcher', 'preferences', 'currentPage'],
  data () {
    return {
      search: '',
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
      set (val) {
        this.navigate(val)
      }
    }
  },
  methods: {
    navigate (number) {
      if (number > this.document.num_pages) {
        this.page = this.document.num_pages
        number = this.page
      }
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
