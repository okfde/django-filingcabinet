<template>
  <div class="row py-2 bg-dark document-toolbar">
    <div class="col-auto">
      <div class="input-group input-group-sm">
        <input type="text" class="page-number-input form-control bg-light form-control-sm"
          v-model="page"
          @keypress="onlyAllowNumbers"
          @keydown.enter="navigate"
        >
        <div class="input-group-append">
          <span class="input-group-text">/ {{ document.num_pages }}</span>
        </div>
      </div>
    </div>
    <div class="col-auto ml-auto">
      <div class="input-group input-group-sm">
        <input type="text" class="search-input form-control form-control-sm" :value="search"
          placeholder="not working"
          @keydown.enter="runSearch"
        >
        <div class="input-group-append">
          <button class="btn btn-outline-light">Search</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'document-toolbar',
  props: ['document', 'currentPage'],
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
    onlyAllowNumbers (e) {
      if (e.which < 48 || e.which > 57 && e.which !== 13) {
        e.preventDefault()
      }
    },
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
    }
  }
}
</script>

<style lang="scss">
.document-toolbar {
  position: sticky;
  top: 0;
  z-index: 30;
}

.page-number-input {
  width: 70px !important;
}
</style>
