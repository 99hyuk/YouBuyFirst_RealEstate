# Session Auth MVP

## Decision

The first login implementation uses Spring Security with the servlet container's default in-memory HTTP session store.

- Browser identity is carried by the `JSESSIONID` cookie.
- The backend resolves the session to an `APP_USERS` row.
- Login uses the user-facing `username` field, while `email` and `displayName` remain unique account profile fields.
- Redis is intentionally not used in this MVP.
- If the backend runs with more than one instance, use sticky sessions or migrate to Spring Session with Redis before relying on shared login state.

## Endpoints

| endpoint | method | auth | response |
| --- | --- | --- | --- |
| `/api/auth/register` | POST | public | `201` with current user and `JSESSIONID` cookie |
| `/api/auth/login` | POST | public | `200` with current user and `JSESSIONID` cookie |
| `/api/auth/me` | GET | session | `200` with current user, `401` without session |
| `/api/auth/logout` | POST | session | `204`, invalidates the session |

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

## Session Cookie

Default runtime settings live in `backend/src/main/resources/application.yml`.

- `SERVER_SESSION_TIMEOUT`: default `30m`
- `SERVER_SESSION_COOKIE_SECURE`: default `false` for local development, set `true` behind HTTPS
- `SameSite`: `lax`
- `HttpOnly`: `true`

## Follow-Up

- Add user-scoped watch target, alert rule, observation memo, and chat history APIs using the authenticated `APP_USERS.id`.
- Re-enable CSRF protection with a SPA token endpoint before sensitive user mutations become broad.
