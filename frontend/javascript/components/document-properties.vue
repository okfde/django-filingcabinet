<template>
  <div class="row py-2 document-properties">
    <div class="col-auto">
      <h5>
        {{ i18n.documentProperties }}
      </h5>
      <dl>
        <dt>{{ i18n.title }}</dt>
        <dd>{{ document.properties.title || document.title }}</dd>
        <template v-if="document.published_at">
          <dt>{{ i18n.publicationDate }}</dt>
          <dd>{{ publishedAt }}</dd>
        </template>
        <template v-if="document.properties.url">
          <dt>{{ i18n.url }}</dt>
          <dd>
            <a :href="document.properties.url" target="_blank" rel="noopener">
              {{ document.properties.url.slice(0, 20) }}&hellip;
            </a>
          </dd>
        </template>
        <template v-if="document.properties.author">
          <dt>{{ i18n.author }}</dt>
          <dd>{{ document.properties.author }}</dd>
        </template>
        <template v-if="document.properties.creator">
          <dt>{{ i18n.creator }}</dt>
          <dd>{{ document.properties.creator }}</dd>
        </template>
        <template v-if="document.properties.producer">
          <dt>{{ i18n.producer }}</dt>
          <dd>{{ document.properties.producer }}</dd>
        </template>
      </dl>
    </div>
  </div>
</template>

<script>
export default {
  name: 'DocumentProperties',
  props: {
    document: {
      type: Object,
      required: true
    }
  },
  computed: {
    i18n() {
      return this.$root.config.i18n
    },
    dtf() {
      return new Intl.DateTimeFormat(document.documentElement.lang, {
        year: 'numeric',
        month: 'numeric',
        day: 'numeric',
        hour: 'numeric',
        minute: 'numeric'
      })
    },
    publishedAt() {
      if (this.document.published_at) {
        return this.dtf.format(new Date(this.document.published_at))
      }
      return null
    }
  }
}
</script>

<style scoped>
.document-properties {
  background-color: #fff;
}
</style>
