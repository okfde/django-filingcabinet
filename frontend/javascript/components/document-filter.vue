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
          v-model="value"
          class="form-control"
          @change="updateFilter"
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
  </div>
</template>

<script>
const DEFAULT_LANG = 'en'

export default {
  name: 'DocumentFilter',
  props: {
    filter: {
      type: Object,
      required: true
    },
    // eslint-disable-next-line vue/require-prop-types
    initialValue: {
      default: ''
    }
  },
  data () {
    return {
      value: this.initialValue
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
    updateFilter () {
      this.$emit('change', {key: this.filter.key, value: this.value})
    }
  }
}
</script>