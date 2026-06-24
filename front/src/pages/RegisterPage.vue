<script setup lang="ts">
import { reactive, ref } from 'vue';
import { useRouter } from 'vue-router';

import { register } from '../lib/auth-session';

const router = useRouter();
const usernamePattern = '[A-Za-z0-9]+';
const passwordPattern = '(?=.*[A-Za-z])(?=.*\\d)(?=.*[^A-Za-z0-9]).{8,100}';

const registerForm = reactive({
  username: '',
  email: '',
  displayName: '',
  password: ''
});
const registerError = ref('');
const registerPending = ref(false);

const normalizeUsername = (value: string) => value.trim().toLowerCase();
const normalizeText = (value: string) => value.trim();

const handleRegister = async () => {
  registerError.value = '';
  registerPending.value = true;
  try {
    await register({
      username: normalizeUsername(registerForm.username),
      email: normalizeText(registerForm.email).toLowerCase(),
      displayName: normalizeText(registerForm.displayName),
      password: registerForm.password
    });
    await router.push('/realestate/mypage');
  } catch (error) {
    registerError.value = error instanceof Error ? error.message : '회원가입 요청을 처리하지 못했습니다.';
  } finally {
    registerPending.value = false;
  }
};
</script>

<template>
  <section class="surface-page auth-page" aria-labelledby="register-title">
    <div class="auth-header">
      <p class="label">계정</p>
      <h2 id="register-title">회원가입</h2>
      <span>저장 지역, 알림 조건, 관찰 메모를 사용자 계정 기준으로 관리합니다.</span>
    </div>

    <section class="auth-grid auth-single-grid" aria-label="회원가입">
      <form class="auth-panel" data-testid="register-submit" @submit.prevent="handleRegister">
        <div class="section-band-title compact">
          <div>
            <p class="label">처음 사용자</p>
            <h3>회원가입</h3>
          </div>
        </div>
        <label>
          <span>아이디</span>
          <input
            v-model="registerForm.username"
            autocomplete="username"
            data-testid="register-username"
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
          <span>이메일</span>
          <input
            v-model="registerForm.email"
            autocomplete="email"
            data-testid="register-email"
            maxlength="255"
            required
            type="email"
          />
        </label>
        <label>
          <span>닉네임</span>
          <input
            v-model="registerForm.displayName"
            autocomplete="nickname"
            data-testid="register-display-name"
            maxlength="20"
            minlength="2"
            required
            type="text"
          />
        </label>
        <label>
          <span>비밀번호</span>
          <input
            v-model="registerForm.password"
            autocomplete="new-password"
            data-testid="register-password"
            maxlength="100"
            minlength="8"
            :pattern="passwordPattern"
            required
            title="비밀번호는 영문, 숫자, 특수문자를 모두 포함해야 합니다."
            type="password"
          />
        </label>
        <p class="auth-rule">아이디는 영문·숫자 4-20자, 비밀번호는 영문·숫자·특수문자 포함 8자 이상입니다.</p>
        <p v-if="registerError" class="auth-error" role="alert">{{ registerError }}</p>
        <button class="auth-submit-button" :disabled="registerPending" type="submit">
          {{ registerPending ? '생성 중' : '회원가입' }}
        </button>
        <div class="auth-secondary-actions" aria-label="회원가입 보조 작업">
          <RouterLink data-testid="register-login-link" to="/auth/login">로그인으로 돌아가기</RouterLink>
        </div>
      </form>
    </section>
  </section>
</template>
