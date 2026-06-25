import { ref } from 'vue';

export type AuthUser = {
  id: string;
  username: string;
  email: string;
  displayName: string;
  authProvider: string;
  createdAt: string;
  lastSeenAt: string;
};

export type LoginPayload = {
  username: string;
  password: string;
};

export type RegisterPayload = LoginPayload & {
  email: string;
  displayName: string;
};

export type OAuthProviderStatus = {
  provider: 'google' | 'naver' | 'kakao';
  displayName: string;
  authorizationUrl: string;
  configured: boolean;
};

export const currentAuthUser = ref<AuthUser | null>(null);

const jsonHeaders = {
  'Content-Type': 'application/json'
};

const defaultOAuthProviders: OAuthProviderStatus[] = [
  {
    provider: 'google',
    displayName: 'Google',
    authorizationUrl: '/oauth2/authorization/google',
    configured: false
  },
  {
    provider: 'naver',
    displayName: 'Naver',
    authorizationUrl: '/oauth2/authorization/naver',
    configured: false
  },
  {
    provider: 'kakao',
    displayName: 'Kakao',
    authorizationUrl: '/oauth2/authorization/kakao',
    configured: false
  }
];

const isOAuthProviderList = (value: unknown): value is OAuthProviderStatus[] => (
  Array.isArray(value)
  && value.every((provider) => (
    typeof provider === 'object'
    && provider !== null
    && ['google', 'naver', 'kakao'].includes(String((provider as OAuthProviderStatus).provider))
    && typeof (provider as OAuthProviderStatus).displayName === 'string'
    && typeof (provider as OAuthProviderStatus).authorizationUrl === 'string'
    && typeof (provider as OAuthProviderStatus).configured === 'boolean'
  ))
);

export async function loadOAuthProviders(): Promise<OAuthProviderStatus[]> {
  try {
    const response = await fetch('/api/auth/oauth/providers', {
      credentials: 'include'
    });

    if (!response.ok) {
      return defaultOAuthProviders;
    }

    const providers = await response.json() as unknown;
    return isOAuthProviderList(providers) ? providers : defaultOAuthProviders;
  } catch {
    return defaultOAuthProviders;
  }
}

export async function loadCurrentUser(): Promise<AuthUser | null> {
  const response = await fetch('/api/auth/me', {
    credentials: 'include'
  });

  if (response.status === 401) {
    currentAuthUser.value = null;
    return null;
  }
  if (!response.ok) {
    throw new Error('현재 로그인 상태를 확인하지 못했습니다.');
  }

  const user = await response.json() as AuthUser;
  currentAuthUser.value = user;
  return user;
}

export async function login(payload: LoginPayload): Promise<AuthUser> {
  const response = await fetch('/api/auth/login', {
    body: JSON.stringify(payload),
    credentials: 'include',
    headers: jsonHeaders,
    method: 'POST'
  });

  if (response.status === 401) {
    throw new Error('아이디나 비밀번호를 다시 확인해주세요.');
  }
  if (!response.ok) {
    throw new Error('로그인 요청을 처리하지 못했습니다.');
  }

  const user = await response.json() as AuthUser;
  currentAuthUser.value = user;
  return user;
}

export async function register(payload: RegisterPayload): Promise<AuthUser> {
  const response = await fetch('/api/auth/register', {
    body: JSON.stringify(payload),
    credentials: 'include',
    headers: jsonHeaders,
    method: 'POST'
  });

  if (response.status === 409) {
    throw new Error('이미 사용 중인 아이디, 이메일, 닉네임이 있습니다.');
  }
  if (!response.ok) {
    throw new Error('회원가입 정보를 다시 확인해주세요.');
  }

  const user = await response.json() as AuthUser;
  currentAuthUser.value = user;
  return user;
}

export async function logout(): Promise<void> {
  const response = await fetch('/api/auth/logout', {
    credentials: 'include',
    method: 'POST'
  });

  if (!response.ok && response.status !== 401) {
    throw new Error('로그아웃 요청을 처리하지 못했습니다.');
  }
  currentAuthUser.value = null;
}
