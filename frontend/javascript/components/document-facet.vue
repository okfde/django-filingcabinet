<template>
  <div class="document-facet bg-secondary py-2 px-3">
    <h5>
      {{ label }}
      <button
        v-if="value"
        class="btn btn-sm btn-link text-white"
        @click="$emit('select', '')">
        <span class="visually-hidden">{{ i18n.clear }}</span>
        <i class="fa fa-close" />
      </button>
    </h5>
    <ul class="document-facet-list">
      <li v-for="facet in facetList" :key="facet.value">
        <a
          v-if="!facet.selected"
          href="#"
          @click.prevent="selectFacetValue(facet.value)">
          {{ facet.label }} ({{ facet.count }} {{ i18n.pages }})
        </a>
        <span v-else>
          {{ facet.label }} ({{ facet.count }} {{ i18n.pages }})
        </span>
      </li>
    </ul>
  </div>
</template>

<script>
const DEFAULT_LANG = 'en'

const equal = (a, b) => {
  // Really simple edge-case ignoring equality
  if (typeof a === 'object') {
    for (const k of Object.keys(a)) {
      if (a[k] !== b[k]) {
        return false
      }
    }
    return true
  }
  return a === b
}

export default {
  name: 'DocumentFacet',
  props: {
    filter: {
      type: Object,
      required: true
    },
    values: {
      type: Array,
      default: () => []
    },
    // eslint-disable-next-line vue/require-prop-types
    value: {
      default: ''
    }
  },
  emits: ['select'],
  computed: {
    i18n() {
      return this.$root.config.i18n
    },
    lang() {
      return document.documentElement.lang
    },
    label() {
      return this.filter.label[this.lang] || this.filter.label[DEFAULT_LANG]
    },
    filterChoiceLabelMap() {
      const labelMap = new Map()
      if (this.filter.choices) {
        this.filter.choices.forEach((choice) => {
          labelMap.set(
            choice.value,
            (choice.label && choice.label[this.lang]) || choice.value
          )
        })
      }
      return labelMap
    },
    facetList() {
      return this.values.map(([facetValue, facetCount]) => {
        return {
          selected: this.checkSelected(facetValue),
          value: facetValue,
          count: facetCount,
          label: this.getFacetLabel(facetValue)
        }
      })
    }
  },
  methods: {
    checkSelected(facetValue) {
      const val = this.getFacetValue(facetValue)
      return equal(val, this.value)
    },
    getFacetLabel(value) {
      if (this.filter.choices) {
        return this.filterChoiceLabelMap.get(value) || value
      }
      if (this.filter.facet_config?.type === 'date_histogram') {
        const date = new Date(value)
        return date.getFullYear()
      }
      return value
    },
    getFacetValue(value) {
      if (this.filter.facet_config?.type === 'date_histogram') {
        const date = new Date(value)
        const before = `${date.getFullYear()}-12-31`
        return {
          [`${this.filter.key}_after`]: date.toISOString().split('T')[0],
          [`${this.filter.key}_before`]: before
        }
      } else {
        return value
      }
    },
    selectFacetValue(value) {
      this.$emit('select', this.getFacetValue(value))
    }
  }
}
</script>

<style scoped>
.document-facet-list {
  max-height: 8rem;
  overflow-y: scroll;
  list-style-type: none;
  padding-left: 0;
  margin-bottom: 0;
}

.document-facet-list li a {
  color: inherit;
  text-decoration: underline;
}
</style>
