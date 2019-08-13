<template>
  <div class="document">
    <div v-if="showPreview">
      
    </div>
    <div v-else-if="document" class="">
      <RecycleScroller
        class="scroller"
        :items="pages"
        page-mode
        key-field="number"
        sizeField="size"
        :emitUpdate="true"
        v-slot="{ item }"
      >
        <document-page
          :key="item.number"
          :page="item"
        />
      </RecycleScroller>
    </div>
  </div>
</template>

<script>

import 'intersection-observer'

import { RecycleScroller, DynamicScroller, DynamicScrollerItem } from 'vue-virtual-scroller'

import DocumentPage from './document-page.vue'

import {getData} from '../lib/utils.js'

export default {
  name: 'document',
  props: {
    documentUrl: {
      type: String
    },
    preview: {
      type: Boolean,
      default: true
    }
  },
  components: {
    RecycleScroller, DynamicScroller, DynamicScrollerItem,
    DocumentPage
  },
  data () {
    return {
      document: null,
      showPreview: false
    }
  },
  created () {
    getData(this.documentUrl).then((doc) => {
      doc.pages = doc.pages.map(p => {
        p.size = Math.ceil(700 / p.width * p.height)
        return p
      })
      this.document = doc
    })
  },
  computed: {
    i18n () {
      return this.config.i18n
    },
    pages () {
      if (this.document !== null) {
        return this.document.pages
      }
    },
    previewPages () {

    }
  }
}
</script>

<style lang="scss">
@import '~vue-virtual-scroller/dist/vue-virtual-scroller.css';

</style>
