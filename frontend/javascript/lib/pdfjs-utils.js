/*
  From: https://github.com/mozilla/pdf.js/blob/master/web/pdf_link_service.js
*/

class SimpleLinkService {
  constructor() {
    // 2 = new window
    this.externalLinkTarget = 2;
    this.externalLinkRel = "noopener nofollow noreferrer";
    this.externalLinkEnabled = true;
    this._ignoreDestinationZoom = false;
  }

  /**
   * @type {number}
   */
  get pagesCount() {
    return 0;
  }

  /**
   * @type {number}
   */
  get page() {
    return 0;
  }

  /**
   * @param {number} value
   */
  set page(value) {}

  /**
   * @type {number}
   */
  get rotation() {
    return 0;
  }

  /**
   * @param {number} value
   */
  set rotation(value) {}

  /**
   * @param dest - The PDF destination object.
   */
  navigateTo() {}

  /**
   * @param dest - The PDF destination object.
   * @returns {string} The hyperlink to the PDF object.
   */
  getDestinationHash() {
    return "#";
  }

  /**
   * @param hash - The PDF parameters/hash.
   * @returns {string} The hyperlink to the PDF object.
   */
  getAnchorUrl() {
    return "#";
  }

  /**
   * @param {string} hash
   */
  setHash() {}

  /**
   * @param {string} action
   */
  executeNamedAction() {}

  /**
   * @param {number} pageNum - page number.
   * @param {Object} pageRef - reference to the page.
   */
  cachePageRef() {}

  /**
   * @param {number} pageNumber
   */
  isPageVisible() {
    return true;
  }
}

export {
  SimpleLinkService
}