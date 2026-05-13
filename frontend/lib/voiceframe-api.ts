const DEFAULT_VOICEFRAME_API_BASE_URL = "http://127.0.0.1:8000"

export function getVoiceframeApiBaseUrl() {
  return (process.env.NEXT_PUBLIC_VOICEFRAME_API_BASE_URL || DEFAULT_VOICEFRAME_API_BASE_URL).replace(/\/$/, "")
}

export function voiceframeApiUrl(path: string) {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`
  return `${getVoiceframeApiBaseUrl()}${normalizedPath}`
}

/**
 * Media URLs are served by Vistarak Django at /media/... on the same host.
 */
export function voiceframeMediaUrl(path: string) {
  if (!path) return ""
  if (/^https?:\/\//i.test(path)) return path
  const base = getVoiceframeApiBaseUrl()
  return `${base}${path.startsWith("/") ? path : `/${path}`}`
}
