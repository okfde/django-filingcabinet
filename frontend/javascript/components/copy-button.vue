<script setup>
import { onMounted, useTemplateRef, inject } from 'vue'
import { Tooltip } from 'bootstrap'

const props = defineProps({
  copyText: {
    type: String,
    required: true
  }
})
const i18n = inject('i18n')

const button = useTemplateRef('button')

const showPopup = (text) => {
  const tooltip = Tooltip.getOrCreateInstance(button.value)
  tooltip.setContent({ '.tooltip-inner': text })

  setTimeout(() => {
    tooltip.hide()
    tooltip.setContent({
      '.tooltip-inner': button.value.dataset.bsOriginalTitle
    })
  }, 2000)
}

const copy = () => {
  navigator.clipboard.writeText(props.copyText).then(
    () => showPopup(i18n.copied),
    () => showPopup(i18n.copyFailed)
  )
}

onMounted(() => {
  Tooltip.getOrCreateInstance(button.value)
})
</script>

<template>
  <button class="btn btn-sm btn-secondary" ref="button" @click="copy">
    <slot />
  </button>
</template>
