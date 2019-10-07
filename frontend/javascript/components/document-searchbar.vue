<template>
  <div class="row py-1 bg-secondary text-white document-searchbar">
    <div class="col-auto">
      <div class="input-group input-group-sm">
      </div>
    </div>
    <div class="col-auto ml-auto">
      <div v-if="searching" class="spinner-border spinner-border-sm" role="status">
        <span class="sr-only">{{ i18n.searching }}</span>
      </div>
      <small>
        {{ i18n.found_on }} {{ pages.length }} {{ i18n.pages }}
      </small>
      <div class="btn-group" role="group">
        <button type="button"
          class="btn btn-sm btn-light"
          :disabled="!hasPrev"
          @click="prevSearchResult"
        >
          <i class="fa fa-chevron-left"></i>
        </button>
        <button type="button"
          class="btn btn-sm btn-light"
          :disabled="!hasNext"
          @click="nextSearchResult"
        >
          <i class="fa fa-chevron-right"></i>
        </button>
      </div>
      <button type="button"
          class="btn btn-sm btn-light"
          @click="clear"
        >
          <i class="fa fa-close"></i>
        </button>
    </div>
  </div>
</template>

<script>
export default {
  name: 'document-searchbar',
  props: ['searcher', 'searchIndex', 'pages'],
  data () {
    return {
    }
  },
  computed: {
    i18n () {
      return this.$root.config.i18n
    },
    searching () {
      return !this.searcher.done
    },
    hasNext () {
      return this.pages.length > 0 && this.searchIndex < this.pages.length - 1
    },
    hasPrev () {
      return this.pages.length > 0 && this.searchIndex > 0
    }
  },
  methods: {
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
