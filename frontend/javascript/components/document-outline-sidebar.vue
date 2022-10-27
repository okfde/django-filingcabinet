<template>
  <div class="outline-wrapper" :style="{ height: height }">
    <div ref="outline" class="document-outline" v-html="outlineHTML" />
  </div>
</template>

<script>
const TOC_RE = /^(\s*)- \[([^\]]+)\]\(#page-(\d+)\)\s*$/;

function escapeHTML(s) {
  return s
    .replace(/&/g, "&amp;")
    .replace(/"/g, "&quot;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

export default {
  name: "DocumentOutlineSidebar",
  props: ["outline", "height"],
  computed: {
    outlineHTML() {
      /*
      Converts nested markdown list with links to HTML
      Here be dragons
      */
      let html = ["<ul>"];
      let depth = 0;
      let openLi = false;
      this.outline.split(/\r?\n/).forEach((line) => {
        const match = TOC_RE.exec(line);
        if (match === null) {
          return;
        }
        const d = match[1].length / 2;
        if (d > depth) {
          for (let i = depth; i < d; i += 1) {
            html.push("<ul>");
          }
          openLi = false;
        } else if (d < depth) {
          for (let i = depth; i > d; i -= 1) {
            html.push("</li></ul>");
          }
          openLi = true;
        } else {
          if (openLi) {
            html.push("</li>");
          }
          html.push("<li>");
        }
        if (d != depth) {
          depth = d;
          if (openLi) {
            html.push("</li><li>");
          } else {
            html.push("<li>");
          }
        }
        html.push(`<a href="#page-${match[3]}">${escapeHTML(match[2])}</a>`);
      });
      html.push("</li></ul>");
      return html.join("");
    },
  },
  mounted() {
    /* Instead of:
    - generating lots of vue components for the toc with event listeners
    - listening on all links
    this listens on the parent, catches link clicks and navigates.
    Pretty dumb, but works for now.
    */
    this.$refs.outline.addEventListener("click", this.outlineClick);
  },
  beforeDestroy() {
    this.$refs.outline.removeEventListener("click", this.outlineClick);
  },
  methods: {
    outlineClick(e) {
      e.preventDefault();
      e.stopPropagation();
      if (e.target.nodeName !== "A") {
        return;
      }
      this.navigate(parseInt(e.target.attributes.href.value.split("-")[1], 10));
    },
    navigate(number) {
      this.$emit("navigate", {
        number,
        source: "outline",
      });
    },
  },
};
</script>

<style lang="scss" scoped>
.outline-wrapper {
  overflow: auto;
}
</style>

<style lang="scss">
.document-outline {
  li ul {
    padding-left: 0.5rem;
  }
  ul {
    color: #fff;
  }
  a,
  a:hover,
  a:visited {
    color: #fff;
  }
}
</style>
