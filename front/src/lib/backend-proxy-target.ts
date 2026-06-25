export function resolveBackendProxyTarget(env: Record<string, string | undefined>): string {
  return env.VITE_BACKEND_PROXY_TARGET?.trim()
    || env.BACKEND_PROXY_TARGET?.trim()
    || 'http://127.0.0.1:8080';
}
