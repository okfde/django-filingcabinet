/*
  Adapted from: https://github.com/mozilla/pdf.js/blob/master/web/pdf_link_service.js

 * Copyright 2015 Mozilla Foundation
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */


class PDFLinkService {
  /**
   * @param {PDFLinkServiceOptions} options
   */
  constructor({
    externalLinkTarget = null,
    externalLinkRel = null,
    externalLinkEnabled = true,
    ignoreDestinationZoom = false,
  } = {}) {
    this.externalLinkTarget = externalLinkTarget;
    this.externalLinkRel = externalLinkRel;
    this.externalLinkEnabled = externalLinkEnabled;
    this._ignoreDestinationZoom = ignoreDestinationZoom;

    this.baseUrl = null;
    this.pdfDocument = null;
    this.pdfViewer = null;
    this.pdfHistory = null;

    this._pagesRefCache = null;
  }

  setDocument(pdfDocument, baseUrl = null) {
    this.baseUrl = baseUrl;
    this.pdfDocument = pdfDocument;
    this._pagesRefCache = Object.create(null);
  }

  setViewer(pdfViewer) {
    this.pdfViewer = pdfViewer;
  }

  setHistory(pdfHistory) {
    this.pdfHistory = pdfHistory;
  }

  /**
   * @type {number}
   */
  get pagesCount() {
    return this.pdfDocument ? this.pdfDocument.numPages : 0;
  }

  /**
   * @type {number}
   */
  get page() {
    return this.pdfViewer.currentPageNumber;
  }

  /**
   * @param {number} value
   */
  set page(value) {
    this.pdfViewer.currentPageNumber = value;
  }

  /**
   * @type {number}
   */
  get rotation() {
    return this.pdfViewer.pagesRotation;
  }

  /**
   * @param {number} value
   */
  set rotation(value) {
    this.pdfViewer.pagesRotation = value;
  }

  /**
   * @param {string|Array} dest - The named, or explicit, PDF destination.
   */
  navigateTo(dest) {
    const goToDestination = ({ namedDest, explicitDest }) => {
      // Dest array looks like that: <page-ref> </XYZ|/FitXXX> <args..>
      const destRef = explicitDest[0];
      let pageNumber;

      if (destRef instanceof Object) {
        pageNumber = this._cachedPageNumber(destRef);

        if (pageNumber === null) {
          // Fetch the page reference if it's not yet available. This could
          // only occur during loading, before all pages have been resolved.
          this.pdfDocument
            .getPageIndex(destRef)
            .then(pageIndex => {
              this.cachePageRef(pageIndex + 1, destRef);
              goToDestination({ namedDest, explicitDest });
            })
            .catch(() => {
              console.error(
                `PDFLinkService.navigateTo: "${destRef}" is not ` +
                  `a valid page reference, for dest="${dest}".`
              );
            });
          return;
        }
      } else if (Number.isInteger(destRef)) {
        pageNumber = destRef + 1;
      } else {
        console.error(
          `PDFLinkService.navigateTo: "${destRef}" is not ` +
            `a valid destination reference, for dest="${dest}".`
        );
        return;
      }
      if (!pageNumber || pageNumber < 1 || pageNumber > this.pagesCount) {
        console.error(
          `PDFLinkService.navigateTo: "${pageNumber}" is not ` +
            `a valid page number, for dest="${dest}".`
        );
        return;
      }

      if (this.pdfHistory) {
        // Update the browser history before scrolling the new destination into
        // view, to be able to accurately capture the current document position.
        this.pdfHistory.pushCurrentPosition();
        this.pdfHistory.push({ namedDest, explicitDest, pageNumber });
      }

      this.pdfViewer.scrollPageIntoView({
        pageNumber,
        destArray: explicitDest,
        ignoreDestinationZoom: this._ignoreDestinationZoom,
      });
    };

    new Promise((resolve) => {
      if (typeof dest === "string") {
        this.pdfDocument.getDestination(dest).then(destArray => {
          resolve({
            namedDest: dest,
            explicitDest: destArray,
          });
        });
        return;
      }
      resolve({
        namedDest: "",
        explicitDest: dest,
      });
    }).then(data => {
      if (!Array.isArray(data.explicitDest)) {
        console.error(
          `PDFLinkService.navigateTo: "${data.explicitDest}" is` +
            ` not a valid destination array, for dest="${dest}".`
        );
        return;
      }
      goToDestination(data);
    });
  }

