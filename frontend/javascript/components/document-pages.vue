<template>
  <div class="document-pages">
    <RecycleScroller
      class="scroller"
      :items="pages"
      page-mode
      key-field="number"
      sizeField="normalSize"
      v-slot="{ item }"
    >
      <document-page
        :key="item.number"
        :page="item"
        :show-text="showText"
      />
    </RecycleScroller>
  </div>
</template>

<script>

import 'intersection-observer'

import { RecycleScroller, DynamicScroller, DynamicScrollerItem } from 'vue-virtual-scroller'

import DocumentPage from './document-page.vue'

export default {
  name: 'document-pages',
  props: ['document', 'preferences'],
  components: {
    RecycleScroller, DynamicScroller, DynamicScrollerItem,
    DocumentPage
  },
  computed: {
    showText () {
      return this.preferences.showText
    },
    pages () {
      return this.document.pages
    }
  }
}
</script>

<style lang="scss">
@import '~vue-virtual-scroller/dist/vue-virtual-scroller.css';

.document-pages {
  padding: 1rem 0;
}
</style>
