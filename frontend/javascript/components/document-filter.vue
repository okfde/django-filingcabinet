<template>
  <div class="mb-3 row">
    <label :for="filter.id" class="col-sm-3 col-md-2 col-form-label">
      {{ label }}
    </label>
    <template v-if="filter.type == 'choice'">
      <div class="col-sm-9 col-md-10">
        <select
          :id="filter.id"
          :value="value"
          class="form-control"
          @keyup.enter="submit"
          @input="updateFilter($event.target.value)">
          <option value="">---</option>
          <option
            v-for="opt in filter.choices"
            :key="opt.value"
            :value="opt.value">
            {{ opt.label ? opt.label[lang] : opt.value }}
          </option>
        </select>
      </div>
    </template>
    <template v-if="filter.type == 'daterange'">
      <div class="col-sm-9 col-md-10">
        <document-date-range-filter
          :value="value || {}"
          :filter="filter"
          @submit="submit"
          @input="updateFilter" />
      </div>
    </template>
  </div>
</template>

<script>
import DocumentDateRangeFilter from './document-daterangefilter.vue'

const DEFAULT_LANG = 'en'

export default {
  name: 'DocumentFilter',
  components: {
    DocumentDateRangeFilter
  },
  props: {
    filter: {
      type: Object,
      required: true
    },
    // eslint-disable-next-line vue/require-prop-types
    value: {
      default: ''
    }
  },
  emits: ['input', 'submit'],
  computed: {
    lang() {
      return document.documentElement.lang
    },
    label() {
      return this.filter.label[this.lang] || this.filter.label[DEFAULT_LANG]
    }
  },
  methods: {
    submit() {
      this.$emit('submit')
    },
    updateFilter(value) {
      this.$emit('input', { key: this.filter.key, value })
    }
  }
}
</script>
