const INTERVAL = 20

var documents = []
var searching = false

function queryDocuments (term, cb) {
  let results = []
  documents.forEach((d) => {
    let match = undefined
    while (true) {
      match = d.content.indexOf(term, match === undefined ? match : match + 1)
      if (match === -1) {
        break
      }
      results.push({
        type: 'match',
        query: term,
        number: d.number,
        position: match
      })
      if (results.length >= INTERVAL) {
        cb({
          type: 'matches',
          results: results
        })
        results = []
      }
    }
  })
  if (results.length > 0) {
    cb({
      type: 'matches',
      results: results
    })
  }
}

function searchDocuments (query) {
  if (query.length > 0) {
    queryDocuments(query, self.postMessage)
  }
  self.postMessage({
    type: 'matches',
    results: null,
  })
}


// Respond to message from parent thread
self.addEventListener('message', (event) => {
  if (event.data.type == 'add-documents') {
    documents = [
      ...documents,
      ...event.data.documents
    ]
  } else if (event.data.type == 'query') {
    searchDocuments(event.data.query)
  }
})
