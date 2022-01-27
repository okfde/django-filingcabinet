<template>
  <div
    class="document-preview-pages"
    :style="{'height': height}"
  >
    <RecycleScroller
      v-slot="{ item }"
      class="scroller"
      :items="pages"
      key-field="number"
      size-field="smallSize"
      :emit-update="true"
    >
      <document-preview-page
        :key="item.number"
        :page="item"
        :image-formats="imageFormats"
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
  name: 'DocumentPreviewSidebar',
  components: {
    RecycleScroller,
    DocumentPreviewPage
  },
  props: {
    pages: {
      type: Array,
      required: true,
    },
    imageFormats: {
      type: Array,
      default: () => []
    },
    height: {
      type: String,
      required: true,
    }
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
