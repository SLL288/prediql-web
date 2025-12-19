export function isValidHttpUrl(value: string): boolean {
  try {
    const url = new URL(value)
    return url.protocol === 'http:' || url.protocol === 'https:'
  } catch (err) {
    return false
  }
}

export function tryParseJson(value: string | undefined): Record<string, any> | undefined {
  if (!value || !value.trim()) return undefined
  return JSON.parse(value)
}

export function isPositiveInt(value: number, max = Number.MAX_SAFE_INTEGER): boolean {
  return Number.isInteger(value) && value > 0 && value <= max
}
