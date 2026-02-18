<template>
  <div class="timeline-page" v-loading="loading">
    <div class="page-header">
      <h2>时间线视图</h2>
      <el-select v-model="selectedYear" placeholder="选择年份" clearable @change="fetchTimeline">
        <el-option
          v-for="year in years"
          :key="year"
          :label="`${year}年`"
          :value="year"
        />
      </el-select>
    </div>

    <!-- 时间线 -->
    <div class="timeline">
      <div
        v-for="(laws, month) in sortedTimeline"
        :key="month"
        class="timeline-group"
      >
        <div class="timeline-header" @click="toggleGroup(month)">
          <el-icon class="toggle-icon" :class="{ expanded: expandedGroups.has(month) }">
            <CaretRight />
          </el-icon>
          <span class="month-label">{{ formatMonth(month) }}</span>
          <span class="count-badge">{{ laws.length }} 条</span>
        </div>

        <transition name="expand">
          <div v-show="expandedGroups.has(month)" class="timeline-content">
            <div
              v-for="law in laws"
              :key="law.id"
              class="law-card"
              @click="goToDetail(law.id)"
            >
              <div class="title">{{ law.title }}</div>
              <div class="meta">
                <span>{{ law.category }}</span>
              </div>
            </div>
          </div>
        </transition>
      </div>

      <el-empty v-if="!loading && Object.keys(timeline).length === 0" description="暂无法规数据" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getTimeline } from '../api/laws'

const router = useRouter()

const timeline = ref({})
const years = ref([])
const selectedYear = ref(null)
const loading = ref(false)
const expandedGroups = ref(new Set())

// 排序后的时间线（按月份降序）
const sortedTimeline = computed(() => {
  const sorted = {}
  Object.keys(timeline.value)
    .sort((a, b) => b.localeCompare(a))
    .forEach(key => {
      sorted[key] = timeline.value[key]
    })
  return sorted
})

// 格式化月份
const formatMonth = (monthStr) => {
  if (!monthStr) return ''
  const [year, month] = monthStr.split('-')
  return `${year}年${parseInt(month)}月`
}

// 展开/折叠分组
const toggleGroup = (month) => {
  if (expandedGroups.value.has(month)) {
    expandedGroups.value.delete(month)
  } else {
    expandedGroups.value.add(month)
  }
  // 触发响应式更新
  expandedGroups.value = new Set(expandedGroups.value)
}

// 跳转详情
const goToDetail = (id) => {
  router.push(`/law/${id}`)
}

// 获取时间线数据
const fetchTimeline = async () => {
  loading.value = true
  try {
    const params = {}
    if (selectedYear.value) {
      params.year = selectedYear.value
    }

    const res = await getTimeline(params)
    timeline.value = res.timeline
    years.value = res.years || []

    // 默认展开最近3个月
    const recentMonths = Object.keys(res.timeline)
      .sort((a, b) => b.localeCompare(a))
      .slice(0, 3)
    expandedGroups.value = new Set(recentMonths)
  } catch (error) {
    console.error('获取时间线失败:', error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchTimeline()
})
</script>

<style scoped>
.timeline-page {
  max-width: 1000px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
}

.page-header h2 {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

.timeline {
  min-height: 400px;
}

.timeline-group {
  margin-bottom: 16px;
}

.timeline-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: white;
  border-radius: 8px;
  cursor: pointer;
  box-shadow: var(--shadow-sm);
  transition: background-color 0.2s;
}

.timeline-header:hover {
  background: var(--bg-secondary);
}

.toggle-icon {
  transition: transform 0.2s;
  color: var(--text-secondary);
}

.toggle-icon.expanded {
  transform: rotate(90deg);
}

.month-label {
  font-weight: 500;
  color: var(--text-primary);
}

.count-badge {
  margin-left: auto;
  font-size: 13px;
  color: var(--text-secondary);
  background: var(--bg-secondary);
  padding: 2px 8px;
  border-radius: 10px;
}

.timeline-content {
  margin-top: 8px;
  padding-left: 24px;
  border-left: 2px solid var(--border-color);
  margin-left: 20px;
}

.expand-enter-active,
.expand-leave-active {
  transition: all 0.3s ease;
  overflow: hidden;
}

.expand-enter-from,
.expand-leave-to {
  opacity: 0;
  max-height: 0;
}

.expand-enter-to,
.expand-leave-from {
  opacity: 1;
  max-height: 2000px;
}
</style>
