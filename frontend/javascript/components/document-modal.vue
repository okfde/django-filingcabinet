<template>
  <transition name="modal">
    <div class="modal-mask">
      <div class="modal-wrapper">
        <div class="modal-content">
          <div class="modal-header">
            <slot
              name="header"
              class="modal-title"
            />
            <button
              type="button"
              class="close"
              data-dismiss="modal"
              :aria-label="i18n.close"
              @click="$emit('close')"
            >
              <span aria-hidden="true">&times;</span>
            </button>
          </div>

          <div class="modal-body">
            <slot name="body">
              default body
            </slot>
          </div>
        </div>
      </div>
    </div>
  </transition>
</template>

<script>

export default {
  name: 'DocumentModal',
  computed: {
    i18n () {
      return this.$root.config.i18n
    }
  }
}
</script>

<style lang="scss" scoped>
.modal-mask {
  position: absolute;
  z-index: 9998;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: table;
  transition: opacity 0.3s ease;
}

.modal-wrapper {
  margin: 1rem auto;
  display: table-cell;
}

.modal-container {
  width: 300px;
  margin: 0px auto;
  padding: 20px 30px;
  transition: all 0.3s ease;
}

.modal-enter {
  opacity: 0;
}

.modal-leave-active {
  opacity: 0;
}

.modal-enter .modal-container,
.modal-leave-active .modal-container {
  -webkit-transform: scale(1.1);
  transform: scale(1.1);
}

</style>

