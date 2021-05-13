<template>
  <div class="document-facet bg-secondary py-2 px-3">
    <h5>
      {{ label }}
      <button
        v-if="value"
        class="btn btn-sm btn-link text-white"
        @click="$emit('select', '')"
      >
        <span class="sr-only">{{ i18n.clear }}</span>
        <i class="fa fa-close" />
      </button>
    </h5>
    <ul>
      <li
        v-for="facet in facetList"
        :key="facet.value"
      >
        <a
          v-if="!facet.selected"
          href="#"
          @click.prevent="$emit('select', facet.value)"
        >
          {{ facet.label }} ({{ facet.count }})
        </a>
        <span v-else>
          {{ facet.label }} ({{ facet.count }})
        </span>
      </li>
    </ul>
  </div>
</template>

<script>

const DEFAULT_LANG = 'en'

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
  computed: {
    i18n () {
      return this.$root.config.i18n
    },
    lang () {
      return document.documentElement.lang
    },
    label () {
      return this.filter.label[this.lang] || this.filter.label[DEFAULT_LANG]
    },
    filterChoiceLabelMap () {
      let labelMap = new Map()
      this.filter.choices.forEach((choice) => {
        labelMap.set(choice.value, (choice.label && choice.label[this.lang]) || choice.value)
      })
      return labelMap
    },
    facetList () {
      return this.values.map(([facetValue, facetCount]) => {
        return {
          selected: facetValue === this.value,
          value: facetValue,
          count: facetCount,
          label: this.filterChoiceLabelMap.get(facetValue) || facetValue
        }
      })
    }
  }
}
</script>

<style scoped>
.document-facet {
  max-height: 8rem;
  overflow-y: scroll;
}

.document-facet ul {
  list-style-type: none;
  padding-left: 0;
}

.document-facet ul li a {
  color: inherit;
  text-decoration: underline;
}
</style>