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
      await this.downloadAndWriteFile(document, dirHandle)
      this.documentsDownloaded += 1
      this.progressCallback(this.documentsDownloaded / this.documentCount * 100)  
    }
    for (const directory of collection.directories) {
      const subDirHandle = await this.getSubDirectoryHandle(dirHandle, directory)
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

  async getSubDirectoryHandle(dirHandle, directory) {
    const dirName = directory.name.replace(/[\\/:*?"<>|]/gi, '_')
    try {
      // If directory exists, return handle
      return await dirHandle.getDirectoryHandle(dirName, { create: false });
    } catch (e) {
      if (e.name !== "NotFoundError") {
        console.warn("Error getting subdirectory handle", directory)
        throw e
      }
    }
    // If directory does not exist, try creating it
    return await dirHandle.getDirectoryHandle(dirName, { create: true });
  }

  async downloadAndWriteFile(document, dirHandle) {
    const filename = document.url.split('/').pop().replace(/\.pdf$/, `-${document.id}.pdf`);
    try {
      // if file exists, skip
      await dirHandle.getFileHandle(filename, { create: false });
      return
    } catch (e) {
      if (e.name !== "NotFoundError") {
        throw e
      }
    }
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
