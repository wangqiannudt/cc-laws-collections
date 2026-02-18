<template>
  <div class="search-page">
    <!-- 搜索结果标题 -->
    <div class="page-header">
      <h2>搜索结果</h2>
      <span class="keyword">关键词: "{{ keyword }}"</span>
      <span class="total-count">共 {{ total }} 条</span>
    </div>

    <!-- 搜索结果列表 -->
    <div class="law-list" v-loading="loading">
      <div
        v-for="law in laws"
        :key="law.id"
        class="law-card"
        @click="goToDetail(law.id)"
      >
        <div class="title" v-html="highlightKeyword(law.title)"></div>
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
        <div class="snippet" v-if="law.content">
          {{ getSnippet(law.content) }}
        </div>
      </div>

      <el-empty v-if="!loading && laws.length === 0" description="未找到相关法规" />
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
import { searchLaws } from '../api/laws'

const route = useRoute()
const router = useRouter()

const laws = ref([])
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const keyword = ref('')

// 格式化日期
const formatDate = (dateStr) => {
  if (!dateStr) return '未知日期'
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN')
}

// 高亮关键词
const highlightKeyword = (text) => {
  if (!keyword.value || !text) return text
  const regex = new RegExp(`(${keyword.value})`, 'gi')
  return text.replace(regex, '<mark>$1</mark>')
}

// 获取摘要
const getSnippet = (content) => {
  if (!content) return ''
  // 移除 HTML 标签
  const text = content.replace(/<[^>]+>/g, '').replace(/\s+/g, ' ')
  // 查找关键词位置
  const lowerText = text.toLowerCase()
  const lowerKeyword = keyword.value.toLowerCase()
  const index = lowerText.indexOf(lowerKeyword)

  if (index === -1) {
    return text.slice(0, 150) + (text.length > 150 ? '...' : '')
  }

  const start = Math.max(0, index - 50)
  const end = Math.min(text.length, index + keyword.value.length + 100)
  let snippet = text.slice(start, end)
  if (start > 0) snippet = '...' + snippet
  if (end < text.length) snippet = snippet + '...'
  return snippet
}

// 搜索法规
const search = async () => {
  if (!keyword.value) return

  loading.value = true
  try {
    const res = await searchLaws(keyword.value, {
      page: currentPage.value,
      page_size: pageSize.value,
    })
    laws.value = res.items
    total.value = res.total
  } catch (error) {
    console.error('搜索失败:', error)
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
  search()
}

// 监听路由变化
watch(() => route.query.keyword, (newKeyword) => {
  if (newKeyword) {
    keyword.value = newKeyword
    currentPage.value = 1
    search()
  }
})

onMounted(() => {
  if (route.query.keyword) {
    keyword.value = route.query.keyword
    search()
  }
})
</script>

<style scoped>
.search-page {
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

.keyword {
  font-size: 14px;
  color: var(--text-secondary);
}

.total-count {
  font-size: 14px;
  color: var(--text-secondary);
}

.snippet {
  font-size: 13px;
  color: var(--text-secondary);
  margin-top: 8px;
  line-height: 1.6;
}

.snippet :deep(mark) {
  background-color: #fef3c7;
  padding: 0 2px;
  border-radius: 2px;
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
