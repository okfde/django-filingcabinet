<template>
  <div class="annotation" :style="annotationStyle" :class="{'current': isCurrent}" @click="$emit('currentannotation', annotation.id)">
    <span class="visually-hidden">{{ annotation.title }}</span>
  </div>
</template>

<script>

export default {
  name: 'document-page-annotationoverlay',
  props: ['annotation', 'page', 'currentAnnotation'],
  data () {
    return {
      
    }
  },
  computed: {
    isCurrent () {
      return this.annotation.id === this.currentAnnotation
    },
    annotationStyle () {
      let bg = ''
      if (this.annotation.highlight) {
        bg = `url(${this.annotation.image})`
      }
      return {
        'background-image': bg,
        transform: 'translateY(-1px)',
        top: (this.annotation.top / this.page.height * 100) + '%',
        left: (this.annotation.left / this.page.width * 100) + '%',
        width: (this.annotation.width / this.page.width * 100) + '%',
        height: (this.annotation.height / this.page.height * 100) + '%',
      }
    }
  },
}
</script>

<style lang="scss" scoped>

.annotation {
  position: absolute;
  background-repeat: no-repeat;
  background-size: contain;
  cursor: help;

  &:hover, &.current{
    box-shadow: 0px 0px 5px 3px #FCED00;
  }
}
</style>
