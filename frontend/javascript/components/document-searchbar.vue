<template>
  <div class="row py-1 bg-secondary text-white document-searchbar">
    <div class="col-auto">
      <div
        v-if="searcher"
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
      </div>
      <small v-if="searcher">
        {{ i18n.found_on }} {{ pages.length }} {{ i18n.pages }}
      </small>
    </div>
    <div class="col col-md-auto ml-auto">
      <div
        v-if="searching"
        class="spinner-border spinner-border-sm"
        role="status"
      >
        <span class="sr-only">{{ i18n.searching }}</span>
      </div>
      <div class="input-group input-group-sm">
        <input
          v-model="search"
          type="text"
          class="search-input form-control form-control-sm"
          @keydown.enter="runSearch"
        >
        <div class="input-group-append">
          <button
            class="btn btn-outline-light"
            @click="runSearch"
          >
            {{ i18n.search }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'DocumentSearchbar',
  props: ['searcher', 'searchIndex', 'pages', 'defaultSearch'],
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

</style>
