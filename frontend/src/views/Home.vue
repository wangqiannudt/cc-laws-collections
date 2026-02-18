<template>
  <div class="home-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <h2>{{ currentCategory || '全部法规' }}</h2>
      <span class="total-count">共 {{ total }} 条</span>
    </div>

    <!-- 法规列表 -->
    <div class="law-list" v-loading="loading">
      <div
        v-for="law in laws"
        :key="law.id"
        class="law-card"
        @click="goToDetail(law.id)"
      >
        <div class="title">{{ law.title }}</div>
        <div class="meta">
          <span>
            <el-icon><Calendar /></el-icon>
            {{ formatDate(law.publish_date) }}
          </span>
          <span>
            <el-icon><Folder /></el-icon>
            {{ law.category }}
          </span>
        </div>
      </div>

      <el-empty v-if="!loading && laws.length === 0" description="暂无法规数据" />
    </div>

    <!-- 分页 -->
    <div class="pagination-wrapper" v-if="total > 0">
      <el-pagination
        v-model:current-page="currentPage"
        :page-size="pageSize"
        :total="total"
        layout="prev, pager, next, total"
        @current-change="handlePageChange"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getLaws } from '../api/laws'

const route = useRoute()
const router = useRouter()

const laws = ref([])
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

const currentCategory = ref('')

// 格式化日期
const formatDate = (dateStr) => {
  if (!dateStr) return '未知日期'
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN')
}

// 获取法规列表
const fetchLaws = async () => {
  loading.value = true
  try {
    const params = {
      page: currentPage.value,
      page_size: pageSize.value,
    }

    if (route.query.category) {
      params.category = route.query.category
      currentCategory.value = route.query.category
    } else {
      currentCategory.value = ''
    }

    const res = await getLaws(params)
    laws.value = res.items
    total.value = res.total
  } catch (error) {
    console.error('获取法规列表失败:', error)
  } finally {
    loading.value = false
  }
}

// 跳转详情
const goToDetail = (id) => {
  router.push(`/law/${id}`)
}

// 分页变化
const handlePageChange = (page) => {
  currentPage.value = page
  fetchLaws()
}

// 监听路由变化
watch(() => route.query.category, () => {
  currentPage.value = 1
  fetchLaws()
})

onMounted(() => {
  fetchLaws()
})
</script>

<style scoped>
.home-page {
  max-width: 1000px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  align-items: baseline;
  gap: 12px;
  margin-bottom: 20px;
}

.page-header h2 {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

.total-count {
  font-size: 14px;
  color: var(--text-secondary);
}

.law-list {
  min-height: 400px;
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 24px;
  padding: 16px 0;
}
</style>
