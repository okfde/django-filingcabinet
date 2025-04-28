<template>
  <div
    class="document-search-pages bg-secondary text-light"
    :style="{ height: height }">
    <RecycleScroller
      v-slot="{ item }"
      class="scroller"
      :items="pages"
      key-field="number"
      :item-size="116">
      <DocumentSearchPreview
        :key="item.number"
        :matches="item"
        :page="documentPages[item.number - 1]"
        :current-page="currentPage"
        @navigate="navigate(item)" />
    </RecycleScroller>
  </div>
</template>

<script>
import 'intersection-observer'

import { RecycleScroller } from 'vue-virtual-scroller'

import DocumentSearchPreview from './document-search-preview.vue'

export default {
  name: 'DocumentSearchSidebar',
  components: {
    DocumentSearchPreview,
    RecycleScroller
  },
  props: {
    documentPages: {
      type: Array,
      required: true
    },
    pages: {
      type: Array,
      required: true
    },
    currentPage: {
      type: Number,
      required: true
    },
    height: {
      type: String,
      required: true
    }
  },
  emits: ['navigate'],
  computed: {},
  methods: {
    navigate(item) {
      const searchIndex = this.pages.findIndex((i) => i === item)
      this.$emit('navigate', {
        number: item.number,
        source: 'search',
        searchIndex
      })
    }
  }
}
</script>

<style lang="scss">
.document-search-pages {
  padding: 0.5rem 0;
  width: 100%;
}
</style>
