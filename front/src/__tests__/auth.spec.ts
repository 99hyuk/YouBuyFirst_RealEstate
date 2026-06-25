import { readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { flushPromises, mount } from '@vue/test-utils';
import { createMemoryHistory, createRouter } from 'vue-router';
import { afterEach, describe, expect, it, vi } from 'vitest';

import App from '../App.vue';
import { routes } from '../router/routes';

const testDir = dirname(fileURLToPath(import.meta.url));

type AuthUser = {
  id: string;
  username: string;
  email: string;
  displayName: string;
  authProvider: string;
  createdAt: string;
  lastSeenAt: string;
};

const currentUser: AuthUser = {
  id: 'user-1',
  username: 'happy01',
  email: 'happy@example.com',
  displayName: '행복',
  authProvider: 'local',
  createdAt: '2026-06-23T00:00:00Z',
  lastSeenAt: '2026-06-23T00:00:00Z'
};

const configuredOAuthProviders = [
  {
    provider: 'google',
    displayName: 'Google',
    authorizationUrl: '/oauth2/authorization/google',
    configured: true
  },
  {
    provider: 'naver',
    displayName: 'Naver',
    authorizationUrl: '/oauth2/authorization/naver',
    configured: true
  },
  {
    provider: 'kakao',
    displayName: 'Kakao',
    authorizationUrl: '/oauth2/authorization/kakao',
    configured: true
  }
];

const unconfiguredOAuthProviders = configuredOAuthProviders.map((provider) => ({
  ...provider,
  configured: false
}));

const mountAppAt = async (path: string) => {
  const router = createRouter({
    history: createMemoryHistory(),
    routes
  });

  router.push(path);
  await router.isReady();

  const wrapper = mount(App, {
    global: {
      plugins: [router]
    }
  });
  await flushPromises();

  return { wrapper, router };
};

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('session auth UI', () => {
  it('greets the current user and switches the account action to logout', async () => {
    vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url === '/api/auth/me') {
        return new Response(JSON.stringify(currentUser), {
          headers: { 'Content-Type': 'application/json' },
          status: 200
        });
      }
      if (url === '/api/auth/logout' && init?.method === 'POST') {
        return new Response(null, { status: 204 });
      }

      return new Response(JSON.stringify({ items: [] }), {
        headers: { 'Content-Type': 'application/json' },
        status: 200
      });
    }));

    const { wrapper } = await mountAppAt('/dashboard');

    expect(wrapper.get('[data-testid="auth-greeting"]').text()).toContain('행복님 안녕하세요');
    expect(wrapper.get('[data-testid="logout-button"]').text()).toContain('로그아웃');
  });

  it('renders only the login form with links to registration and account recovery', async () => {
    vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL) => {
      if (String(input) === '/api/auth/me') {
        return new Response(null, { status: 401 });
      }

      return new Response(JSON.stringify({ items: [] }), {
        headers: { 'Content-Type': 'application/json' },
        status: 200
      });
    }));

    const { wrapper } = await mountAppAt('/auth/login');

    expect(wrapper.text()).toContain('로그인');
    expect(wrapper.find('[data-testid="register-username"]').exists()).toBe(false);
    expect(wrapper.get('[data-testid="login-username"]').attributes('pattern')).toBe('[A-Za-z0-9]+');
    expect(wrapper.get('[data-testid="register-link"]').attributes('href')).toBe('/auth/register');
    expect(wrapper.get('[data-testid="find-account-link"]').attributes('href')).toBe('/auth/find-account');
  });

  it('renders OAuth login entry points for Google, Naver, and Kakao', async () => {
    vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url === '/api/auth/me') {
        return new Response(null, { status: 401 });
      }
      if (url === '/api/auth/oauth/providers') {
        return new Response(JSON.stringify(configuredOAuthProviders), {
          headers: { 'Content-Type': 'application/json' },
          status: 200
        });
      }

      return new Response(JSON.stringify({ items: [] }), {
        headers: { 'Content-Type': 'application/json' },
        status: 200
      });
    }));

    const { wrapper } = await mountAppAt('/auth/login');

    expect(wrapper.get('[data-testid="oauth-login-google"]').attributes('href')).toBe('/oauth2/authorization/google');
    expect(wrapper.get('[data-testid="oauth-login-naver"]').attributes('href')).toBe('/oauth2/authorization/naver');
    expect(wrapper.get('[data-testid="oauth-login-kakao"]').attributes('href')).toBe('/oauth2/authorization/kakao');
    expect(wrapper.get('[data-testid="oauth-login-google"]').attributes('aria-label')).toBe('Google 로그인');
    expect(wrapper.find('[data-testid="oauth-login-google"] .oauth-provider-icon.google').exists()).toBe(true);
    expect(wrapper.find('[data-testid="oauth-login-naver"] .oauth-provider-icon.naver').exists()).toBe(true);
    expect(wrapper.find('[data-testid="oauth-login-kakao"] .oauth-provider-icon.kakao').exists()).toBe(true);
  });

  it('disables OAuth login and registration entry points before provider credentials are configured', async () => {
    vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url === '/api/auth/me') {
        return new Response(null, { status: 401 });
      }
      if (url === '/api/auth/oauth/providers') {
        return new Response(JSON.stringify(unconfiguredOAuthProviders), {
          headers: { 'Content-Type': 'application/json' },
          status: 200
        });
      }

      return new Response(JSON.stringify({ items: [] }), {
        headers: { 'Content-Type': 'application/json' },
        status: 200
      });
    }));

    const login = await mountAppAt('/auth/login');

    expect(login.wrapper.get('[data-testid="oauth-login-google"]').element.tagName).toBe('BUTTON');
    expect(login.wrapper.get('[data-testid="oauth-login-google"]').attributes('disabled')).toBeDefined();
    expect(login.wrapper.get('[data-testid="oauth-login-google"]').attributes('href')).toBeUndefined();

    login.wrapper.unmount();

    const register = await mountAppAt('/auth/register');

    expect(register.wrapper.get('[data-testid="oauth-register-kakao"]').element.tagName).toBe('BUTTON');
    expect(register.wrapper.get('[data-testid="oauth-register-kakao"]').attributes('disabled')).toBeDefined();
    expect(register.wrapper.get('[data-testid="oauth-register-kakao"]').attributes('href')).toBeUndefined();
  });

  it('renders registration as a separate page with strict field constraints', async () => {
    vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL) => {
      if (String(input) === '/api/auth/me') {
        return new Response(null, { status: 401 });
      }

      return new Response(JSON.stringify({ items: [] }), {
        headers: { 'Content-Type': 'application/json' },
        status: 200
      });
    }));

    const { wrapper } = await mountAppAt('/auth/register');

    expect(wrapper.text()).toContain('회원가입');
    expect(wrapper.find('[data-testid="login-password"]').exists()).toBe(false);
    expect(wrapper.get('[data-testid="register-username"]').attributes('pattern')).toBe('[A-Za-z0-9]+');
    expect(wrapper.get('[data-testid="register-email"]').attributes('type')).toBe('email');
    expect(wrapper.get('[data-testid="register-display-name"]').attributes('maxlength')).toBe('20');
    expect(wrapper.get('[data-testid="register-password"]').attributes('pattern')).toContain('(?=.*[A-Za-z])');
    expect(wrapper.get('[data-testid="register-password"]').attributes('pattern')).toContain('(?=.*\\d)');
    expect(wrapper.get('[data-testid="register-password"]').attributes('pattern')).toContain('(?=.*[^A-Za-z0-9])');
  });

  it('renders account recovery as a separate page for ID and password lookup', async () => {
    vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL) => {
      if (String(input) === '/api/auth/me') {
        return new Response(null, { status: 401 });
      }

      return new Response(JSON.stringify({ items: [] }), {
        headers: { 'Content-Type': 'application/json' },
        status: 200
      });
    }));

    const { wrapper } = await mountAppAt('/auth/find-account');

    expect(wrapper.text()).toContain('ID 찾기');
    expect(wrapper.text()).toContain('PW 찾기');
    expect(wrapper.get('[data-testid="find-id-email"]').attributes('type')).toBe('email');
    expect(wrapper.get('[data-testid="find-password-username"]').attributes('pattern')).toBe('[A-Za-z0-9]+');
    expect(wrapper.get('[data-testid="find-login-link"]').attributes('href')).toBe('/auth/login');
  });

  it('submits username and password with browser session credentials', async () => {
    const fetcher = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url === '/api/auth/me') {
        return new Response(null, { status: 401 });
      }
      if (url === '/api/auth/login') {
        return new Response(JSON.stringify(currentUser), {
          headers: { 'Content-Type': 'application/json' },
          status: 200
        });
      }

      return new Response(JSON.stringify({ items: [] }), {
        headers: { 'Content-Type': 'application/json' },
        status: 200
      });
    });
    vi.stubGlobal('fetch', fetcher);

    const { wrapper, router } = await mountAppAt('/auth/login');

    await wrapper.get('[data-testid="login-username"]').setValue('happy01');
    await wrapper.get('[data-testid="login-password"]').setValue('watch-1234!');
    await wrapper.get('[data-testid="login-submit"]').trigger('submit');
    await flushPromises();

    expect(fetcher).toHaveBeenCalledWith('/api/auth/login', expect.objectContaining({
      credentials: 'include',
      method: 'POST'
    }));
    expect(JSON.parse(String((fetcher.mock.calls.find(([input]) => input === '/api/auth/login')?.[1] as RequestInit).body))).toEqual({
      username: 'happy01',
      password: 'watch-1234!'
    });
    expect(router.currentRoute.value.path).toBe('/dashboard');
  });

  it('centers auth flow panels and styles every enabled auth button as clickable', () => {
    const styles = readFileSync(resolve(testDir, '../styles.css'), 'utf8');

    expect(styles).toContain('align-items: center;');
    expect(styles).toContain('justify-content: center;');
    expect(styles).toContain('.login-button:hover');
    expect(styles).toContain('.login-button:focus-visible');
    expect(styles).toContain('.auth-submit-button:hover:not(:disabled)');
    expect(styles).toContain('.auth-submit-button:focus-visible');
    expect(styles).toContain('.oauth-login-list.icon-row');
    expect(styles).toContain('grid-template-columns: repeat(3, 48px);');
    expect(styles).toContain('.oauth-provider-icon');
    expect(styles).toContain('cursor: pointer');
  });
});
