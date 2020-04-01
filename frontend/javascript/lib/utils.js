function getData (url = '', headers = {}) {
  headers = headers || {}
  return window.fetch(url, {
    method: 'GET',
    cache: 'no-cache',
    credentials: 'same-origin',
    headers: {
      'Accept': 'application/json',
      'X-Requested-With': 'XMLHttpRequest',
      ...headers
    }
  }).then(response => response.json())
}

function postData (url = '', data = {}, csrfToken, method = 'POST') {
  return window.fetch(url, {
    method: method,
    cache: 'no-cache',
    credentials: 'same-origin',
    headers: {
      'Content-Type': 'application/json',
      'X-Requested-With': 'XMLHttpRequest',
      'X-CSRFToken': csrfToken
    },
    body: JSON.stringify(data)
  }).then(response => {
    if (method !== 'DELETE') {
      return response.json()
    }
  })
}

function triggerDownload (blobUrl, filename) {
  const a = document.createElement("a");
  if (!a.click) {
    throw new Error('a.click() is not supported.');
  }
  a.href = blobUrl;
  a.target = "_blank";
  // Use a.download if available. This increases the likelihood that
  // the file is downloaded instead of opened by another PDF plugin.
  if ("download" in a) {
    a.download = filename;
  }
  // <a> must be in the document for IE and recent Firefox versions,
  // otherwise .click() is ignored.
  (document.body || document.documentElement).appendChild(a);
  a.click();
  a.remove();
}


export {
  getData,
  postData,
  triggerDownload
}
