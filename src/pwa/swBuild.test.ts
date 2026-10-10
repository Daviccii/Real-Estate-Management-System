import { describe, expect, it } from 'vitest'

import {
  BUILD_ID_TOKEN,
  PRECACHE_END,
  PRECACHE_START,
  computeBuildId,
  computePrecacheList,
  injectBuildMetadata,
} from './swBuild'

const SOURCE = `const VERSION = /*__BUILD_ID__*/ 'dev'
const PRECACHE = /*__PRECACHE_START__*/ [
  '/',
  '/offline.html',
] /*__PRECACHE_END__*/

self.addEventListener('install', () => {})`

describe('computePrecacheList', () => {
  it('maps dist files to deduplicated, sorted cache urls with the shell first', () => {
    expect(
      computePrecacheList([
        'icons/icon-512.png',
        'index.html',
        'assets/index-abc.js',
        'sw.js',
        'assets/sw.js',
        'icons/icon-192.png',
        'assets\\vendor-abc.js',
        'index.html',
      ]),
    ).toEqual([
      '/',
      '/assets/index-abc.js',
      '/assets/vendor-abc.js',
      '/icons/icon-192.png',
      '/icons/icon-512.png',
    ])
  })
})

describe('computeBuildId', () => {
  it('derives a stable short id that changes with the precache list', () => {
    const id = computeBuildId(['/', '/assets/index-abc.js'])
    expect(id).toMatch(/^[0-9a-f]{12}$/)
    expect(computeBuildId(['/', '/assets/index-abc.js'])).toBe(id)
    expect(computeBuildId(['/', '/assets/index-def.js'])).not.toBe(id)
  })
})

describe('injectBuildMetadata', () => {
  const urls = ['/', '/assets/index-abc.js', '/offline.html']

  it('replaces the marker region with the precache list and stamps the build id', () => {
    const output = injectBuildMetadata(SOURCE, urls)
    const between = output.slice(
      output.indexOf(PRECACHE_START) + PRECACHE_START.length,
      output.indexOf(PRECACHE_END),
    )
    expect(JSON.parse(between)).toEqual(urls)
    expect(output).toContain(`${BUILD_ID_TOKEN} '${computeBuildId(urls)}'`)
    expect(output).not.toContain("'dev'")
    expect(output.startsWith('const VERSION = ')).toBe(true)
    expect(output.endsWith("self.addEventListener('install', () => {})")).toBe(true)
  })

  it('is idempotent so repeated builds produce identical output', () => {
    const once = injectBuildMetadata(SOURCE, urls)
    expect(injectBuildMetadata(once, urls)).toBe(once)
  })

  it('fails loudly when the markers or the build id token are missing', () => {
    expect(() => injectBuildMetadata("const x = 'no markers'", urls)).toThrow(
      /precache injection markers/,
    )
    expect(() => injectBuildMetadata(SOURCE.replace(BUILD_ID_TOKEN, ''), urls)).toThrow(
      /build id token/,
    )
  })
})
