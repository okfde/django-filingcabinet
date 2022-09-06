import { createApp } from 'vue'

import DocumentCollection from './components/document-collection.vue'
import DocumentViewer from './components/document-viewer.vue'

function createDocumentViewer(selector, props) {
  createApp(DocumentViewer, {
    preview: true,
    ...props
  }).mount(selector)
}

function createDocumentCollectionViewer(selector, props) {
  createApp(DocumentCollection, props).mount(selector)
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