  /**
   * @param {string|Array} dest - The PDF destination object.
   * @returns {string} The hyperlink to the PDF object.
   */
  getDestinationHash(dest) {
    if (typeof dest === "string") {
      return this.getAnchorUrl("#" + escape(dest));
    }
    if (Array.isArray(dest)) {
      const str = JSON.stringify(dest);
      return this.getAnchorUrl("#" + escape(str));
    }
    return this.getAnchorUrl("");
  }

  /**
   * Prefix the full url on anchor links to make sure that links are resolved
   * relative to the current URL instead of the one defined in <base href>.
   * @param {string} anchor The anchor hash, including the #.
   * @returns {string} The hyperlink to the PDF object.
   */
  getAnchorUrl(anchor) {
    return (this.baseUrl || "") + anchor;
  }

  /**
   * @param {string} hash
   */
  setHash() {
    /* Currently not implemented by FC */
  }

  /**
   * @param {string} action
   */
  executeNamedAction() {
  /* Currently not implemented by FC */
  }

  /**
   * @param {number} pageNum - page number.
   * @param {Object} pageRef - reference to the page.
   */
  cachePageRef(pageNum, pageRef) {
    if (!pageRef) {
      return;
    }
    const refStr =
      pageRef.gen === 0 ? `${pageRef.num}R` : `${pageRef.num}R${pageRef.gen}`;
    this._pagesRefCache[refStr] = pageNum;
  }

  _cachedPageNumber(pageRef) {
    const refStr =
      pageRef.gen === 0 ? `${pageRef.num}R` : `${pageRef.num}R${pageRef.gen}`;
    return (this._pagesRefCache && this._pagesRefCache[refStr]) || null;
  }

  /**
   * @param {number} pageNumber
   */
  isPageVisible(pageNumber) {
    return this.pdfViewer.isPageVisible(pageNumber);
  }
}

// function isValidExplicitDestination(dest) {
//   if (!Array.isArray(dest)) {
//     return false;
//   }
//   const destLength = dest.length;
//   if (destLength < 2) {
//     return false;
//   }
//   const page = dest[0];
//   if (
//     !(
//       typeof page === "object" &&
//       Number.isInteger(page.num) &&
//       Number.isInteger(page.gen)
//     ) &&
//     !(Number.isInteger(page) && page >= 0)
//   ) {
//     return false;
//   }
//   const zoom = dest[1];
//   if (!(typeof zoom === "object" && typeof zoom.name === "string")) {
//     return false;
//   }
//   let allowNull = true;
//   switch (zoom.name) {
//     case "XYZ":
//       if (destLength !== 5) {
//         return false;
//       }
//       break;
//     case "Fit":
//     case "FitB":
//       return destLength === 2;
//     case "FitH":
//     case "FitBH":
//     case "FitV":
//     case "FitBV":
//       if (destLength !== 3) {
//         return false;
//       }
//       break;
//     case "FitR":
//       if (destLength !== 6) {
//         return false;
//       }
//       allowNull = false;
//       break;
//     default:
//       return false;
//   }
//   for (let i = 2; i < destLength; i++) {
//     const param = dest[i];
//     if (!(typeof param === "number" || (allowNull && param === null))) {
//       return false;
//     }
//   }
//   return true;
// }

class FilingcabinetLinkService extends PDFLinkService {}

export {
  FilingcabinetLinkService
}
