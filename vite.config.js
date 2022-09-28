import { resolve } from 'path'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue2'

const outputDir = resolve(__dirname, 'build')

// https://vitejs.dev/config/
export default defineConfig({
  base: '/static/',
  resolve: {
    dedupe: ['vue', 'bootstrap', 'pdfjs-dist'],
    extensions: ['.mjs', '.js', '.ts', '.vue', '.json']
  },
  build: {
    manifest: true,
    emptyOutDir: true,
    outDir: outputDir,
    sourcemap: true,
    rollupOptions: {
      input: {
        entry: 'frontend/javascript/entry.js',
      },
      output: {
        sourcemap: true,
        entryFileNames: '[name].js',
        assetFileNames: (assetInfo) => {
          if (assetInfo.name.endsWith('.css')) {
            return 'css/[name][extname]'
          } else if (
            assetInfo.name.match(/(\.(woff2?|eot|ttf|otf)|font\.svg)(\?.*)?$/)
          ) {
            return 'fonts/[name][extname]'
          } else if (assetInfo.name.match(/\.(jpg|png|svg)$/)) {
            return 'img/[name][extname]'
          }

          console.log('assetInfo', assetInfo)
          return 'js/[name][extname]'
        }
      }
    }
  },
  plugins: [vue()]
})
