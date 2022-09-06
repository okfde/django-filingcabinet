<template>
  <a
    :href="pageAnchor"
    class="d-flex search-preview-page text-white"
    :class="{ 'bg-dark': isCurrent }"
    @click.prevent="navigate">
    <img
      :src="imageUrl"
      alt=""
      class="flex-shrink-0 img-fluid"
      style="height: 90px" />
    <div class="flex-grow-1 ms-2">
      <h6>
        {{ i18n.page }} {{ page.number }} -
        <template v-if="matches.count === 1">
          {{ i18n.one_match }}
        </template>
        <template v-else> {{ matches.count }} {{ i18n.matches }} </template>
      </h6>
      <div class="query-highlight">
        <template
          v-for="result in matches.results"
          :key="result.query_highlight">
          <span v-html="result.query_highlight" />
        </template>
      </div>
    </div>
  </a>
</template>

<script>
export default {
  name: 'DocumentSearchPreview',
  props: ['page', 'matches', 'currentPage'],
  computed: {
    i18n() {
      return this.$root.config.i18n
    },
    imageUrl() {
      return this.page.image_url.replace(/\{size\}/, 'small')
    },
    pageAnchor() {
      return `#page-${this.page.number}`
    },
    isCurrent() {
      return this.page.number === this.currentPage
    }
  },
  methods: {
    navigate() {
      this.$emit('navigate', this.page.number)
    }
  }
}
</script>

<style lang="scss" scoped>
.search-preview-page {
  cursor: pointer;
  text-decoration: none;
  height: 106px;
  padding: 8px 5px;
  margin-bottom: 9px;
}
.query-highlight {
  font-size: 0.7rem;
  max-height: 48px;
  overflow: hidden;
  span {
    text-overflow: ellipsis;
  }
}
</style>

<style lang="scss">
/* Do not scope as it's v-html-injected */
.query-highlight {
  em {
    background-color: yellow;
    color: #333;
  }
}
</style>
