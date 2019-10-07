<template>
  <div class="annotation-container" :style="style">
    <page-annotation
      v-for="annotation in annotations"
      :key="annotation.id"
      :annotation="annotation"
      :current-annotation="currentAnnotation"
      @currentannotation="$emit('currentannotation', $event)"
    />
  </div>
</template>


<script>

import PageAnnotation from './document-annotation.vue'

export default {
  name: 'document-page-annotations',
  props: ['page', 'annotations', 'currentAnnotation'],
  components: {
    PageAnnotation
  },
  computed: {
    style () {
      return {
        height: this.page.normalSize + 'px'
      }
    }
  }
}
</script>

<style lang="scss" scoped>
.annotation-container {
  overflow-y: auto;
}
</style>
