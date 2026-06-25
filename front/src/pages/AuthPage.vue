<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue';
import { useRouter } from 'vue-router';

import { loadOAuthProviders, login, type OAuthProviderStatus } from '../lib/auth-session';

const router = useRouter();
const usernamePattern = '[A-Za-z0-9]+';

const loginForm = reactive({
  username: '',
  password: ''
});
const loginError = ref('');
const loginPending = ref(false);
const oauthProviders = ref<OAuthProviderStatus[]>([]);

const normalizeUsername = (value: string) => value.trim().toLowerCase();

onMounted(async () => {
  oauthProviders.value = await loadOAuthProviders();
});

const handleLogin = async () => {
  loginError.value = '';
  loginPending.value = true;
  try {
    await login({
      username: normalizeUsername(loginForm.username),
      password: loginForm.password
    });
    await router.push('/dashboard');
  } catch (error) {
    loginError.value = error instanceof Error ? error.message : '로그인 요청을 처리하지 못했습니다.';
  } finally {
    loginPending.value = false;
  }
};
</script>

<template>
  <section class="surface-page auth-page" aria-labelledby="auth-title">
    <div class="auth-header">
      <p class="label">계정</p>
      <h2 id="auth-title">로그인</h2>
      <span>로그인하면 상단 계정 상태와 채팅 참여 상태를 사용자 세션 기준으로 관리합니다.</span>
    </div>

    <section class="auth-grid auth-single-grid" aria-label="로그인">
      <form class="auth-panel" data-testid="login-submit" @submit.prevent="handleLogin">
        <div class="section-band-title compact">
          <div>
            <p class="label">기존 사용자</p>
            <h3>로그인</h3>
          </div>
        </div>
        <label>
          <span>아이디</span>
          <input
            v-model="loginForm.username"
            autocomplete="username"
            data-testid="login-username"
            inputmode="text"
            maxlength="20"
            minlength="4"
            :pattern="usernamePattern"
            required
            title="아이디는 영문과 숫자만 사용할 수 있습니다."
            type="text"
          />
        </label>
        <label>
          <span>비밀번호</span>
          <input
            v-model="loginForm.password"
            autocomplete="current-password"
            data-testid="login-password"
            maxlength="100"
            required
            type="password"
          />
        </label>
        <p v-if="loginError" class="auth-error" role="alert">{{ loginError }}</p>
        <button class="auth-submit-button" :disabled="loginPending" type="submit">
          {{ loginPending ? '확인 중' : '로그인' }}
        </button>
        <div class="oauth-login-list icon-row" aria-label="간편 로그인">
          <p>간편 로그인</p>
          <template v-for="provider in oauthProviders" :key="provider.provider">
            <a
              v-if="provider.configured"
              class="oauth-login-button"
              :class="provider.provider"
              :aria-label="`${provider.displayName} 로그인`"
              :data-testid="`oauth-login-${provider.provider}`"
              :href="provider.authorizationUrl"
              :title="`${provider.displayName} 로그인`"
            >
              <span class="oauth-provider-icon google" v-if="provider.provider === 'google'" aria-hidden="true">
                <svg viewBox="0 0 24 24" focusable="false">
                  <path fill="#4285f4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                  <path fill="#34a853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.15v2.84C3.96 20.53 7.68 23 12 23z" />
                  <path fill="#fbbc05" d="M5.84 14.1c-.22-.66-.35-1.36-.35-2.1s.13-1.44.35-2.1V7.06H2.15C1.4 8.56 1 10.23 1 12s.4 3.44 1.15 4.94l3.69-2.84z" />
                  <path fill="#ea4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.68 1 3.96 3.47 2.15 7.06L5.84 9.9C6.71 7.31 9.14 5.38 12 5.38z" />
                </svg>
              </span>
              <span class="oauth-provider-icon naver" v-else-if="provider.provider === 'naver'" aria-hidden="true">
                <svg viewBox="0 0 24 24" focusable="false">
                  <rect width="24" height="24" rx="5" fill="#03c75a" />
                  <path fill="#ffffff" d="M14.72 12.42 9.08 4.8H4.8v14.4h4.48v-7.62l5.64 7.62h4.28V4.8h-4.48v7.62z" />
                </svg>
              </span>
              <span class="oauth-provider-icon kakao" v-else aria-hidden="true">
                <svg viewBox="0 0 24 24" focusable="false">
                  <path fill="#391b1b" d="M12 4.2c-4.42 0-8 2.78-8 6.2 0 2.12 1.38 3.99 3.49 5.11l-.69 2.74c-.07.27.24.49.47.33l3.31-2.16c.46.07.93.1 1.42.1 4.42 0 8-2.78 8-6.2S16.42 4.2 12 4.2z" />
                </svg>
              </span>
            </a>
            <button
              v-else
              class="oauth-login-button disabled"
              :class="provider.provider"
              :aria-label="`${provider.displayName} 설정 필요`"
              :data-testid="`oauth-login-${provider.provider}`"
              disabled
              :title="`${provider.displayName} 설정 필요`"
              type="button"
            >
              <span class="oauth-provider-icon google" v-if="provider.provider === 'google'" aria-hidden="true">
                <svg viewBox="0 0 24 24" focusable="false">
                  <path fill="#4285f4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                  <path fill="#34a853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.15v2.84C3.96 20.53 7.68 23 12 23z" />
                  <path fill="#fbbc05" d="M5.84 14.1c-.22-.66-.35-1.36-.35-2.1s.13-1.44.35-2.1V7.06H2.15C1.4 8.56 1 10.23 1 12s.4 3.44 1.15 4.94l3.69-2.84z" />
                  <path fill="#ea4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.68 1 3.96 3.47 2.15 7.06L5.84 9.9C6.71 7.31 9.14 5.38 12 5.38z" />
                </svg>
              </span>
              <span class="oauth-provider-icon naver" v-else-if="provider.provider === 'naver'" aria-hidden="true">
                <svg viewBox="0 0 24 24" focusable="false">
                  <rect width="24" height="24" rx="5" fill="#03c75a" />
                  <path fill="#ffffff" d="M14.72 12.42 9.08 4.8H4.8v14.4h4.48v-7.62l5.64 7.62h4.28V4.8h-4.48v7.62z" />
                </svg>
              </span>
              <span class="oauth-provider-icon kakao" v-else aria-hidden="true">
                <svg viewBox="0 0 24 24" focusable="false">
                  <path fill="#391b1b" d="M12 4.2c-4.42 0-8 2.78-8 6.2 0 2.12 1.38 3.99 3.49 5.11l-.69 2.74c-.07.27.24.49.47.33l3.31-2.16c.46.07.93.1 1.42.1 4.42 0 8-2.78 8-6.2S16.42 4.2 12 4.2z" />
                </svg>
              </span>
            </button>
          </template>
        </div>
        <div class="auth-secondary-actions" aria-label="계정 보조 작업">
          <RouterLink data-testid="register-link" to="/auth/register">회원가입 하러가기</RouterLink>
          <RouterLink data-testid="find-account-link" to="/auth/find-account">ID/PW 찾기</RouterLink>
        </div>
      </form>
    </section>
  </section>
</template>
