<template>
  <nav class="stepper-timeline" aria-label="Progress">
    <div
      v-for="(step, index) in steps"
      :key="step.value"
      class="stepper-timeline__item"
      :class="{ 
        'is-active': activeValue === step.value, 
        'is-completed': isStepCompleted(index),
        'is-disabled': step.disabled,
        'is-processing': step.value === 'processing' && activeValue === 'processing'
      }"
      @click="handleStepClick(step)"
    >
      <!-- 连接线 -->
      <div v-if="index < steps.length - 1" class="stepper-timeline__line"></div>

      <!-- 步骤节点 -->
      <div class="stepper-timeline__node">
        <div class="stepper-timeline__dot">
          <el-icon v-if="isStepCompleted(index) || step.icon"><component :is="isStepCompleted(index) ? Check : step.icon" /></el-icon>
          <span v-else>{{ index + 1 }}</span>
        </div>
        
        <div class="stepper-timeline__content">
          <span class="stepper-timeline__label">{{ step.label }}</span>
          <span v-if="step.subLabel" class="stepper-timeline__sub">{{ step.subLabel }}</span>
        </div>
      </div>
    </div>
  </nav>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { Check } from '@element-plus/icons-vue';

interface Step {
  label: string;
  value: string;
  subLabel?: string;
  icon?: any;
  disabled?: boolean;
}

const props = defineProps<{
  steps: Step[];
  activeValue: string;
}>();

const emit = defineEmits<{
  (e: 'change', value: string): void;
}>();

const activeIndex = computed(() => 
  props.steps.findIndex(s => s.value === props.activeValue)
);

const isStepCompleted = (index: number) => {
  return index < activeIndex.value;
};

const handleStepClick = (step: Step) => {
  if (step.disabled) return;
  emit('change', step.value);
};
</script>

<style scoped>
.stepper-timeline {
  display: flex;
  align-items: flex-start;
  margin: 32px 0 40px;
  padding: 0;
  position: relative;
}

.stepper-timeline__item {
  position: relative;
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  cursor: pointer;
  transition: all 0.3s ease;
}

/* 连接线 */
.stepper-timeline__line {
  position: absolute;
  top: 16px;
  left: 50%;
  width: 100%;
  height: 2px;
  background: var(--line);
  z-index: 1;
  transition: background-color 0.3s ease;
}

.stepper-timeline__item.is-completed .stepper-timeline__line {
  background: var(--safe);
}

/* 节点容器 */
.stepper-timeline__node {
  position: relative;
  z-index: 2;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  width: 100%;
}

/* 圆点 */
.stepper-timeline__dot {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--panel-strong);
  border: 2px solid var(--line);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 700;
  color: var(--muted);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  margin-bottom: 12px;
}

.stepper-timeline__item.is-processing .stepper-timeline__dot {
  border-color: var(--warn);
  color: var(--warn);
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0% { box-shadow: 0 0 0 0 rgba(138, 100, 20, 0.4); transform: rotate(0deg); }
  70% { box-shadow: 0 0 0 10px rgba(138, 100, 20, 0); transform: rotate(252deg); }
  100% { box-shadow: 0 0 0 0 rgba(138, 100, 20, 0); transform: rotate(360deg); }
}

.stepper-timeline__item.is-active .stepper-timeline__dot {
  border-color: var(--ink);
  color: var(--ink);
  transform: scale(1.1);
  box-shadow: 0 0 0 4px rgba(0, 0, 0, 0.05);
}

.stepper-timeline__item.is-completed .stepper-timeline__dot {
  background: var(--safe);
  border-color: var(--safe);
  color: white;
}

/* 内容 */
.stepper-timeline__content {
  display: flex;
  flex-direction: column;
  gap: 4px;
  max-width: 120px;
}

.stepper-timeline__label {
  font-size: 14px;
  font-weight: 600;
  color: var(--muted);
  transition: color 0.3s ease;
}

.stepper-timeline__item.is-active .stepper-timeline__label {
  color: var(--ink);
}

.stepper-timeline__sub {
  font-size: 12px;
  color: var(--muted);
  opacity: 0.8;
}

/* 悬停效果 */
.stepper-timeline__item:hover:not(.is-disabled) .stepper-timeline__dot {
  border-color: var(--ink);
}

.stepper-timeline__item:hover:not(.is-disabled) .stepper-timeline__label {
  color: var(--ink);
}

/* 禁用状态 */
.stepper-timeline__item.is-disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

/* 响应式适配 */
@media (max-width: 780px) {
  .stepper-timeline {
    flex-direction: column;
    align-items: flex-start;
    gap: 24px;
    padding-left: 40px;
  }

  .stepper-timeline__item {
    flex: none;
    width: 100%;
    flex-direction: row;
    align-items: flex-start;
  }

  .stepper-timeline__line {
    top: 32px;
    left: 16px;
    bottom: -24px;
    width: 2px;
    height: auto;
    right: auto;
  }

  .stepper-timeline__node {
    flex-direction: row;
    text-align: left;
    gap: 16px;
  }

  .stepper-timeline__dot {
    margin-bottom: 0;
    flex-shrink: 0;
  }

  .stepper-timeline__content {
    max-width: none;
  }
}
</style>
