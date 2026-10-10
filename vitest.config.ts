import { defineConfig } from 'vitest/config'

// No React plugin needed: Vitest transforms .tsx through esbuild, which already
// picks up "jsx": "react-jsx" from tsconfig.json.
export default defineConfig({
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    include: ['src/**/*.test.{ts,tsx}'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'lcov'],
      reportsDirectory: './coverage',
      include: ['src/utils/**', 'src/components/**', 'src/services/**', 'src/contexts/**'],
      exclude: ['src/**/*.test.*', 'src/test/**'],
      // Only files a test actually loads count towards the percentage, so the
      // number measures the code under test instead of every untested module.
      all: false,
      thresholds: { lines: 70, functions: 65, branches: 70 },
    },
  },
})
