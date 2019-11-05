<template>
  <div class="document-preview-pages">
    <RecycleScroller
      class="scroller"
      :items="pages"
      page-mode
      key-field="number"
      :buffer="400"
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

import { RecycleScroller } from 'vue-virtual-scroller'

import DocumentPreviewPage from './document-preview-page.vue'

export default {
  name: 'document-preview-sidebar',
  props: ['pages'],
  components: {
    RecycleScroller,
    DocumentPreviewPage
  },
  computed: {
    i18n () {
      return this.config.i18n
    },
  },
  mounted () {
    this.initialNav = false
  },
  updated () {
    if (!this.initialNav) {
      this.initialNav = true
      this.$emit('navigatesidebar')
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
  padding: 0.5rem 0;
}
</style>
