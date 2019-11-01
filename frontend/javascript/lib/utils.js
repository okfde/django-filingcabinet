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

export {
  getData,
  postData
}
