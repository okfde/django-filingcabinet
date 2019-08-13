import Vue from 'vue'

import Document from './components/document.vue'

Vue.config.productionTip = false

function createDocumentViewer (selector, props) {
  /* eslint-disable no-new */
  let DocumentClass = Vue.extend(Document)
  props.preview = true
  let instance = new DocumentClass({
    propsData: props
  })
  instance.$mount(selector)
}


Array.from(document.querySelectorAll('[data-fcdocument]')).forEach(el => {
  createDocumentViewer(el, {
    documentUrl: el.dataset.fcdocument
  })
})

const exp = {
  createDocumentViewer
}

export default exp
