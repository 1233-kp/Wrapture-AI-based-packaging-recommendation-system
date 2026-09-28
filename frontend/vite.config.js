import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'
import { VitePWA } from 'vite-plugin-pwa'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
    VitePWA({
      // Auto-activates a new service worker as soon as one is available (no
      // "new version ready, click to reload" prompt to build) — returning
      // visitors get the fresh build on their next navigation instead of
      // staying pinned to whatever was cached at install time.
      registerType: 'autoUpdate',
      injectRegister: 'auto',
      manifest: {
        name: 'Wrapture',
        short_name: 'Wrapture',
        description:
          'Wrapture analyzes food commodity properties and recommends the best-fit packaging material, with explainable shelf-life and sustainability insights.',
        theme_color: '#0f172a',
        background_color: '#0f172a',
        display: 'standalone',
        start_url: '/',
        icons: [
          { src: '/pwa-icons/icon-192.png', sizes: '192x192', type: 'image/png' },
          { src: '/pwa-icons/icon-512.png', sizes: '512x512', type: 'image/png' },
        ],
      },
      workbox: {
        // Only ever precaches this build's own static output (JS/CSS/HTML/
        // images/fonts) — no origin outside this deployment is listed here,
        // so the Render backend (VITE_API_BASE_URL) and Supabase
        // (auth + REST) are never touched by the service worker. Deliberately
        // no `runtimeCaching` entries for either: adding one would be the only
        // way to make the SW intercept those requests, so leaving it out is
        // what keeps API/auth calls live-network-only, not an oversight.
        globPatterns: ['**/*.{js,css,html,ico,png,svg,woff,woff2}'],
        // SPA fallback for the precached shell — separate mechanism from
        // vercel.json's rewrite (that one handles direct/online navigation
        // via Vercel's routing; this one handles the app shell rendering
        // instantly from cache on a flaky/offline connection).
        navigateFallback: '/index.html',
      },
    }),
  ],
  server: {
    port: 5173,
  },
})
