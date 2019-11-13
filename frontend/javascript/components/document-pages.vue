<template>
  <div class="document-pages">
    <RecycleScroller
      class="scroller"
      :items="pages"
      page-mode
      key-field="number"
      sizeField="normalSize"
      :emitUpdate="true"
      :prerender="3"
      @update="updateCurrentPage"
      v-slot="{ item }"
    >
      <document-page
        :key="item.number"
        :page="item"
        :annotations="annotations[item.number] || []"
        :show-text="showText"
        :show-annotations="showAnnotations"
        :current-annotation="currentAnnotation"
        :annotation-form="activeAnnotationForm"
        :width="width"
        @currentannotation="$emit('currentannotation', $event)"
        @activateannotationform="$emit('activateannotationform', $event)"
      />
    </RecycleScroller>
  </div>
</template>

<script>

import 'intersection-observer'

import { RecycleScroller } from 'vue-virtual-scroller'

import DocumentPage from './document-page.vue'

export default {
  name: 'document-pages',
  props: [
    'document', 'pages', 'preferences', 'annotations', 'currentAnnotation',
    'activeAnnotationForm', 'width'
  ],
  components: {
    RecycleScroller,
    DocumentPage
  },
  computed: {
    showText () {
      return this.preferences.showText
    },
    showAnnotations () {
      return this.preferences.showAnnotations
    },
  },
  mounted () {
    this.initialNav = false
  },
  updated () {
    if (!this.initialNav || !this.document.loaded) {
      if (this.document.loaded) {
        this.initialNav = true
      }
      this.$emit('initialized')
    }
  },
  methods: {
    updateCurrentPage (startIndex, endIndex) {
      this.$emit('currentpage', {start: startIndex, end: endIndex})
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
