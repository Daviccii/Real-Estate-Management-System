/*
 * Build-time service-worker metadata injection.
 *
 * public/sw.js carries two marker pairs: one wraps the precache URL list and
 * one stamps the cache-version string. After `vite build` has written dist/,
 * the plugin below rewrites both:
 *  - the precache list becomes every built file, so one online visit is
 *    enough to run the whole app offline;
 *  - the version becomes a hash of that list, so each deploy activates fresh
 *    caches and activate() evicts the previous deploy's.
 */

// @ts-expect-error node builtins are untyped in this DOM-only tsconfig; this module only runs under Node.
import { createHash } from 'node:crypto'
// @ts-expect-error node builtins are untyped in this DOM-only tsconfig; this module only runs under Node.
import { existsSync, readdirSync, readFileSync, writeFileSync } from 'node:fs'
// @ts-expect-error node builtins are untyped in this DOM-only tsconfig; this module only runs under Node.
import { join, resolve } from 'node:path'

import type { Plugin } from 'vite'

declare const process: { cwd: () => string }

export const PRECACHE_START = '/*__PRECACHE_START__*/'
export const PRECACHE_END = '/*__PRECACHE_END__*/'
export const BUILD_ID_TOKEN = '/*__BUILD_ID__*/'

export const computePrecacheList = (files: string[]): string[] => {
  const urls = files
    .map((file) => file.replace(/\\/g, '/'))
    .filter((file) => file !== 'sw.js' && !file.endsWith('/sw.js'))
    .map((file) => (file === 'index.html' ? '/' : `/${file}`))
  const root = urls.includes('/') ? ['/'] : []
  const nested = [...new Set(urls.filter((url) => url !== '/'))].sort()
  return [...root, ...nested]
}

export const computeBuildId = (precacheList: string[]): string =>
  createHash('sha256').update(JSON.stringify(precacheList)).digest('hex').slice(0, 12)

export const injectBuildMetadata = (source: string, precacheList: string[]): string => {
  const start = source.indexOf(PRECACHE_START)
  const end = source.indexOf(PRECACHE_END)
  if (start === -1 || end === -1 || end < start) {
    throw new Error('sw.js is missing the precache injection markers')
  }
  const injected = `${PRECACHE_START} ${JSON.stringify(precacheList, null, 2)} ${PRECACHE_END}`
  const withPrecache = source.slice(0, start) + injected + source.slice(end + PRECACHE_END.length)

  if (!withPrecache.includes(BUILD_ID_TOKEN)) {
    throw new Error('sw.js is missing the build id token')
  }
  const stamp = `${BUILD_ID_TOKEN} '${computeBuildId(precacheList)}'`
  const stamped = withPrecache.replace(/\/\*__BUILD_ID__\*\/\s*'[^']*'/, stamp)
  if (stamped === withPrecache && !withPrecache.includes(stamp)) {
    throw new Error('sw.js build id token is not followed by a quoted version string')
  }
  return stamped
}

const listDistFiles = (root: string, prefix = ''): string[] =>
  readdirSync(join(root, prefix), { withFileTypes: true }).flatMap(
    (entry: { name: string; isDirectory: () => boolean }) => {
      const relative = prefix ? `${prefix}/${entry.name}` : entry.name
      if (entry.isDirectory()) return listDistFiles(root, relative)
      return [relative]
    },
  )

export const createPwaPrecachePlugin = (): Plugin => ({
  name: 'propnoxa:pwa-precache',
  apply: 'build',
  closeBundle() {
    const distDir = resolve(process.cwd(), 'dist')
    const swPath = join(distDir, 'sw.js')
    if (!existsSync(swPath)) return
    const precache = computePrecacheList(listDistFiles(distDir))
    const source = readFileSync(swPath, 'utf8')
    writeFileSync(swPath, injectBuildMetadata(source, precache))
  },
})
