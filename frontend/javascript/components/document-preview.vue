<template>
  <div>
    <a :href="documentUrl" @click="navigate" class="preview-doc" target="_blank">
      <img v-if="imageUrl" v-show="imageLoaded" ref="image" @load="onImageLoad" :src="imageUrl" alt="" class="img-fluid page-image"/>
      <div v-if="!imageLoaded" class="spinner-grow" role="status">
        <span class="sr-only">Loading...</span>
      </div>
      <p class="text-truncate">
        <template v-if="highlight">
          {{ i18n.page  }} {{ page }}
        </template>
        <template v-else>
          {{ document.title }}
        </template>
      </p>
    </a>
    <div class="query-highlight mb-5" v-if="highlight">
      <span v-html="highlight"></span>
    </div>
  </div>
</template>

<script>

export default {
  name: 'document-preview',
  props: {
    document: {
      type: Object,
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
  beforeDestroy () {
    if (this.document.cover_image && !this.imageLoaded) {
      // Cancel image download on destroy
      this.$refs.image.setAttribute('src', "")
    }
  },
  computed: {
    i18n () {
      return this.$root.config.i18n
    },
    imageUrl () {
      return this.image || this.document.cover_image
    },
    documentUrl () {
      let url = this.document.site_url
      if (this.page) {
        url += `?page=${this.page}`
      }
      return url
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
  font-size: 0.7rem;
  max-height: 48px;
  overflow: hidden;
  span {
    text-overflow: ellipsis;
  }
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