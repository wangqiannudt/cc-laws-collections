<template>
  <div class="app-container">
    <el-container>
      <!-- 顶部导航 -->
      <el-header class="app-header">
        <div class="header-content">
          <h1 class="app-title" @click="$router.push('/')">法规标准管理系统</h1>
          <div class="header-actions">
            <el-input
              v-model="searchKeyword"
              placeholder="搜索法规..."
              class="search-input"
              @keyup.enter="handleSearch"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
              <template #append>
                <el-button @click="handleSearch">搜索</el-button>
              </template>
            </el-input>
          </div>
        </div>
      </el-header>

      <el-container>
        <!-- 侧边栏 -->
        <el-aside width="220px" class="app-aside">
          <el-menu
            :default-active="activeCategory"
            class="category-menu"
            @select="handleCategorySelect"
          >
            <el-menu-item index="">
              <el-icon><List /></el-icon>
              <span>全部法规</span>
            </el-menu-item>
            <el-menu-item
              v-for="cat in categories"
              :key="cat.code"
              :index="cat.name"
            >
              <el-icon><Folder /></el-icon>
              <span>{{ cat.name }}</span>
            </el-menu-item>
          </el-menu>

          <!-- 快捷操作 -->
          <div class="quick-actions">
            <el-button type="primary" @click="$router.push('/timeline')">
              <el-icon><Clock /></el-icon>
              时间线视图
            </el-button>
            <el-button @click="handleRefresh" :loading="crawling">
              <el-icon><Refresh /></el-icon>
              检查更新
            </el-button>
          </div>
        </el-aside>

        <!-- 主内容区 -->
        <el-main class="app-main">
          <router-view />
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getCategories, startCrawl, getCrawlStatus } from './api/laws'

const router = useRouter()
const route = useRoute()

const searchKeyword = ref('')
const categories = ref([])
const crawling = ref(false)

const activeCategory = computed(() => route.query.category || '')

// 获取分类列表
const fetchCategories = async () => {
  try {
    const res = await getCategories()
    categories.value = res
  } catch (error) {
    console.error('获取分类失败:', error)
  }
}

// 搜索
const handleSearch = () => {
  if (searchKeyword.value.trim()) {
    router.push({
      path: '/search',
      query: { keyword: searchKeyword.value.trim() }
    })
  }
}

// 分类选择
const handleCategorySelect = (category) => {
  if (category) {
    router.push({ path: '/', query: { category } })
  } else {
    router.push('/')
  }
}

// 检查更新
const handleRefresh = async () => {
  if (crawling.value) return

  crawling.value = true
  try {
    const res = await startCrawl()
    ElMessage.success(res.message || '更新完成')
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '更新失败')
  } finally {
    crawling.value = false
  }
}

onMounted(() => {
  fetchCategories()
})
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  background-color: var(--bg-secondary);
  color: var(--text-primary);
}

:root {
  --primary-color: #3b82f6;
  --text-primary: #1f2937;
  --text-secondary: #6b7280;
  --bg-primary: #ffffff;
  --bg-secondary: #f9fafb;
  --border-color: #e5e7eb;
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.07);
}

.app-container {
  min-height: 100vh;
}

.app-header {
  background: var(--bg-primary);
  border-bottom: 1px solid var(--border-color);
  box-shadow: var(--shadow-sm);
  height: auto !important;
  padding: 16px 24px;
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  max-width: 1400px;
  margin: 0 auto;
}

.app-title {
  font-size: 20px;
  font-weight: 600;
  color: var(--primary-color);
  cursor: pointer;
}

.search-input {
  width: 400px;
}

.app-aside {
  background: var(--bg-primary);
  border-right: 1px solid var(--border-color);
  padding: 16px 0;
}

.category-menu {
  border-right: none;
}

.quick-actions {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.quick-actions .el-button {
  width: 100%;
  justify-content: flex-start;
}

.app-main {
  background: var(--bg-secondary);
  min-height: calc(100vh - 72px);
  padding: 24px;
}

/* 法规卡片样式 */
.law-card {
  background: white;
  border-radius: 8px;
  padding: 20px 24px;
  margin-bottom: 12px;
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--border-color);
  transition: box-shadow 0.2s, transform 0.2s;
  cursor: pointer;
}

.law-card:hover {
  box-shadow: var(--shadow-md);
  transform: translateY(-1px);
}

.law-card .title {
  font-size: 16px;
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.law-card .meta {
  font-size: 13px;
  color: var(--text-secondary);
  display: flex;
  gap: 16px;
}

/* 正文排版 */
.law-content {
  font-size: 16px;
  line-height: 1.8;
  color: var(--text-primary);
  max-width: 800px;
}

.law-content p {
  margin-bottom: 1em;
  text-indent: 2em;
}

.law-content h1, .law-content h2, .law-content h3 {
  margin: 1.5em 0 1em;
  text-indent: 0;
}
</style>
