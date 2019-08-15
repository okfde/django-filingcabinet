<template>
  <div class="document-preview-pages">
    <RecycleScroller
      class="scroller"
      :items="pages"
      page-mode
      key-field="number"
      sizeField="smallSize"
      :emitUpdate="true"
      v-slot="{ item }"
    >
      <document-preview-page
        :key="item.number"
        :page="item"
        @navigate="navigate"
      />
    </RecycleScroller>
  </div>
</template>

<script>

import 'intersection-observer'

import { RecycleScroller, DynamicScroller, DynamicScrollerItem } from 'vue-virtual-scroller'

import DocumentPreviewPage from './document-preview-page.vue'

export default {
  name: 'document-preview-sidebar',
  props: ['document'],
  components: {
    RecycleScroller, DynamicScroller, DynamicScrollerItem,
    DocumentPreviewPage
  },
  computed: {
    i18n () {
      return this.config.i18n
    },
    pages () {
      return this.document.pages
    }
  },
  methods: {
    navigate (number) {
      this.$emit('navigate', {
        number,
        source: 'sidebar'
      })
    }
  }
}
</script>

<style lang="scss">
@import '~vue-virtual-scroller/dist/vue-virtual-scroller.css';

.document-preview-pages {
  height: 100vh;
  overflow: auto;
  top: 50px;
  position: sticky;
}
</style>
