<template>
  <div class="form-group row">
    <label
      :for="filter.id"
      class="col-sm-2 col-form-label"
    >
      {{ label }}
    </label>
    <template v-if="filter.type == 'choice'">
      <div class="col-sm-10">
        <select
          :id="filter.id"
          :value="value"
          class="form-control"
          @input="updateFilter($event.target.value)"
        >
          <option value="">
            ---
          </option>
          <option
            v-for="opt in filter.choices"
            :key="opt.value"
            :value="opt.value"
          >
            {{ opt.label ? opt.label[lang] : opt.value }}
          </option>
        </select>
      </div>
    </template>
    <template v-if="filter.type == 'daterange'">
      <div class="col-sm-10">
        <document-date-range-filter
          :value="value || {}"
          :filter="filter"
          @input="updateFilter"
        />
      </div>
    </template>
  </div>
</template>

<script>
const DEFAULT_LANG = 'en'

import DocumentDateRangeFilter from './document-daterangefilter.vue'

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
  computed: {
    lang () {
      return document.documentElement.lang
    },
    label () {
      return this.filter.label[this.lang] || this.filter.label[DEFAULT_LANG]
    }
  },
  methods: {
    updateFilter (value) {
      this.$emit('input', {key: this.filter.key, value})
    }
  }
}
</script>