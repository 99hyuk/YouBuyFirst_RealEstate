<script setup lang="ts">
import { reactive, ref } from 'vue';
import { useRouter } from 'vue-router';

import { login } from '../lib/auth-session';

const router = useRouter();
const usernamePattern = '[A-Za-z0-9]+';

const loginForm = reactive({
  username: '',
  password: ''
});
const loginError = ref('');
const loginPending = ref(false);

const normalizeUsername = (value: string) => value.trim().toLowerCase();

const handleLogin = async () => {
  loginError.value = '';
  loginPending.value = true;
  try {
    await login({
      username: normalizeUsername(loginForm.username),
      password: loginForm.password
    });
    await router.push('/realestate/mypage');
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
      <span>마이페이지 저장 지역, 알림 조건, 관찰 메모를 사용자 계정 기준으로 관리합니다.</span>
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
        <div class="auth-secondary-actions" aria-label="계정 보조 작업">
          <RouterLink data-testid="register-link" to="/auth/register">회원가입 하러가기</RouterLink>
          <RouterLink data-testid="find-account-link" to="/auth/find-account">ID/PW 찾기</RouterLink>
        </div>
      </form>
    </section>
  </section>
</template>
