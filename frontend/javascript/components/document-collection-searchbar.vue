<template>
  <div class="row py-1 bg-dark text-white document-searchbar">
    <div class="col-12">
      <div
        v-if="hasFilters"
        class="row"
      >
        <div class="col">
          <div class="form-group row">
            <label
              for="document-collection-search"
              class="col-sm-2 col-form-label"
            >
              {{ i18n.searchTerm }}
            </label>
            <div class="col-sm-10">
              <input
                id="document-collection-search"
                v-model="search"
                type="search"
                class="search-input form-control"
                @keydown.enter="runSearch"
              >
            </div>
          </div>
          <document-filter
            v-for="filter in filters"
            :key="filter.id"
            :filter="filter"
            :initial-value="filterValues[filter.id] || ''"
            @change="updateFilter"
          />
        </div>
      </div>
      <div class="row mb-2">
        <div class="col mr-auto">
          <div
            v-if="searching"
            class="spinner-border spinner-border-sm"
            role="status"
          />
          <small v-if="searching">{{ i18n.searching }}</small>
          <small v-if="searcher && searcher.done">
            <template v-if="resultCount == 1">
              {{ resultCount }} {{ i18n.document }} {{ i18n.found }} 
            </template>
            <template v-else>
              {{ resultCount }} {{ i18n.documents }} {{ i18n.found }} 
            </template>
          </small>
        </div>
        <div class="col-auto ml-auto">
          <div
            v-if="!hasFilters"
            class="input-group input-group-sm"
          >
            <input
              v-model="search"
              type="search"
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
          <button
            v-else
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

import DocumentFilter from './document-filter.vue'

export default {
  name: 'DocumentCollectionSearchbar',
  components: {
    DocumentFilter
  },
  props: ['searcher', 'filters'],
  data () {
    return {
      search: this.searcher?.term || '',
      filterValues: this.searcher?.filters || new Map(),
    }
  },
  computed: {
    i18n () {
      return this.$root.config.i18n
    },
    searching () {
      return this.searcher && !this.searcher.done
    },
    hasFilters () {
      return !!this.filters && this.filters.length > 0
    },
    resultCount () {
      if (this.searcher !== null) {
        return this.searcher.docCount
      }
      return 0
    }
  },
  methods: {
    clear () {
      this.$emit('clearsearch')
    },
    runSearch () {
      this.$emit('search', {
        term: this.search,
        filters: this.filterValues
      })
    },
    updateFilter ({key, value}) {
      this.filterValues.set(key, value)
    }
  }
}
</script>

<style lang="scss">

</style>
