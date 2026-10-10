// @ts-expect-error node builtins are untyped in this DOM-only tsconfig; vitest runs in Node.
import { existsSync, readFileSync } from 'node:fs'

import { describe, expect, it } from 'vitest'

// jsdom gives import.meta.url an http:// scheme, so resolve through the Node cwd instead.
declare const process: { cwd: () => string }

interface ManifestIcon {
  src: string
  sizes: string
  type: string
  purpose: string
}

interface ManifestShortcut {
  name: string
  url: string
}

interface WebAppManifest {
  name: string
  short_name: string
  start_url: string
  scope: string
  display: string
  theme_color: string
  background_color: string
  icons: ManifestIcon[]
  shortcuts: ManifestShortcut[]
}

const manifest = JSON.parse(
  readFileSync(`${process.cwd()}/public/manifest.webmanifest`, 'utf8'),
) as WebAppManifest

const publicFile = (path: string) => `${process.cwd()}/public${path}`

const swSource = readFileSync(publicFile('/sw.js'), 'utf8')

describe('web app manifest', () => {
  it('declares the installable app identity', () => {
    expect(manifest.name).toContain('PropNoxa')
    expect(manifest.short_name).toBe('PropNoxa')
    expect(manifest.start_url).toBe('/')
    expect(manifest.scope).toBe('/')
    expect(manifest.display).toBe('standalone')
  })

  it('uses the brand colour for splash screens and browser chrome', () => {
    expect(manifest.theme_color).toBe('#102a43')
    expect(manifest.background_color).toBe('#102a43')
  })

  it('ships 192px, 512px, and maskable icons that exist on disk', () => {
    expect(manifest.icons.some((icon) => icon.sizes === '192x192' && icon.purpose === 'any')).toBe(true)
    expect(manifest.icons.some((icon) => icon.sizes === '512x512' && icon.purpose === 'any')).toBe(true)
    expect(manifest.icons.some((icon) => icon.purpose === 'maskable')).toBe(true)

    manifest.icons.forEach((icon) => {
      expect(existsSync(publicFile(icon.src)), icon.src).toBe(true)
      expect(icon.type).toBe('image/png')
    })
  })

  it('offers shortcuts into the two most common tasks', () => {
    expect(manifest.shortcuts.map((shortcut) => shortcut.url)).toEqual(['/properties', '/dashboard'])
  })

  it('ships the offline shell and the service worker it pairs with', () => {
    expect(existsSync(publicFile('/sw.js'))).toBe(true)
    expect(existsSync(publicFile('/offline.html'))).toBe(true)
  })

  it('keeps the build-injection markers the precache plugin rewrites', () => {
    expect(swSource).toContain('/*__PRECACHE_START__*/')
    expect(swSource).toContain('/*__PRECACHE_END__*/')
    expect(swSource).toContain('/*__BUILD_ID__*/')
  })

  it('ignores Vary on cache lookups so crossorigin asset requests still match', () => {
    const matchCalls: string[] = swSource.match(/caches\.match\([^)]*\)/g) ?? []
    expect(matchCalls).toHaveLength(4)
    matchCalls.forEach((call) => expect(call).toContain('ignoreVary: true'))
  })
})
