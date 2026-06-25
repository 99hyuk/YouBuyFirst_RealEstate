# Session Auth MVP

## Decision

The first login implementation uses Spring Security with the servlet container's default in-memory HTTP session store.

- Browser identity is carried by the `JSESSIONID` cookie.
- The backend resolves the session to an `APP_USERS` row.
- Login uses the user-facing `username` field, while `email` and `displayName` remain unique account profile fields.
- Google, Naver, and Kakao OAuth login reuse the same session contract after provider authentication succeeds.
- Redis is intentionally not used in this MVP.
- If the backend runs with more than one instance, use sticky sessions or migrate to Spring Session with Redis before relying on shared login state.

## Endpoints

| endpoint | method | auth | response |
| --- | --- | --- | --- |
| `/api/auth/register` | POST | public | `201` with current user and `JSESSIONID` cookie |
| `/api/auth/login` | POST | public | `200` with current user and `JSESSIONID` cookie |
| `/api/auth/me` | GET | session | `200` with current user, `401` without session |
| `/api/auth/oauth/providers` | GET | public | Google, Naver, and Kakao OAuth availability for the current backend config |
| `/api/auth/logout` | POST | session | `204`, invalidates the session |
| `/oauth2/authorization/{provider}` | GET | public | redirects to Google, Naver, or Kakao when that provider has client credentials |
| `/login/oauth2/code/{provider}` | GET | provider callback | creates or links an `APP_USERS` row, sets `JSESSIONID`, redirects to `/dashboard` |

Register request:

```json
{
  "username": "observer01",
  "email": "observer@example.com",
  "password": "watch-1234!",
  "displayName": "Market Observer"
}
```

Validation:

- `username`: English letters and numbers only, 4-20 characters, unique.
- `password`: 8-100 characters and must include a letter, number, and special character.
- `email`: valid email format, unique.
- `displayName`: 2-20 characters after trimming, unique.

Login request:

```json
{
  "username": "observer01",
  "password": "watch-1234!"
}
```

Current user response:

```json
{
  "id": "uuid",
  "username": "observer01",
  "email": "observer@example.com",
  "displayName": "Market Observer",
  "authProvider": "local",
  "createdAt": "2026-06-23T09:00:00Z",
  "lastSeenAt": "2026-06-23T09:05:00Z"
}
```

OAuth account handling:

- Provider identities are stored in `user_oauth_accounts` with unique `(provider, provider_user_id)`.
- First OAuth login creates an `APP_USERS` row when no account with that email exists.
- If a provider email matches an existing local account, the provider identity is linked to that user instead of creating a duplicate.
- Google login is handled through the OIDC user service and is converted to the same `AppUserPrincipal` session shape as Naver and Kakao.
- The frontend checks `/api/auth/oauth/providers` before rendering social OAuth links. Providers without configured credentials are shown as disabled buttons, so local users do not hit Spring's Whitelabel 404 fallback.
- Google and Naver need `client-id` and `client-secret`; Kakao needs the REST API key as `client-id`, and `client-secret` only when Kakao client secret verification is enabled.
- Supported env vars: `OAUTH_GOOGLE_CLIENT_ID`, `OAUTH_GOOGLE_CLIENT_SECRET`, `OAUTH_NAVER_CLIENT_ID`, `OAUTH_NAVER_CLIENT_SECRET`, `OAUTH_KAKAO_CLIENT_ID`, `OAUTH_KAKAO_CLIENT_SECRET`.
- Set `APP_AUTH_OAUTH_REDIRECT_BASE_URL` when OAuth callbacks must return through a public proxy origin. For example, `https://example.ngrok-free.dev` produces `https://example.ngrok-free.dev/login/oauth2/code/google`.
- Local SPA redirects can be set with `APP_AUTH_OAUTH_SUCCESS_REDIRECT=http://127.0.0.1:5173/dashboard` and `APP_AUTH_OAUTH_FAILURE_REDIRECT=http://127.0.0.1:5173/auth/login?oauth=failed`.

## Session Cookie

Default runtime settings live in `backend/src/main/resources/application.yml`.

- `SERVER_SESSION_TIMEOUT`: default `30m`
- `SERVER_SESSION_COOKIE_SECURE`: default `false` for local development, set `true` behind HTTPS
- `SameSite`: `lax`
- `HttpOnly`: `true`

## Follow-Up

- Add user-scoped watch target, alert rule, observation memo, and chat history APIs using the authenticated `APP_USERS.id`.
- Re-enable CSRF protection with a SPA token endpoint before sensitive user mutations become broad.
