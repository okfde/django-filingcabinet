<template>
  <div
    :id="'sidebar-annotation-' + annotation.id"
    class="annotation"
    :class="{ current: isCurrent, 'has-rect': hasRect }"
    @mouseover="activateAnnotation"
    @mouseout="deactivateAnnotation"
    @click="permanentlyActivateAnnotation"
  >
    <h6>
      {{ annotation.title }}
      <button
        v-if="annotation.can_delete"
        class="btn btn-sm btn-danger float-end delete-button"
        @click="deleteAnnotation"
      >
        <i class="fa fa-ban"></i>
      </button>
    </h6>
    <p v-if="annotation.description.length > 0">
      {{ annotation.description }}
    </p>
    <time
      :datetime="annotation.timestamp"
      class="d-block small text-end text-muted"
      >{{ annotationTime }}</time
    >
  </div>
</template>

<script>
export default {
  name: "document-page-annotation",
  props: ["annotation", "currentAnnotation"],
  data() {
    return {
      activated: false,
    };
  },
  computed: {
    isCurrent() {
      return this.annotation.id === this.currentAnnotation;
    },
    hasRect() {
      return !!this.annotation.left;
    },
    dtf() {
      return new Intl.DateTimeFormat("de", {
        year: "numeric",
        month: "numeric",
        day: "numeric",
        hour: "numeric",
        minute: "numeric",
      });
    },
    annotationTime() {
      const d = new Date(this.annotation.timestamp);
      return this.dtf.format(d);
    },
  },
  methods: {
    permanentlyActivateAnnotation() {
      this.activated = true;
      this.activateAnnotation();
    },
    activateAnnotation() {
      this.$emit("currentannotation", this.annotation.id);
    },
    deactivateAnnotation() {
      if (this.activated) {
        return;
      }
      this.$emit("currentannotation", null);
    },
    deleteAnnotation() {
      this.$emit("deleteannotation", this.annotation);
    },
  },
};
</script>

<style lang="scss" scoped>
.annotation {
  background-color: #fff;
  padding: 5px;
  cursor: pointer;
  margin-bottom: 0.5rem;

  p {
    margin-bottom: 0;
  }
  .delete-button {
    visibility: hidden;
  }
  &.current .delete-button {
    visibility: visible;
  }
}
.current.has-rect {
  outline: 1px solid #fced00;
}
</style>
