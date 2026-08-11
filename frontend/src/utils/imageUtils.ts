/** Convert hex-encoded image bytes (from surgical guidance API) to a blob URL */
export function hexToBlobUrl(hex: string, mime = 'image/jpeg'): string {
  const pairs = hex.match(/.{1,2}/g)
  if (!pairs) return ''
  const bytes = new Uint8Array(pairs.map((b) => parseInt(b, 16)))
  const blob = new Blob([bytes], { type: mime })
  return URL.createObjectURL(blob)
}
