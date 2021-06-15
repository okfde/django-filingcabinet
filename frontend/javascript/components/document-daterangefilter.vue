<template>
  <div class="input-group">
    <input
      v-model="min"
      type="date"
      class="form-control"
      @input="updateValue"
    >
    <div class="input-group-prepend">
      <span class="input-group-text">-</span>
    </div>
  
    <input
      v-model="max"
      type="date"
      class="form-control"
      @input="updateValue"
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
      min: this.value[`${this.filter.key}_after`],
      max: this.value[`${this.filter.key}_before`]
    }
  },
  methods: {
    updateValue() {
      this.$emit('input', {
        [`${this.filter.key}_after`]: this.min,
        [`${this.filter.key}_before`]: this.max,
      })
    }
  }
}
</script>