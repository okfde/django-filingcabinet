<template>
  <div class="document">
    <div v-if="showPreview">
      Preview
    </div>
    <div v-else-if="document" class="document">
      <div class="row">
        <div class="col-md-3">
          <document-preview-sidebar
            :document="document"
            @navigate="navigate"
          ></document-preview-sidebar>
        </div>
        <div class="col-md-9" ref="documentContainer">
          <document-pages :document="document"></document-pages>
        </div>
      </div>
    </div>
  </div>
</template>

<script>

import DocumentPages from './document-pages.vue'
import DocumentPreviewSidebar from './document-preview-sidebar.vue'

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
    DocumentPages,
    DocumentPreviewSidebar
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
        let ratio = p.height / p.width
        p.normalSize = Math.ceil(700 * ratio) + 60
        p.smallSize = Math.ceil(180 * ratio) + 40
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
  },
  methods: {
    navigate (number) {
      let offset = this.document.pages.filter((p) => p.number < number)
        .map((p) => p.normalSize)
        .reduce((a, v) => a + v, 0)
      let top = this.$refs.documentContainer.offsetTop
      window.scrollTo(0, top + offset)
    }
  }
}
</script>

<style lang="scss">

</style>
