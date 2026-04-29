const DEFAULT_MANIM_API_BASE_URL = "http://127.0.0.1:8000"
const DEFAULT_MANIM_API_ROUTE_PREFIX = "/visualization"

function _envBool(name: string) {
  const raw = (process.env[name] || "").toLowerCase()
  return raw === "1" || raw === "true" || raw === "yes"
}

/**
 * Returns the API base URL used for manim endpoints. If NEXT_PUBLIC_MANIM_API_USE_DJANGO
 * is enabled, the configured route prefix (default `/visualization`) will be appended
 * to the base host unless it's already present.
 */
export function getManimApiBaseUrl() {
  const rawBase = (process.env.NEXT_PUBLIC_MANIM_API_BASE_URL || DEFAULT_MANIM_API_BASE_URL).replace(/\/$/, "")
  const useDjango = _envBool("NEXT_PUBLIC_MANIM_API_USE_DJANGO")
  const routePrefix = (process.env.NEXT_PUBLIC_MANIM_API_ROUTE_PREFIX || DEFAULT_MANIM_API_ROUTE_PREFIX).replace(/\/$/, "")

  if (!useDjango) return rawBase

  // if the base already contains the prefix, return as-is
  if (rawBase.endsWith(routePrefix) || rawBase.includes(routePrefix + "/")) return rawBase
  return `${rawBase}${routePrefix.startsWith("/") ? routePrefix : `/${routePrefix}`}`
}

/**
 * Returns the host/base to use for static/media URLs. If the API base includes
 * a Django route prefix (e.g. `/visualization`), strip it — media lives at the
 * site root (e.g. `http://host:port/media/...`).
 */
export function getManimHostBase() {
  const rawBase = (process.env.NEXT_PUBLIC_MANIM_API_BASE_URL || DEFAULT_MANIM_API_BASE_URL).replace(/\/$/, "")
  const routePrefix = (process.env.NEXT_PUBLIC_MANIM_API_ROUTE_PREFIX || DEFAULT_MANIM_API_ROUTE_PREFIX).replace(/\/$/, "")
  const useDjango = _envBool("NEXT_PUBLIC_MANIM_API_USE_DJANGO")
  if (!useDjango) return rawBase
  // if base already contains prefix, remove it to get host base
  if (rawBase.endsWith(routePrefix)) return rawBase.slice(0, -routePrefix.length)
  return rawBase
}

export function manimApiUrl(path: string) {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`
  return `${getManimApiBaseUrl()}${normalizedPath}`
}

export function manimMediaUrl(path: string) {
  if (!path) return ""
  if (/^https?:\/\//i.test(path)) return path
  const base = getManimHostBase()
  return `${base}${path.startsWith("/") ? path : `/${path}`}`
}
