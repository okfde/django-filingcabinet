<template>
  <div class="row py-1 bg-dark text-white document-searchbar">
    <div class="col-12">
      <div v-if="hasFilters" class="row">
        <div class="col">
          <div class="mb-3 row">
            <label
              for="document-collection-search"
              class="col-sm-3 col-md-2 col-form-label">
              {{ i18n.searchTerm }}
            </label>
            <div class="col-sm-9 col-md-10">
              <input
                id="document-collection-search"
                v-model="search"
                type="search"
                class="search-input form-control"
                @keydown.enter="runSearch" />
            </div>
          </div>
          <DocumentFilter
            v-for="filter in filters"
            :key="filter.id"
            :filter="filter"
            :value="filterValues.get(filter.key) || ''"
            @input="updateFilter"
            @submit="runSearch" />
        </div>
      </div>
      <div class="row mb-2">
        <div class="col me-auto">
          <div
            v-if="searching"
            class="spinner-border spinner-border-sm"
            role="status" />
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
              <template v-else> {{ pageCount }} {{ i18n.documents }} </template>
              {{ i18n.found }}
            </template>
            <a
              v-if="showSearchFeed"
              :href="rssUrl"
              class="text-white ms-2"
              target="_blank">
              <i class="fa fa-rss" aria-hidden="true" />
            </a>
            <template v-if="directory">
              <br />{{ i18n.searchingInDirectory }} {{ directory.name }}
            </template>
          </small>
        </div>
        <div v-if="searcher" class="col-auto ms-auto me-2">
          <button class="btn btn-dark" @click="clear">
            {{ i18n.clearSearch }}
          </button>
        </div>
        <div class="col-auto ms-auto">
          <div v-if="!hasFilters" class="input-group input-group-sm">
            <input
              v-model="search"
              type="search"
              class="search-input form-control form-control-sm"
              @keydown.enter="runSearch" />
            <button class="btn btn-outline-light" @click="runSearch">
              {{ i18n.search }}
            </button>
          </div>
          <button v-else class="btn btn-outline-light" @click="runSearch">
            {{ i18n.search }}
          </button>
        </div>
      </div>
      <div v-if="hasFacets" class="row d-flex mb-2">
        <div v-for="facet in facetList" :key="facet.key" class="col-4">
          <DocumentFacet
            :values="facet.values"
            :filter="facet.filter"
            :value="facet.value"
            @select="setFilter(facet.filter.key, $event)" />
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import DocumentFacet from './document-facet.vue'
import DocumentFilter from './document-filter.vue'

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
    directory: {
      type: Object,
      default: null
    },
    showSearchFeed: {
      type: Boolean,
      default: false
    },
    filters: {
      type: Array,
      default: () => []
    }
  },
  emits: ['search', 'clearsearch'],
  data() {
    return {
      search: this.searcher?.term || '',
      filterValues: this.searcher?.filters || new Map()
    }
  },
  computed: {
    i18n() {
      return this.$root.config.i18n
    },
    searching() {
      return this.searcher && !this.searcher.done
    },
    hasFilters() {
      return !!this.filters && this.filters.length > 0
    },
    hasFacets() {
      return !!(
        this.searcher &&
        this.searcher.response &&
        this.searcher.response.facets
      )
    },
    facetList() {
      const facets = []
      for (const field in this.searcher.response.facets.fields) {
        const facetValues = this.searcher.response.facets.fields[field]
        if (facetValues.length === 0) {
          continue
        }
        const filter = this.filters.filter((f) => f.key === field)[0]
        if (filter === undefined) {
          continue
        }
        facets.push({
          key: filter.key,
          filter,
          values: facetValues,
          value: this.filterValues.get(filter.key) || ''
        })
      }
      return facets
    },
    pageCount() {
      if (this.searcher !== null) {
        return this.searcher.response.meta.total_count
      }
      return 0
    },
    pageCountFormatted() {
      return new Intl.NumberFormat(document.documentElement.lang, {
        style: 'decimal'
      }).format(this.pageCount)
    },
    resultCount() {
      if (this.searcher !== null) {
        return this.searcher.docCount
      }
      return 0
    },
    rssUrl() {
      if (this.searcher) {
        return this.searcher.url + '&format=rss'
      }
      return ''
    }
  },
  methods: {
    clear() {
      this.search = ''
      this.$emit('clearsearch')
    },
    runSearch() {
      this.$emit('search', {
        term: this.search,
        filters: this.filterValues
      })
    },
    setFilter(key, event) {
      this.updateFilter({ key, value: event })
      this.runSearch()
    },
    updateFilter({ key, value }) {
      this.filerValues = new Map(this.filterValues.set(key, value))
    }
  }
}
</script>

<style lang="scss"></style>
