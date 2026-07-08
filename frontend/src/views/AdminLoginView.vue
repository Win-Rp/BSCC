<template>
  <div class="admin-login-container">
    <el-card class="admin-login-card" shadow="hover">
      <div class="login-header">
        <h2>{{ adminPanelTitle }}</h2>
        <p>{{ translateText("登录后可管理订单、任务和日志数据") }}</p>
      </div>

      <el-form
        ref="loginFormRef"
        :model="loginForm"
        :rules="loginRules"
        label-position="top"
        @keyup.enter="handleLogin"
      >
        <el-form-item :label="translateText('账号')" prop="username">
          <el-input
            v-model="loginForm.username"
            :placeholder="translateText('请输入管理员账号')"
            :prefix-icon="User"
          />
        </el-form-item>

        <el-form-item :label="translateText('密码')" prop="password">
          <el-input
            v-model="loginForm.password"
            type="password"
            :placeholder="translateText('请输入管理员密码')"
            :prefix-icon="Lock"
            show-password
          />
        </el-form-item>

        <div class="login-tips">
          <el-icon><InfoFilled /></el-icon>
          <span>{{ translateText("后台操作默认写入审计日志，退出后需重新鉴权。") }}</span>
        </div>

        <el-form-item>
          <el-button
            type="primary"
            class="login-btn"
            :loading="loading"
            @click="handleLogin"
          >
            {{ translateText("登 录") }}
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import type { FormInstance, FormRules } from 'element-plus';
import { User, Lock, InfoFilled } from '@element-plus/icons-vue';
import { adminLogin, getPublicSiteConfig } from '@/services/api';
import { applyRouteSeo } from '@/utils/seo';
import { useAppI18n } from '@/composables/useAppI18n';

const { translateText } = useAppI18n();
const router = useRouter();
const loginFormRef = ref<FormInstance>();
const loading = ref(false);
const siteTitle = ref('标书查重系统');
const adminPanelTitle = computed(() => `${(siteTitle.value || translateText("标书查重系统")).trim()} ${translateText("运营后台")}`);

const loginForm = reactive({
  username: '',
  password: ''
});

const loginRules = reactive<FormRules>({
  username: [{ required: true, message: translateText('请输入账号'), trigger: 'blur' }],
  password: [{ required: true, message: translateText('请输入密码'), trigger: 'blur' }]
});

onMounted(async () => {
  try {
    const siteConfig = await getPublicSiteConfig();
    if (siteConfig?.site_title) {
      siteTitle.value = siteConfig.site_title;
    }
  } catch {
    // 保持默认标题即可
  }
});

watch(
  adminPanelTitle,
  (value) => {
    applyRouteSeo(
      {
        title: value,
        description: translateText('网站运营后台登录入口。'),
        robots: 'noindex,nofollow'
      },
      { currentPath: '/admin/login' }
    );
  },
  { immediate: true }
);

const handleLogin = async () => {
  if (!loginFormRef.value) return;
  
  await loginFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true;
      try {
        const res = await adminLogin(loginForm.username, loginForm.password);
        // 保存 token
        localStorage.setItem('admin_token', res.token);
        localStorage.setItem('admin_username', res.username);
        
        ElMessage.success(translateText('登录成功'));
        router.push('/admin');
      } catch (error) {
        ElMessage.error(error instanceof Error ? error.message : translateText('登录失败，请检查账号密码'));
      } finally {
        loading.value = false;
      }
    }
  });
};
</script>

<style scoped>
.admin-login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background-color: var(--background);
}

.admin-login-card {
  width: 100%;
  max-width: 420px;
  border-radius: 12px;
  box-shadow: var(--shadow);
  border: 1px solid var(--line);
}

.login-header {
  text-align: center;
  margin-bottom: 32px;
}

.login-header h2 {
  margin: 0 0 8px 0;
  font-size: 24px;
  color: var(--ink);
}

.login-header p {
  margin: 0;
  font-size: 14px;
  color: var(--muted);
}

.login-tips {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 12px;
  background-color: var(--panel);
  border-radius: 8px;
  margin-bottom: 24px;
  font-size: 12px;
  color: var(--muted);
}

