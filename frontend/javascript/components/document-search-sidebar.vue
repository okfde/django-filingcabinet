<template>
  <div class="document-search-pages bg-secondary text-light">
    <RecycleScroller
      class="scroller"
      :items="pages"
      page-mode
      key-field="number"
      :item-size="116"
      v-slot="{ item }"
    >
      <document-search-preview
        :key="item.number"
        :matches="item"
        :page="document.pages[item.number - 1]"
        @navigate="navigate"
      />
    </RecycleScroller>
  </div>
</template>

<script>

import 'intersection-observer'

import { RecycleScroller } from 'vue-virtual-scroller'

import DocumentSearchPreview from './document-search-preview.vue'

export default {
  name: 'document-search-sidebar',
  props: ['document', 'pages'],
  components: {
    DocumentSearchPreview,
    RecycleScroller
  },
  computed: {
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

</style>
