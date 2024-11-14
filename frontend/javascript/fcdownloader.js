class Downloader {
  constructor(collectionUrl, progressCallback) {
    this.collectionUrl = collectionUrl;
    this.documentCount = null
    this.documentsDownloaded = 0
    this.progressCallback = progressCallback
    this.finished = false
  }

  async start() {
    let dirHandle
    try {
      dirHandle = await this.getDirectoryHandle()
    } catch (err) {
      console.error('Error getting save handle:', err);
      return false
    }
    console.log("Got dirHandle", dirHandle)
    await this.downloadDirectory(dirHandle, null);
    return true
  }

  async downloadDirectory(dirHandle, directory) {
    const collection = await this.getCollectionData(directory)
    if (directory === null) {
      this.documentCount = collection.document_count
    }
    const documents = await this.getDocumentsData(collection.documents_uri, directory)
    for (const document of documents) {
      console.log("Downloading file", document)
      await this.downloadAndAddFile(document, dirHandle)
    }
    for (const directory of collection.directories) {
      const dirName = directory.name
      const subDirHandle = await dirHandle.getDirectoryHandle(dirName, { create: true });
      await this.downloadDirectory(subDirHandle, directory)
    }
  }

  _addDirectoryParamToUrl(url, directory) {
    url = new URL(
      url,
      window.location.origin
    )
    const params = new URLSearchParams(url.search)
    if (directory) {
      params.append('directory', directory.id)
    }
    url.search = params
    return url
  }

  async getCollectionData(directory = null) {
    const url = this._addDirectoryParamToUrl(this.collectionUrl, directory)
    const response = await fetch(url);
    return await response.json();
  }

  async getDocumentsData(documentUrl, directory = null) {
    let url = this._addDirectoryParamToUrl(documentUrl, directory)
    const documents = []
    while (url) {
      const response = await fetch(url);
      const data = await response.json();
      documents.push(...data.objects.map((obj) => ({
        id: obj.id,
        url: obj.file_url
      })));
      url = data.next;
    }
    return documents
  }

  async getDirectoryHandle () {
    const pickerOpts = {
      mode: 'readwrite',
      startIn: 'downloads'
    };

    return await window.showDirectoryPicker(pickerOpts);
  }

  async downloadAndAddFile(document, dirHandle) {
    const filename = document.url.split('/').pop().replace(/\.pdf$/, `-${document.id}.pdf`);
    const fileHandle = await dirHandle.getFileHandle(filename, { create: true });
    const response = await fetch(document.url);
    const writable = await fileHandle.createWritable();
    const reader = response.body.getReader();
    while (true) {
      const {value, done} = await reader.read();
      if (done) break;
      await writable.write(value);
    }
    await writable.close();
    this.documentsDownloaded += 1
    this.progressCallback(this.documentsDownloaded / this.documentCount * 100)
  }
}


const startDownload = async (collectionUrl, downloadError, downloadButton, downloadProgress) => {
  const downloader = new Downloader(collectionUrl, (progress) => {
    downloadProgress.setAttribute('aria-valuenow', progress)
    const bar = downloadProgress.querySelector('.progress-bar')
    bar.style.width = `${progress}%`
    bar.classList.remove('progress-bar-animated')
  });
  downloadButton.disabled = true;
  downloadProgress.hidden = false
  downloadButton.textContent = downloadButton.dataset.downloading;
  let result
  try {
    result = await downloader.start();
  } catch (err) {
    downloadError.textContent = err.message;
    downloadError.hidden = false;
    return
  }
  if (result) {
    downloadButton.textContent = downloadButton.dataset.downloaded;
  } else {
    downloadButton.disabled = false;
  }
}

document.addEventListener('DOMContentLoaded', () => {
    const downloadSection = document.querySelector('[data-fcdownload]')
    const downloadButton = downloadSection?.querySelector('button');
    const downloadProgress = downloadSection?.querySelector('.progress');
    const downloadError = downloadSection.querySelector('.alert')
    if (downloadButton === null) {
        return;
    }
    if ('showDirectoryPicker' in window) {
        downloadButton.addEventListener('click', () => {
          const collectionUrl = downloadSection.dataset.fcdownload
          startDownload(collectionUrl, downloadError, downloadButton, downloadProgress);
        });
    } else {
        downloadButton.disabled = true;
        downloadError.hidden = false;
    }
});
