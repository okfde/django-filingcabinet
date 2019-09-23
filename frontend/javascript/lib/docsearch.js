import Worker from './docsearch.worker.js';

const worker = new Worker();


function addDocuments(documents) {
  worker.postMessage({
    type: 'add-documents',
    documents: documents
  });
}


function dispatch (responder) {
  var listener = function (event) {
    if (event.data.type === 'matches') {
      if (event.data.results === null) {
        responder.markDone()
        worker.removeEventListener('message', listener)
      } else {
        responder.addResults(event.data.results)
      }
    }
  }
  return listener
}

function searchDocuments (term) {
  let responder = {
    resultCb: null,
    doneCb: null,
    results: [],
    pageCount: 0,
    pages: {},
    done: false,
    doneCalled: false,
    addResults (results) {
      this.results = [
        ...this.results,
        ...results
      ]
      results.forEach((r) => {
        if (this.pages[r.number] === undefined) {
          this.pageCount += 1
          this.pages[r.number] = true
        }
      })
      if (this.resultCb) {
        this.resultCb(results)
      }
    },
    markDone () {
      this.done = true
      if (this.doneCb && !this.doneCalled) {
        this.doneCalled = true
        this.doneCb()
      }
    },
    result (f) {
      this.resultCb = f
      this.results.forEach(f)
      return this
    },
    done (f) {
      this.doneCb = f
      if (this.done && !this.doneCalled) {
        this.doneCalled = true
        this.doneCb()
      }
      return this
    },
    start () {
      worker.postMessage({
        type: 'query',
        query: term
      });
    }
  }

  worker.addEventListener("message", dispatch(responder));

  return responder
}


export default {
  addDocuments,
  searchDocuments
}