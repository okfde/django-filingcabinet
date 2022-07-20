<template>
  <div class="input-group">
    <input
      :value="min"
      type="date"
      class="form-control"
      @input="updateMin($event.target.value)"
      @change="updateMin($event.target.value)"
    >
    <span class="input-group-text">-</span>
    <input
      :value="max"
      type="date"
      class="form-control"
      @input="updateMax($event.target.value)"
      @change="updateMax($event.target.value)"
    >
  </div>
</template>

<script>
export default {
  name: 'DocumentDateRangeFilter',
  props: {
    filter: {
      type: Object,
      required: true
    },
    value: {
      type: Object,
      required: true
    },
  },
  data () {
    return {
      currentMin: this.min,
      currentMax: this.max
    }
  },
  computed: {
    min () {
      return this.value[`${this.filter.key}_after`]
    },
    max () {
      return this.value[`${this.filter.key}_before`]
    }
  },
  methods: {
    updateMin (min) {
      this.currentMin = min
      this.updateValue()
    },
    updateMax (max) {
      this.currentMax = max
      this.updateValue()
    },
    updateValue() {
      this.$emit('input', {
        [`${this.filter.key}_after`]: this.currentMin,
        [`${this.filter.key}_before`]: this.currentMax,
      })
    }
  }
}
</script>