.login-btn {
  width: 100%;
  height: 40px;
  font-size: 16px;
  border-radius: 8px;
  background: var(--ink);
  border-color: var(--ink);
}

.login-btn:hover {
  background: #333;
  border-color: #333;
}
</style><template>
  <div class="admin-login-container">
    <el-card class="admin-login-card" shadow="hover">
      <div class="login-header">
        <h2>{{ adminPanelTitle }}</h2>
        <p>登录后可管理订单、任务和日志数据</p>
      </div>

      <el-form
        ref="loginFormRef"
        :model="loginForm"
        :rules="loginRules"
        label-position="top"
        @keyup.enter="handleLogin"
      >
        <el-form-item label="账号" prop="username">
          <el-input
            v-model="loginForm.username"
            placeholder="请输入管理员账号"
            :prefix-icon="User"
          />
        </el-form-item>

        <el-form-item label="密码" prop="password">
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="请输入管理员密码"
            :prefix-icon="Lock"
            show-password
          />
        </el-form-item>

        <div class="login-tips">
          <el-icon><InfoFilled /></el-icon>
          <span>后台操作默认写入审计日志，退出后需重新鉴权。</span>
        </div>

        <el-form-item>
          <el-button
            type="primary"
            class="login-btn"
            :loading="loading"
            @click="handleLogin"
          >
            登 录
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import type { FormInstance, FormRules } from 'element-plus';
import { User, Lock, InfoFilled } from '@element-plus/icons-vue';
import { adminLogin, getPublicSiteConfig } from '@/services/api';
import { applyRouteSeo } from '@/utils/seo';

const router = useRouter();
const loginFormRef = ref<FormInstance>();
const loading = ref(false);
const siteTitle = ref('标书查重系统');
const adminPanelTitle = computed(() => `${(siteTitle.value || '标书查重系统').trim()} 运营后台`);

const loginForm = reactive({
  username: '',
  password: ''
});

const loginRules = reactive<FormRules>({
  username: [{ required: true, message: '请输入账号', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
});

onMounted(async () => {
  try {
    const siteConfig = await getPublicSiteConfig();
    if (siteConfig?.site_title) {
      siteTitle.value = siteConfig.site_title;
    }
  } catch {
    // 保持默认标题即可
  }
});

watch(
  adminPanelTitle,
  (value) => {
    applyRouteSeo(
      {
        title: value,
        description: '网站运营后台登录入口。',
        robots: 'noindex,nofollow'
      },
      { currentPath: '/admin/login' }
    );
  },
  { immediate: true }
);

const handleLogin = async () => {
  if (!loginFormRef.value) return;
  
  await loginFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true;
      try {
        const res = await adminLogin(loginForm.username, loginForm.password);
        // 保存 token
        localStorage.setItem('admin_token', res.token);
        localStorage.setItem('admin_username', res.username);
        
        ElMessage.success('登录成功');
        router.push('/admin');
      } catch (error) {
        ElMessage.error(error instanceof Error ? error.message : '登录失败，请检查账号密码');
      } finally {
        loading.value = false;
      }
    }
  });
};
</script>

<style scoped>
.admin-login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background-color: var(--background);
}

.admin-login-card {
  width: 100%;
  max-width: 420px;
  border-radius: 12px;
  box-shadow: var(--shadow);
  border: 1px solid var(--line);
}

.login-header {
  text-align: center;
  margin-bottom: 32px;
}

.login-header h2 {
  margin: 0 0 8px 0;
  font-size: 24px;
  color: var(--ink);
}

.login-header p {
  margin: 0;
  font-size: 14px;
  color: var(--muted);
}

.login-tips {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 12px;
  background-color: var(--panel);
  border-radius: 8px;
  margin-bottom: 24px;
  font-size: 12px;
  color: var(--muted);
}

.login-btn {
  width: 100%;
  height: 40px;
  font-size: 16px;
  border-radius: 8px;
  background: var(--ink);
  border-color: var(--ink);
}

.login-btn:hover {
  background: #333;
  border-color: #333;
}
</style>
