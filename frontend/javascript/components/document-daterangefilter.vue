<template>
  <div class="input-group">
    <input
      :value="min"
      type="date"
      class="form-control"
      @input="updateValue($event.target.value)"
    >
    <div class="input-group-prepend">
      <span class="input-group-text">-</span>
    </div>
  
    <input
      :value="max"
      type="date"
      class="form-control"
      @input="updateValue(undefined, $event.target.value)"
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
  computed: {
    min () {
      return this.value[`${this.filter.key}_after`]
    },
    max () {
      return this.value[`${this.filter.key}_before`]
    }
  },
  methods: {
    updateValue(min, max) {
      min = min || this.min
      max = max || this.max
      this.$emit('input', {
        [`${this.filter.key}_after`]: min,
        [`${this.filter.key}_before`]: max,
      })
    }
  }
}
</script>