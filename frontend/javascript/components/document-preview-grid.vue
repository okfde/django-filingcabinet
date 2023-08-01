<template>
  <div ref="documentGrid" class="document-preview-grid bg-secondary container">
    <RecycleScroller
      v-slot="{ item }"
      class="scroller"
      :page-mode="true"
      :items="documentRows"
      :item-size="itemSize"
      key-field="rowId"
      :emit-update="true"
      @update="showRow">
      <div v-if="item.loaded" class="row pt-3">
        <div
          v-for="document in item.documents"
          :key="document.id"
          class="col-md-4 col-lg-3">
          <document-preview :document="document" @navigate="navigate" />
        </div>
      </div>
    </RecycleScroller>
  </div>
</template>

<script>
import 'intersection-observer'

import { RecycleScroller } from 'vue-virtual-scroller'
import DocumentPreview from './document-preview.vue'

const BS_LG = 992
const BS_MD = 768
const DEFAULT_ASPECT_RATIO = Math.sqrt(2)
const TITLE_HEIGHT = 24 + 15 * 2 // + 2 * padding

export default {
  name: 'DocumentPreviewGrid',
  components: {
    DocumentPreview,
    RecycleScroller
  },
  props: {
    documents: {
      type: Array,
      required: true
    }
  },
  emits: ['loadmore', 'navigate'],
  data() {
    return {
      width: null
    }
  },
  computed: {
    i18n() {
      return this.$root.config.i18n
    },
    itemSize() {
      if (this.width === null) {
        return 282
      }
      return 180 * DEFAULT_ASPECT_RATIO + TITLE_HEIGHT
    },
    documentRows() {
      const rows = []
      for (let i = 0; i < this.documents.length; i += this.colCount) {
        const rowDocs = this.documents.slice(i, i + this.colCount)
        rows.push({
          rowId: `${this.documents[0].id}_${i}`,
          loaded: rowDocs.every((d) => d !== null),
          documents: rowDocs
        })
      }
      return rows
    },
    colCount() {
      return document.body.clientWidth >= BS_LG
        ? 4
        : document.body.clientWidth >= BS_MD
        ? 3
        : 1
    }
  },
  mounted() {
    this.width = this.$refs.documentGrid.getBoundingClientRect().width
  },
  methods: {
    navigate(docAndPage) {
      this.$emit('navigate', docAndPage)
    },
    showRow(startIndex, endIndex) {
      const currentDocs = this.documents.slice(
        startIndex * this.colCount,
        endIndex * this.colCount + this.colCount
      )
      if (currentDocs.some((d) => d === null)) {
        const firstNull = currentDocs
          .map((d, i) => [d, i])
          .filter((d) => d[0] === null)[0][1]
        this.$emit('loadmore', startIndex * this.colCount + firstNull)
      }
    }
  }
}
</script>

<style lang="scss">
@import 'vue-virtual-scroller/dist/vue-virtual-scroller.css';
</style>
