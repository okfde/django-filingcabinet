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
        :can-annotate="canAnnotate"
        :supported-formats="supportedFormats"
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
  props: {
    document: {
      type: Object,
      required: true,
    },
    pages: {
      type: Array,
      required: true,
    },
    preferences: {
      type: Object,
      required: true,
    },
    annotations: {
      type: Object,
      required: true,
    },
    currentAnnotation: {
      type: Object,
      default: null,
    },
    activeAnnotationForm: {
      type: Object,
      default: null,
    },
    height: {
      type: String,
      default: null,
    },
    canAnnotate: {
      type: Boolean,
      default: false,
    },
    pdfDocument: {
      type: Object,
      default: null,
    },
  },
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
    supportedFormats () {
      if (this.document.properties && this.document.properties._format_webp) {
        return ["webp"]
      }
      return []
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
@import 'vue-virtual-scroller/dist/vue-virtual-scroller.css';

.scroller {
  height: 100%;
}

.document-pages {
  padding: 1rem 0;
}
</style>
