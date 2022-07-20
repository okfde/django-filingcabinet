<template>
  <div class="row py-2 bg-secondary text-white document-searchbar">
    <div class="col-auto">
      <div
        v-if="searcher && !isSmallScreen"
        class="btn-group"
        role="group"
      >
        <button
          type="button"
          class="btn btn-sm btn-light"
          :disabled="!hasPrev"
          @click="prevSearchResult"
        >
          <i class="fa fa-chevron-left" />
        </button>
        <button
          type="button"
          class="btn btn-sm btn-light"
          :disabled="!hasNext"
          @click="nextSearchResult"
        >
          <i class="fa fa-chevron-right" />
        </button>
        <div
          v-if="searching"
          class="spinner-border spinner-border-sm"
          role="status"
        >
          <span class="visually-hidden">{{ i18n.searching }}</span>
        </div>
      </div>
      <small
        v-if="searcher && searcher.done"
        class="d-none d-sm-inline"
      >
        {{ i18n.found_on }} {{ pages.length }} {{ i18n.pages }}
      </small>
    </div>
    <div class="col col-md-auto ms-auto">
      <div class="input-group input-group-sm">
        <input
          ref="searchInput"
          v-model="search"
          type="text"
          class="search-input form-control form-control-sm"
          @keydown.enter="runSearch"
        >
        <button
          class="btn btn-outline-light"
          @click="runSearch"
        >
          {{ i18n.search }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'DocumentSearchbar',
  props: [
    'searcher', 'searchIndex', 'pages', 'defaultSearch',
    'isSmallScreen'
  ],
  data () {
    return {
      search: this.defaultSearch || '',
    }
  },
  computed: {
    i18n () {
      return this.$root.config.i18n
    },
    searching () {
      return this.searcher && !this.searcher.done
    },
    hasNext () {
      return this.pages.length > 0 && this.searchIndex < this.pages.length - 1
    },
    hasPrev () {
      return this.pages.length > 0 && this.searchIndex > 0
    }
  },
  mounted () {
    this.$refs.searchInput.focus()
  },
  methods: {
    runSearch () {
      this.$emit('search', this.search)
    },
    prevSearchResult () {
      this.$emit('movesearchindex', -1)
    },
    nextSearchResult () {
      this.$emit('movesearchindex', 1)
    },
    clear () {
      this.$emit('clearsearch')
    }
  }
}
</script>

<style lang="scss">
.document-searchbar {
  position: relative;
  z-index: 30;
}
</style>
