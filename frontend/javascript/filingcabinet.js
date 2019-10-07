import Vue from 'vue'

import Document from './components/document.vue'
import DocumentCollection from './components/document-collection.vue'

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

function createDocumentCollectionViewer (selector, props) {
  /* eslint-disable no-new */
  let DocumentCollectionClass = Vue.extend(DocumentCollection)
  let instance = new DocumentCollectionClass({
    propsData: props
  })
  instance.$mount(selector)
}


Array.from(document.querySelectorAll('[data-fcdocument]')).forEach(el => {
  createDocumentViewer(el, {
    documentUrl: el.dataset.fcdocumenturl,
    documentPreview: JSON.parse(el.dataset.fcdocument),
    page: parseInt(el.dataset.fcpage, 10),
    config: JSON.parse(el.dataset.fcconfig)
  })
})

Array.from(document.querySelectorAll('[data-fcdocumentcollection]')).forEach(el => {
  createDocumentCollectionViewer(el, {
    documentCollectionUrl: el.dataset.fcdocumentcollectionurl,
    documentCollectionPreview: JSON.parse(el.dataset.fcdocumentcollection),
    config: JSON.parse(el.dataset.fcconfig)
  })
})

const exp = {
  createDocumentViewer
}

export default exp
