<template>
  <div class="detail-page" v-loading="loading">
    <div v-if="law" class="detail-container">
      <!-- 返回按钮 -->
      <el-button class="back-btn" @click="$router.back()">
        <el-icon><ArrowLeft /></el-icon>
        返回列表
      </el-button>

      <!-- 法规标题 -->
      <h1 class="law-title">{{ law.title }}</h1>

      <!-- 元信息 -->
      <div class="law-meta">
        <span>
          <el-icon><Calendar /></el-icon>
          发布日期: {{ formatDate(law.publish_date) }}
        </span>
        <span>
          <el-icon><Folder /></el-icon>
          分类: {{ law.category }}
        </span>
        <span>
          <el-icon><Link /></el-icon>
          <a :href="law.source_url" target="_blank">查看原文</a>
        </span>
      </div>

      <!-- 正文内容 -->
      <div class="law-content" v-html="law.content"></div>

      <!-- 附件区域 -->
      <div v-if="law.file_url" class="attachment-section">
        <h3>
          <el-icon><Document /></el-icon>
          附件
        </h3>
        <div class="attachment-info">
          <span>{{ getFileName(law.file_url) }}</span>
          <el-button type="primary" size="small" @click="downloadFile">
            <el-icon><Download /></el-icon>
            下载
          </el-button>
        </div>

        <!-- 附件内容 -->
        <div v-if="law.file_content" class="file-content">
          <h4>附件内容预览</h4>
          <pre>{{ law.file_content }}</pre>
        </div>
      </div>

      <!-- 操作按钮 -->
      <div class="actions">
        <el-button @click="handlePrint">
          <el-icon><Printer /></el-icon>
          打印
        </el-button>
      </div>
    </div>

    <el-empty v-else-if="!loading" description="法规不存在" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { getLawDetail } from '../api/laws'

const route = useRoute()
const law = ref(null)
const loading = ref(false)

// 格式化日期
const formatDate = (dateStr) => {
  if (!dateStr) return '未知'
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN')
}

// 获取文件名
const getFileName = (url) => {
  if (!url) return ''
  const parts = url.split('/')
  return parts[parts.length - 1] || '附件'
}

// 下载文件
const downloadFile = () => {
  if (law.value?.file_url) {
    window.open(law.value.file_url, '_blank')
  }
}

// 打印
const handlePrint = () => {
  window.print()
}

// 获取详情
const fetchDetail = async () => {
  loading.value = true
  try {
    const res = await getLawDetail(route.params.id)
    law.value = res
  } catch (error) {
    console.error('获取详情失败:', error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchDetail()
})
</script>

<style scoped>
.detail-page {
  max-width: 900px;
  margin: 0 auto;
}

.detail-container {
  background: white;
  border-radius: 8px;
  padding: 32px 40px;
  box-shadow: var(--shadow-sm);
}

.back-btn {
  margin-bottom: 20px;
}

.law-title {
  font-size: 24px;
  font-weight: 600;
  color: var(--text-primary);
  line-height: 1.4;
  margin-bottom: 16px;
}

.law-meta {
  display: flex;
  gap: 24px;
  font-size: 14px;
  color: var(--text-secondary);
  padding-bottom: 20px;
  border-bottom: 1px solid var(--border-color);
  margin-bottom: 24px;
}

.law-meta span {
  display: flex;
  align-items: center;
  gap: 4px;
}

.law-meta a {
  color: var(--primary-color);
  text-decoration: none;
}

.law-meta a:hover {
  text-decoration: underline;
}

.attachment-section {
  margin-top: 32px;
  padding-top: 24px;
  border-top: 1px solid var(--border-color);
}

.attachment-section h3 {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  margin-bottom: 16px;
}

.attachment-info {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: var(--bg-secondary);
  border-radius: 6px;
}

.file-content {
  margin-top: 16px;
}

.file-content h4 {
  font-size: 14px;
  margin-bottom: 8px;
  color: var(--text-secondary);
}

.file-content pre {
  background: var(--bg-secondary);
  padding: 16px;
  border-radius: 6px;
  font-size: 13px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-wrap: break-word;
  max-height: 400px;
  overflow-y: auto;
}

.actions {
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid var(--border-color);
}

@media print {
  .back-btn, .actions {
    display: none;
  }

  .detail-container {
    box-shadow: none;
    padding: 0;
  }
}
</style>
