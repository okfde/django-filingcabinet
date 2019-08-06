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

export {
  getData
}
