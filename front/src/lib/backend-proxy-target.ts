export function resolveBackendProxyTarget(env: Record<string, string | undefined>): string {
  return env.VITE_BACKEND_PROXY_TARGET?.trim()
    || env.BACKEND_PROXY_TARGET?.trim()
    || 'http://localhost:8080';
}
