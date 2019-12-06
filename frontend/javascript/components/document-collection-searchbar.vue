<template>
  <div class="row py-1 bg-dark text-white document-searchbar">
    <div class="col-auto mr-auto">
      <div v-if="searching" class="spinner-border spinner-border-sm" role="status">
        <span class="sr-only">{{ i18n.searching }}</span>
      </div>
      <small v-if="searcher">
        {{ i18n.found_in }} {{ resultCount }} {{ i18n.document }}
      </small>
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
  </div>
</template>

<script>
export default {
  name: 'document-collection-searchbar',
  props: ['searcher'],
  data () {
    return {
      search: ''
    }
  },
  computed: {
    i18n () {
      return this.$root.config.i18n
    },
    searching () {
      return this.searcher && !this.searcher.done
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
      this.$emit('search', this.search)
    }
  }
}
</script>

<style lang="scss">

</style>
