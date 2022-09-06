<template>
  <div class="annotation-container" :style="style">
    <div v-if="!showAnnotationForm && canAnnotate" class="text-end mb-2">
      <button
        class="btn btn-sm btn-light text-body-secondary"
        @click="activateForm(false)">
        {{ i18n.addAnnotation }}
      </button>
    </div>
    <div v-if="showAnnotationForm">
      <div class="mb-3">
        <label for="">{{ i18n.title }}</label>
        <input
          v-model="title"
          type="text"
          class="form-control form-control-sm" />
      </div>
      <div class="mb-3">
        <label>{{ i18n.description }}</label>
        <textarea
          v-model="description"
          class="form-control form-control-sm"></textarea>
      </div>
      <div class="text-end">
        <button
          class="btn btn-sm btn-light"
          @click.prevent="$emit('activateannotationform', null)">
          {{ i18n.cancel }}
        </button>
        <button
          class="btn btn-sm btn-secondary"
          :disabled="!formValid"
          @click.prevent="postAnnotation">
          {{ i18n.addAnnotation }}
        </button>
      </div>
    </div>
    <div v-if="!showAnnotationForm">
      <page-annotation
        v-for="annotation in annotations"
        :key="annotation.id"
        :annotation="annotation"
        :current-annotation="currentAnnotation"
        @currentannotation="$emit('currentannotation', $event)"
        @deleteannotation="$emit('deleteannotation', $event)" />
    </div>
  </div>
</template>

<script>
import PageAnnotation from './document-annotation.vue'

export default {
  name: 'DocumentPageAnnotations',
  components: {
    PageAnnotation
  },
  props: [
    'page',
    'annotations',
    'currentAnnotation',
    'canAnnotate',
    'activeAnnotationForm'
  ],
  data() {
    return {
      title: '',
      description: ''
    }
  },
  computed: {
    i18n() {
      return this.$root.config.i18n
    },
    style() {
      return {
        height: this.page.normalSize - 15 + 'px'
      }
    },
    formValid() {
      return (
        this.title.length > 0 &&
        this.title.length < 255 &&
        this.description.length < 1024
      )
    },
    showAnnotationForm() {
      if (this.activeAnnotationForm === null) {
        return false
      }
      return this.activeAnnotationForm.number === this.page.number
    }
  },
  methods: {
    postAnnotation() {
      this.activateForm(true)
      this.$emit('activateannotationform', null)
      this.title = ''
      this.description = ''
    },
    activateForm(ready) {
      this.$emit('activateannotationform', {
        number: this.page.number,
        title: this.title,
        description: this.description,
        ready
      })
    }
  }
}
</script>

<style lang="scss" scoped>
.annotation-container {
  overflow-y: auto;
  margin-bottom: 15px;
}
</style>
