<template>
  <div>
    <div ref="toolbar" class="collection-toolbar">
      <div class="row py-2 bg-dark">
        <div class="col-4 col-md-3">
          <div v-if="document" class="btn-group" role="group">
            <button
              type="button"
              class="btn btn-sm btn-secondary"
              @click="clearDocument"
            >
              {{ i18n.backToCollection }}
            </button>
          </div>
        </div>
        <div class="col-auto order-md-3 ms-auto">
          <span class="text-muted d-inline-block text-truncate">
            <template v-if="document">
              {{ collection.title }}
            </template>
            <template v-else>
              {{ collection.document_count }} {{ i18n.documents }}
            </template>
          </span>
        </div>
        <div class="col-10 col-md order-md-2 text-center">
          <h4 class="text-white text-truncate mb-0">
            <template v-if="document">
              {{ document.title }}
            </template>
            <template v-else>
              {{ collection.title }}
            </template>
          </h4>
        </div>

        <div
          v-if="!document && allowToggleSearch"
          class="col-auto order-md-4 ms-auto"
        >
          <button
            v-if="!showSearch"
            type="button"
            class="ms-2 btn btn-sm btn-secondary"
            @click="enableSearch"
          >
            <i class="fa fa-search" />
          </button>
          <button
            v-else
            type="button"
            class="ms-2 btn btn-sm btn-secondary"
            @click="clearSearch"
          >
            <i class="fa fa-close" />
          </button>
        </div>
      </div>
      <document-collection-searchbar
        v-if="showSearch && !document"
        :searcher="searcher"
        :directory="currentDirectory"
        :show-search-feed="showSearchFeed"
        :filters="settings.filters"
        @clearsearch="clearSearch"
        @search="search"
      />
    </div>
    <div v-if="document" class="collection-document">
      <div class="row">
        <div class="col-12 px-0">
          <document
            :document-url="document.resource_uri"
            :document-preview="document"
            :page="documentPage"
            :config="config"
            :defaults="docDefaults"
          />
        </div>
      </div>
    </div>
    <div v-if="!document && searcher">
      <template v-if="searcher.term">
        <document-collection-search-results
          v-for="result in searcher.results"
          :key="result.document.id"
          :document="result.document"
          :pages="result.pages"
          @navigate="navigate"
        />
      </template>
      <template v-else>
        <div class="row bg-secondary">
          <div class="col px-0">
            <document-preview-grid
              :documents="searcher.documents"
              @navigate="navigate"
            />
          </div>
        </div>
      </template>
      <div v-if="searcher.done && searcher.response.meta.next">
        <div class="row bg-secondary justify-content-center">
          <div class="col-auto px-0 pb-5">
            <button
              class="btn btn-secondary my-3"
              @click="loadMoreSearchResults"
            >
              {{ i18n.loadMore }}
            </button>
          </div>
        </div>
      </div>
    </div>
    <div v-show="!document && !searcher" class="document-collection">
      <div class="row bg-secondary">
        <div class="col px-0">
          <div class="list-group list-group-flush">
            <button
              v-if="currentDirectory != null"
              type="button"
              class="list-group-item list-group-item-action list-group-item-dark text-center"
              @click="selectDirectory()"
            >
              <i class="fa fa-arrow-left float-start" />
              {{ currentDirectory.name }}
            </button>
            <button
              v-for="directory in directories"
              :key="directory.id"
              type="button"
              class="list-group-item list-group-item-action list-group-item-secondary"
              @click="selectDirectory(directory)"
            >
              {{ directory.name }}
            </button>
          </div>
          <document-preview-grid
            :documents="documents"
            @navigate="navigate"
            @loadmore="loadMoreDocuments"
          />
          <div
            v-if="shouldPaginate && canPaginate"
            class="col-auto px-0 pb-5 text-center"
          >
            <button
              class="btn btn-secondary my-3"
              @click.prevent="() => loadMoreDocuments()"
            >
              {{ i18n.loadMore }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import Vue from "vue";

import DocumentPreviewGrid from "./document-preview-grid.vue";
import DocumentCollectionSearchbar from "./document-collection-searchbar.vue";
import DocumentCollectionSearchResults from "./document-collection-searchresults.vue";
import Document from "./document.vue";

import { getData } from "../lib/utils.js";

const DOCUMENTS_API_LIMIT = 50;
const MAX_SCROLL_DOCS = DOCUMENTS_API_LIMIT * 100;

function getIDFromURL(s) {
  const parts = s.split("/");
  return parseInt(parts[parts.length - 2], 10);
}

export default {
  name: "DocumentCollection",
  components: {
    DocumentPreviewGrid,
    Document,
    DocumentCollectionSearchbar,
    DocumentCollectionSearchResults,
  },
  props: {
    documentCollection: {
      type: Object,
      default: () => ({
        documents: [],
        directories: [],
      }),
    },
    config: {
      type: Object,
      default: () => ({}),
    },
  },
  data() {
    let documents = [];
    let directories = [];
    let collection = {
      documents,
      directories,
    };
    if (this.documentCollection) {
      collection = this.documentCollection;
    }
    let shouldPaginate = collection.document_directory_count > MAX_SCROLL_DOCS;
    let settings = collection.settings || {};
    let preferences = settings.preferences || {};
    return {
      document: null,
      collection: collection,
      settings: settings,
      showSearch: preferences.showSearch ?? false,
      allowToggleSearch: preferences.allowToggleSearch ?? true,
      showSearchFeed: preferences.showSearchFeed ?? false,
      searcher: null,
      documentPage: 1,
      currentDirectory: null,
      directoryStack: [],
      shouldPaginate,
      documents: this.makeDocuments(collection, shouldPaginate),
      directories: collection.directories,
      documentOffsets: this.makeOffsets(collection, shouldPaginate),
      lastOffset: 0,
      documentsUri: collection.documents_uri || null,
    };
  },
  computed: {
    i18n() {
      return this.config.i18n;
    },
    collectionIndex() {
      const documents = this.documents;
      const collectionIndex = {};
      documents.forEach((d, i) => {
        if (d !== null) {
          collectionIndex[d.id] = i;
        }
      });
      return collectionIndex;
    },
    docDefaults() {
      return {
        maxHeight: "90vh",
      };
    },
    collectionAuth() {
      if (!this.collection.listed && this.collection.uid) {
        return `uid=${this.collection.uid}`;
      }
      return "";
    },
    canPaginate() {
      return (
        this.collection.document_directory_count >
        this.lastOffset + DOCUMENTS_API_LIMIT
      );
    },
  },
  created() {
    if (!this.documentCollection.id && this.documentCollection.resource_uri) {
      this.getCollectionData();
    }
  },
  mounted() {
    if (
      this.documents.length >= 0 &&
      this.documents[0] === null &&
      this.documentsUri
    ) {
      this.loadMoreDocuments(0);
    }
  },
  methods: {
    getCollectionData() {
      let url = [this.documentCollection.resource_uri];
      if (url[0].indexOf("?") === -1) {
        url.push(`?${this.collectionAuth}`);
      } else {
        url.push(`&${this.collectionAuth}`);
      }
      this.documents = [];
      this.directories = [];
      url.push(
        `&directory=${this.currentDirectory ? this.currentDirectory.id : ""}`
      );
      getData(url.join("")).then((docCollection) => {
        this.collection = docCollection;
        this.documentsUri = docCollection.documents_uri;
        this.documentOffsets = this.makeOffsets(docCollection);
        this.documents = this.makeDocuments(docCollection);
        this.directories = docCollection.directories;
        if (!this.settings) {
          this.settings = docCollection.settings;
        }
      });
    },
    makeOffsets(collection) {
      let offsetSteps = collection.documents.length / DOCUMENTS_API_LIMIT;
      let documentOffsets = new Set();
      for (var i = 0; i < offsetSteps; i += 1) {
        documentOffsets.add(i);
      }
      return documentOffsets;
    },
    makeDocuments(collection, shouldPaginate = true) {
      if (this.shouldPaginate || shouldPaginate) {
        return collection.documents;
      }
      let colDocs = collection.documents || [];
      return [
        ...colDocs,
        ...new Array(collection.document_directory_count - colDocs.length).fill(
          null
        ),
      ];
    },
    loadMoreDocuments(offset) {
      if (offset === undefined) {
        offset = this.lastOffset + DOCUMENTS_API_LIMIT;
      }
      offset = offset - (offset % DOCUMENTS_API_LIMIT);
      if (this.shouldPaginate) {
        if (offset === this.lastOffset) {
          return;
        }
        this.documents = [];
        this.lastOffset = offset;
        Vue.nextTick(() => this.goTop());
        return this.getDocuments(offset);
      }
      let offsetStep = offset / DOCUMENTS_API_LIMIT;
      if (!this.documentOffsets.has(offsetStep)) {
        this.documentOffsets.add(offsetStep);
        this.getDocuments(offset);
      }
    },
    getDocuments(offset) {
      if (this.abortController) {
        this.documentOffsets.delete(this.lastOffset);
        this.abortController.abort();
      }
      this.abortController = new AbortController();
      this.lastOffset = offset;
      let url = [this.documentsUri];
      if (url[0].indexOf("?") === -1) {
        url.push("?");
      }
      url.push(`&${this.collectionAuth}`);
      url.push(
        `&directory=${this.currentDirectory ? this.currentDirectory.id : "-"}`
      );
      url.push(`&offset=${offset}&limit=${DOCUMENTS_API_LIMIT}`);
      this.documentOffset = offset + DOCUMENTS_API_LIMIT;
      getData(url.join(""), {}, this.abortController.signal).then((result) => {
        if (!result) {
          return;
        }
        this.abortController = null;
        if (this.shouldPaginate) {
          this.documents = result.objects;
        } else {
          this.documents = [
            ...this.documents.slice(0, offset),
            ...result.objects,
            ...this.documents.slice(offset + result.objects.length),
          ];
        }
      });
    },
    navigate({ document, page }) {
      this.document = document;
      this.documentPage = page || 1;
      this.goTop();
    },
    clearDocument() {
      this.document = null;
      this.goTop();
    },
    goTop() {
      window.scrollTo(0, this.$refs.toolbar.offsetTop);
    },
    enableSearch() {
      this.showSearch = true;
      this.document = null;
    },
    clearSearch() {
      this.searcher = null;
      if (this.allowToggleSearch) {
        this.showSearch = false;
      }
    },
    search({ term, filters }) {
      this.document = null;
      console.log("searching for term", term, "with filters", filters);
      let hasSearch = false;
      if (term) {
        hasSearch = true;
      }
      for (let value of filters.values()) {
        if (value) {
          hasSearch = true;
        }
      }
      if (!hasSearch) {
        this.searcher = null;
        return;
      }
      this.searcher = {
        term: term,
        filters: filters,
        url: this.getSearchUrl({ term, filters }),
        done: false,
        results: [],
        documents: [],
      };
      getData(this.searcher.url).then((response) =>
        this.documentsReceived(response)
      );
    },
    getSearchUrl({ term, filters }) {
      let params = [this.collectionAuth];
      let baseUrl = this.collection.pages_uri;
      if (term) {
        params.push(`q=${encodeURIComponent(term)}`);
      } else {
        params.push("number=1");
      }
      if (this.currentDirectory) {
        params.push(`directory=${this.currentDirectory.id}`);
      }
      for (let [key, value] of filters.entries()) {
        if (value) {
          if (typeof value === "object") {
            for (let urlKey in value) {
              if (value[urlKey]) {
                params.push(`${urlKey}=${encodeURIComponent(value[urlKey])}`);
              }
            }
          } else {
            params.push(`${key}=${encodeURIComponent(value)}`);
          }
        }
      }
      return `${baseUrl}${baseUrl.includes("?") ? "&" : "?"}${params.join(
        "&"
      )}`;
    },
    documentsReceived(response) {
      this.searcher.response = response;
      let missingDocs = [];
      response.objects.forEach((p) => {
        const docId = getIDFromURL(p.document);
        let document = this.collection.documents[this.collectionIndex[docId]];
        if (document === undefined) {
          missingDocs.push(docId);
        }
      });
      if (missingDocs.length > 0) {
        let docsUrl = `${this.collection.documents_uri}${
          this.collection.documents_uri.includes("?") ? "&" : "?"
        }ids=${missingDocs.join(",")}`;
        getData(docsUrl).then((docsResponse) => {
          this.setSearchResults(response.objects, docsResponse.objects);
        });
      } else {
        this.setSearchResults(response.objects, []);
      }
    },
    setSearchResults(results, resultDocuments) {
      const docsWithPages = [];
      let docs = {};
      let docCount = 0;
      let docIndex = {};
      let searcherDocs = [];
      resultDocuments.forEach((d, i) => (docIndex[d.id] = i));
      results.forEach((p) => {
        const docId = getIDFromURL(p.document);
        let docResult = {
          image: p.image.replace(/\{size\}/, "small"),
          number: p.number,
          query_highlight: p.query_highlight,
        };
        if (docs[p.document] === undefined) {
          let document = this.collection.documents[this.collectionIndex[docId]];
          if (document === undefined) {
            document = resultDocuments[docIndex[docId]];
          }
          searcherDocs.push(document);
          docs[p.document] = docCount;
          docCount += 1;
          docsWithPages.push({
            document: document,
            pages: [docResult],
          });
        } else {
          docsWithPages[docs[p.document]].pages.push(docResult);
        }
      });
      this.searcher.documents = searcherDocs;
      this.searcher.results = docsWithPages;
      Vue.set(this.searcher, "docCount", docCount);
      this.searcher.done = true;
    },
    loadMoreSearchResults() {
      this.searcher.done = false;
      getData(this.searcher.response.meta.next).then((response) =>
        this.documentsReceived(response)
      );
    },
    selectDirectory(directory) {
      if (directory) {
        this.directoryStack.push(directory);
      } else {
        this.directoryStack.pop();
      }
      this.currentDirectory =
        this.directoryStack[this.directoryStack.length - 1] || null;
      this.getCollectionData();
    },
  },
};
</script>

<style lang="scss"></style>
