import { defineConfig } from 'vite'

import { createPwaPrecachePlugin } from './src/pwa/swBuild'

export default defineConfig({
  plugins: [createPwaPrecachePlugin()],
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes('/src/pages/admin/')) return 'portal-admin'
          if (id.includes('/src/pages/manager/')) return 'portal-manager'
          if (id.includes('/src/pages/owner/')) return 'portal-owner'
          if (id.includes('/src/pages/agent/')) return 'portal-agent'
          if (id.includes('/src/pages/tenant/')) return 'portal-tenant'
          if (id.includes('/src/pages/provider/')) return 'portal-provider'
          if (id.includes('/node_modules/')) return 'vendor'
          return undefined
        },
      },
    },
  },
})
