<script setup lang="ts">
const usernamePattern = '[A-Za-z0-9]+';
</script>

<template>
  <section class="surface-page auth-page" aria-labelledby="find-account-title">
    <div class="auth-header">
      <p class="label">계정</p>
      <h2 id="find-account-title">ID/PW 찾기</h2>
      <span>가입한 이메일과 아이디 기준으로 계정 복구를 요청합니다.</span>
    </div>

    <section class="auth-grid" aria-label="ID와 PW 찾기">
      <form class="auth-panel">
        <div class="section-band-title compact">
          <div>
            <p class="label">아이디 확인</p>
            <h3>ID 찾기</h3>
          </div>
        </div>
        <label>
          <span>가입 이메일</span>
          <input
            autocomplete="email"
            data-testid="find-id-email"
            maxlength="255"
            required
            type="email"
          />
        </label>
        <button class="auth-submit-button" disabled type="submit">확인 요청</button>
      </form>

      <form class="auth-panel">
        <div class="section-band-title compact">
          <div>
            <p class="label">비밀번호 확인</p>
            <h3>PW 찾기</h3>
          </div>
        </div>
        <label>
          <span>아이디</span>
          <input
            autocomplete="username"
            data-testid="find-password-username"
            inputmode="text"
            maxlength="20"
            minlength="4"
            :pattern="usernamePattern"
            required
            type="text"
          />
        </label>
        <label>
          <span>가입 이메일</span>
          <input
            autocomplete="email"
            data-testid="find-password-email"
            maxlength="255"
            required
            type="email"
          />
        </label>
        <button class="auth-submit-button" disabled type="submit">재설정 요청</button>
      </form>
    </section>

    <div class="auth-bottom-link">
      <RouterLink data-testid="find-login-link" to="/auth/login">로그인으로 돌아가기</RouterLink>
    </div>
  </section>
</template>
