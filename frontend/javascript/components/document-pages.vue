<template>
  <div
    class="document-pages"
    :style="{'height': height}"
  >
    <RecycleScroller
      v-slot="{ item }"
      class="scroller"
      :items="pages"
      :page-mode="isPageMode"
      key-field="number"
      size-field="normalSize"
      :emit-update="true"
      :buffer="buffer"
      @update="updateCurrentPage"
    >
      <document-page
        :key="item.number"
        :page="item"
        :pdf-document="pdfDocument"
        :annotations="annotations[item.number] || []"
        :show-text="showText"
        :show-annotations="showAnnotations"
        :current-annotation="currentAnnotation"
        :annotation-form="activeAnnotationForm"
        :width="width"
        :can-annotate="canAnnotate"
        @currentannotation="$emit('currentannotation', $event)"
        @activateannotationform="$emit('activateannotationform', $event)"
        @deleteannotation="$emit('deleteannotation', $event)"
        @navigate="$emit('navigate', $event)"
      />
    </RecycleScroller>
  </div>
</template>

<script>

import 'intersection-observer'

import { RecycleScroller } from 'vue-virtual-scroller'

import DocumentPage from './document-page.vue'

export default {
  name: 'DocumentPages',
  components: {
    RecycleScroller,
    DocumentPage
  },
  props: [
    'document', 'pages', 'preferences', 'annotations', 'currentAnnotation',
    'activeAnnotationForm', 'width', 'height', 'canAnnotate', 'pdfDocument'
  ],
  computed: {
    showText () {
      return this.preferences.showText
    },
    showAnnotations () {
      return this.preferences.showAnnotations
    },
    isPageMode () {
      return !this.preferences.maxHeight
    },
    buffer () {
      if (this.height) {
        return Math.round(parseInt(this.height.replace('px', '')) * 0.7)
      }
      if (this.pages.length > 0) {
        return Math.round(this.pages[0].normalSize * 0.7)
      }
      return 200
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

.scroller {
  height: 100%;
}

.document-pages {
  padding: 1rem 0;
}
</style>
