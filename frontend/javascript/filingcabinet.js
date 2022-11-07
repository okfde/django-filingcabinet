import Vue from 'vue'

import DocumentViewer from './components/document-viewer.vue'
import DocumentCollection from './components/document-collection.vue'

Vue.config.productionTip = false

function createDocumentViewer(selector, props) {
  /* eslint-disable no-new */
  const DocumentClass = Vue.extend(DocumentViewer)
  props.preview = true
  const instance = new DocumentClass({
    propsData: props
  })
  instance.$mount(selector)
}

function createDocumentCollectionViewer(selector, props) {
  /* eslint-disable no-new */
  const DocumentCollectionClass = Vue.extend(DocumentCollection)
  const instance = new DocumentCollectionClass({
    propsData: props
  })
  instance.$mount(selector)
}

Array.from(document.querySelectorAll('[data-fcdocument]')).forEach((el) => {
  createDocumentViewer(el, {
    documentUrl: el.dataset.fcdocumenturl,
    documentPreview: JSON.parse(el.dataset.fcdocument),
    page: parseInt(el.dataset.fcpage, 10),
    config: JSON.parse(el.dataset.fcconfig),
    defaults: JSON.parse(el.dataset.fcdefaults)
  })
})

Array.from(document.querySelectorAll('[data-fcdocumentcollection]')).forEach(
  (el) => {
    createDocumentCollectionViewer(el, {
      documentCollection: JSON.parse(el.dataset.fcdocumentcollection),
      config: JSON.parse(el.dataset.fcconfig)
    })
  }
)

const exp = {
  createDocumentViewer,
  createDocumentCollectionViewer
}

export default exp
