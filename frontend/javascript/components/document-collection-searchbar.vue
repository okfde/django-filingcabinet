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
            :value="filterValues.get(filter.key) || ''"
            @input="updateFilter"
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
            <template v-if="searcher.term">
              <template v-if="pageCount == 1">
                {{ pageCount }} {{ i18n.page }}
              </template>
              <template v-else>
                {{ pageCount }} {{ i18n.pages }} {{ i18n.found }} 
              </template>
              –
              <template v-if="resultCount == 1">
                {{ resultCount }} {{ i18n.document }}
              </template>
              <template v-else>
                {{ resultCount }} {{ i18n.documents }}
              </template>
              {{ i18n.areShown }}
            </template>
            <template v-else>
              <template v-if="pageCount == 1">
                {{ pageCount }} {{ i18n.document }}
              </template>
              <template v-else>
                {{ pageCount }} {{ i18n.documents }}
              </template>
              {{ i18n.found }} 
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
      <div
        v-if="hasFacets"
        class="row d-flex mb-2"
      >
        <div
          v-for="facet in facetList"
          :key="facet.key"
          class="col-4"
        >
          <document-facet
            :values="facet.values"
            :filter="facet.filter"
            :value="facet.value"
            @select="setFilter(facet.filter.key, $event)"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script>

import DocumentFilter from './document-filter.vue'
import DocumentFacet from './document-facet.vue'

export default {
  name: 'DocumentCollectionSearchbar',
  components: {
    DocumentFilter,
    DocumentFacet
  },
  props: {
    searcher: {
      type: Object,
      default: null
    },
    filters: {
      type: Array,
      default: () => []
    }
  },
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
    hasFacets () {
      return !!(this.searcher && this.searcher.response && this.searcher.response.facets)
    },
    facetList () {
      let facets = [];
      for (let field in this.searcher.response.facets.fields) {
        let facetValues = this.searcher.response.facets.fields[field];
        if (facetValues.length === 0) {
          continue
        }
        let filter = this.filters.filter(f => f.key === field)[0]
        if (filter === undefined) {
          continue
        }
        facets.push({
          key: filter.key,
          filter: filter,
          values: facetValues,
          value: this.filterValues.get(filter.key) || ''
        })
      }
      return facets
    },
    pageCount () {
      if (this.searcher !== null) {
        return this.searcher.response.meta.total_count
      }
      return 0
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
    setFilter(key, event) {
      this.updateFilter({key, value: event})
      this.runSearch()
    },
    updateFilter ({key, value}) {
      this.filerValues = new Map(this.filterValues.set(key, value))
    }
  }
}
</script>

<style lang="scss">

</style>
