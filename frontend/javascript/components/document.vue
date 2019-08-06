<template>
  <div>
    <div v-if="document" class="pages">
      <RecycleScroller
        class="scroller"
        :items="pages"
        :item-size="32"
        page-mode
        key-field="number"
        :emitUpdate="true"
        @update="log"
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
  props: ['documentUrl'],
  components: {
    RecycleScroller, DynamicScroller, DynamicScrollerItem,
    DocumentPage
  },
  data () {
    return {
      document: null
    }
  },
  created () {
    getData(this.documentUrl).then((doc) => {
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
    }
  },
  methods: {
    log (args) {
      console.log(args)
    }
  }
}
</script>

<style lang="scss">
.scroller {
  height: 100%;
}
</style>
