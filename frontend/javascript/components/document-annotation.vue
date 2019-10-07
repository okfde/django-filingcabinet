<template>
  <div class="annotation" :class="{'current': isCurrent}">
    <h6>{{ annotation.title }}</h6>
    <p>
      {{ annotation.description }}
    </p>
  </div>
</template>

<script>

export default {
  name: 'document-page-annotation',
  props: ['annotation', 'currentAnnotation'],
  data () {
    return {
      
    }
  },
  computed: {
    isCurrent () {
      return this.annotation.id === this.currentAnnotation
    },
  },
}
</script>

<style lang="scss" scoped>
.annotation {
  background-color: #fff;
  padding: 5px;
}
.current {

}
</style>
