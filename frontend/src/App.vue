<template>
  <div class="app-container">
    <el-container>
      <!-- 顶部导航 -->
      <el-header class="app-header">
        <div class="header-content">
          <h1 class="app-title" @click="$router.push('/')">国家军队采购法规管理系统</h1>
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
  --primary-color: #1e40af;
  --primary-light: #3b82f6;
  --primary-dark: #1e3a8a;
  --text-primary: #1e293b;
  --text-secondary: #64748b;
  --bg-primary: #ffffff;
  --bg-secondary: #f8fafc;
  --border-color: #e2e8f0;
  --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.06);
  --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.08);
  --shadow-lg: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.app-container {
  min-height: 100vh;
}

.app-header {
  background: linear-gradient(135deg, var(--primary-color) 0%, var(--primary-dark) 100%);
  border-bottom: none;
  box-shadow: var(--shadow-md);
  height: auto !important;
  padding: 16px 32px;
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  max-width: 1400px;
  margin: 0 auto;
}

.app-title {
  font-size: 22px;
  font-weight: 600;
  color: #ffffff;
  cursor: pointer;
  letter-spacing: 0.5px;
}

.search-input {
  width: 400px;
}

.search-input :deep(.el-input__wrapper) {
  background: rgba(255, 255, 255, 0.95);
  border: none;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.search-input :deep(.el-input-group__append) {
  background: var(--primary-light);
  border: none;
  box-shadow: none;
}

.search-input :deep(.el-input-group__append .el-button) {
  color: #ffffff;
}

.app-aside {
  background: var(--bg-primary);
  border-right: 1px solid var(--border-color);
  padding: 20px 0;
}

.category-menu {
  border-right: none;
}

.category-menu :deep(.el-menu-item) {
  height: 48px;
  line-height: 48px;
  margin: 4px 12px;
  border-radius: 8px;
  transition: all 0.2s;
}

.category-menu :deep(.el-menu-item:hover) {
  background: var(--bg-secondary);
}

.category-menu :deep(.el-menu-item.is-active) {
  background: var(--primary-color);
  color: #ffffff;
}

.quick-actions {
  padding: 20px 16px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  border-top: 1px solid var(--border-color);
  margin-top: 16px;
}

.quick-actions .el-button {
  width: 100%;
  justify-content: flex-start;
  border-radius: 8px;
  height: 40px;
}

.app-main {
  background: var(--bg-secondary);
  min-height: calc(100vh - 72px);
  padding: 24px;
}

/* 法规卡片样式 */
.law-card {
  background: white;
  border-radius: 12px;
  padding: 24px 28px;
  margin-bottom: 16px;
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--border-color);
  transition: all 0.25s ease;
  cursor: pointer;
}

.law-card:hover {
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
  border-color: var(--primary-light);
}

.law-card .title {
  font-size: 17px;
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: 10px;
  line-height: 1.5;
}

.law-card .meta {
  font-size: 13px;
  color: var(--text-secondary);
  display: flex;
  gap: 20px;
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
