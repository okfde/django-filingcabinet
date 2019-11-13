<template>
  <div class="document-preview-grid">
    <div class="row bg-secondary pt-3">
      <div v-for="document in documents" class="col-sm-4 col-md-3" :key="document.id">
        <document-preview
          :document="document"
          @navigate="navigate"
        />
      </div>
    </div>
  </div>
</template>

<script>

import 'intersection-observer'

import DocumentPreview from './document-preview.vue'

export default {
  name: 'document-preview-grid',
  props: ['documents'],
  components: {
    DocumentPreview,
  },
  computed: {
    i18n () {
      return this.config.i18n
    },
  },
  methods: {
    navigate (doc) {
      this.$emit('navigate', doc)
    }
  }
}
</script>

<style lang="scss">
.document-preview-grid {

}
</style>
