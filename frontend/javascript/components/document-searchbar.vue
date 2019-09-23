<template>
  <div class="row py-1 bg-secondary text-white document-searchbar">
    <div class="col-auto">
      <div class="input-group input-group-sm">
      </div>
    </div>
    <div class="col-auto ml-auto">
      <div v-if="searching" class="spinner-border spinner-border-sm" role="status">
        <span class="sr-only">Searching...</span>
      </div>
      <small>
        Found on {{ searcher.pageCount }} pages
      </small>
      <div class="btn-group" role="group">
        <button type="button"
          class="btn btn-sm btn-light"
          @click="toggleShowText"
        >
          <i class="fa fa-chevron-left"></i>
        </button>
        <button type="button"
          class="btn btn-sm btn-light"
          @click="toggleShowText"
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
  props: ['searcher'],
  data () {
    return {
    }
  },
  computed: {
    searching () {
      return !this.searcher.done
    }
  },
  methods: {
    toggleShowText () {
      console.log('test')
      this.$emit('updatepreferences', {showText: !this.preferences.showText})
    },
    clear () {
      this.$emit('clearsearch')
    }
  }
}
</script>

<style lang="scss">

</style>
