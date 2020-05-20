<template>
  <div>
    <a
      :href="documentUrl"
      class="preview-doc"
      target="_blank"
      @click="navigate"
    >
      <img
        v-if="imageUrl"
        v-show="imageLoaded"
        ref="image"
        :src="imageUrl"
        alt=""
        class="img-fluid page-image"
        @load="onImageLoad"
      >
      <div
        v-if="!imageLoaded"
        class="spinner-grow"
        role="status"
      >
        <span class="sr-only">Loading...</span>
      </div>
      <p
        class="text-truncate"
        :title="document.title"
      >
        <template v-if="highlight">
          {{ i18n.page }} {{ page }}
        </template>
        <template v-else>
          {{ document.title }}
        </template>
      </p>
    </a>
    <div
      v-if="highlight"
      class="query-highlight mb-5"
    >
      <span v-html="highlight" />
    </div>
  </div>
</template>

<script>

export default {
  name: 'DocumentPreview',
  props: {
    document: {
      type: Object,
      required: true
    },
    page: {
      type: Number,
      default: 1
    },
    highlight: {
      type: String,
      default: null
    },
    image: {
      type: String,
      default: null
    }
  },
  data () {
    return {
      imageLoaded: false
    }
  },
  computed: {
    i18n () {
      return this.$root.config.i18n
    },
    imageUrl () {
      return decodeURI(this.image || this.document.cover_image)
        .replace(/\{size\}/, 'small')
    },
    documentUrl () {
      let url = this.document.site_url
      if (this.page) {
        url += `?page=${this.page}`
      }
      return url
    }
  },
  beforeDestroy () {
    if (this.document.cover_image && !this.imageLoaded) {
      // Cancel image download on destroy
      this.$refs.image.setAttribute('src', "")
    }
  },
  methods: {
    onImageLoad () {
      this.imageLoaded = true
    },
    navigate (e) {
      e.preventDefault()
      this.$emit('navigate', {
        document: this.document,
        page: this.page
      })
    }
  }
}
</script>

<style lang="scss" scoped>
.preview-doc {
  display: block;
  text-align: center;
}
.preview-doc:hover {
  text-decoration: none;
}
.preview-doc .page-image {
  border: 1px solid #aaa;
  margin: 0 auto;
}
.preview-doc p, .preview-doc p:hover {
  text-align: center;
  color: #fff;
  text-decoration: none;
}

.query-highlight {
  background-color: #fff;
  padding: 5px;
  font-size: 0.7rem;
}

</style>

<style lang="scss">
/* Do not scope as it's v-html-injected */
.query-highlight {
  em {
    background-color: yellow;
    color: #333;
  }
}
</style>