<template>
  <div class="row py-2 bg-dark">
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
            Search
          </button>
        </div>
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
      page: this.currentPage
    }
  },
  computed: {
    i18n () {
      return this.config.i18n
    },
  },
  methods: {
    navigate () {
      let number = parseInt(this.page, 10)
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
      console.log('test')
      this.$emit('updatepreferences', {showText: !this.preferences.showText})
    }
  }
}
</script>

<style lang="scss">
.page-number-input {
  width: 70px !important;
}
</style>
