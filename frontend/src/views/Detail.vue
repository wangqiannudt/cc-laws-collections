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
      <div class="law-content" v-html="displayContent"></div>

      <!-- 附件区域（正文较短且有附件内容时不显示预览） -->
      <div v-if="law.file_url || law.file_path" class="attachment-section">
        <h3>
          <el-icon><Document /></el-icon>
          附件
        </h3>
        <div class="attachment-info">
          <span>{{ getFileName(law.file_path || law.file_url) }}</span>
          <el-button type="primary" size="small" @click="downloadFile">
            <el-icon><Download /></el-icon>
            下载
          </el-button>
        </div>

        <!-- 附件内容预览（仅当正文较长时显示） -->
        <div v-if="!hasShortContent && law.file_content" class="file-content">
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
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { getLawDetail } from '../api/laws'

const route = useRoute()
const law = ref(null)
const loading = ref(false)

// 判断正文是否较短
const hasShortContent = computed(() => {
  if (!law.value?.content) return true
  // 去除 HTML 标签后的纯文本长度
  const text = law.value.content.replace(/<[^>]+>/g, '').trim()
  return text.length < 200
})

// 实际显示的内容（正文较短时用附件内容替代）
const displayContent = computed(() => {
  if (!law.value) return ''
  if (hasShortContent.value && law.value.file_content) {
    // 将附件纯文本转换为 HTML 段落
    return law.value.file_content
      .split('\n')
      .filter(line => line.trim())
      .map(line => `<p>${line}</p>`)
      .join('')
  }
  return law.value.content || ''
})

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
  if (law.value?.file_path) {
    // 使用本地下载 API
    window.open(`/api/laws/${law.value.id}/download`, '_blank')
  } else if (law.value?.file_url) {
    // 降级到原始链接
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
  max-width: 960px;
  margin: 0 auto;
}

.detail-container {
  background: white;
  border-radius: 12px;
  padding: 40px 48px;
  box-shadow: var(--shadow-md);
}

.back-btn {
  margin-bottom: 24px;
  border-radius: 8px;
}

.law-title {
  font-size: 26px;
  font-weight: 600;
  color: var(--primary-color);
  line-height: 1.5;
  margin-bottom: 20px;
  padding-bottom: 20px;
  border-bottom: 2px solid var(--border-color);
}

.law-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 24px;
  font-size: 14px;
  color: var(--text-secondary);
  padding-bottom: 20px;
  margin-bottom: 24px;
  border-bottom: 1px solid var(--border-color);
}

.law-meta span {
  display: flex;
  align-items: center;
  gap: 6px;
}

.law-meta a {
  color: var(--primary-color);
  text-decoration: none;
  font-weight: 500;
}

.law-meta a:hover {
  text-decoration: underline;
}

.law-content {
  font-size: 16px;
  line-height: 2;
  color: var(--text-primary);
}

.law-content :deep(p) {
  margin-bottom: 1.2em;
  text-indent: 2em;
  text-align: justify;
}

.law-content :deep(h1),
.law-content :deep(h2),
.law-content :deep(h3) {
  margin: 1.8em 0 1em;
  text-indent: 0;
  font-weight: 600;
  color: var(--text-primary);
}

.law-content :deep(h2) {
  font-size: 18px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border-color);
}

.attachment-section {
  margin-top: 40px;
  padding: 24px;
  background: var(--bg-secondary);
  border-radius: 10px;
}

.attachment-section h3 {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  margin-bottom: 16px;
  color: var(--primary-color);
}

.attachment-info {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 18px;
  background: white;
  border-radius: 8px;
  border: 1px solid var(--border-color);
}

.attachment-info span {
  font-size: 14px;
  color: var(--text-primary);
  font-weight: 500;
}

.file-content {
  margin-top: 20px;
}

.file-content h4 {
  font-size: 14px;
  margin-bottom: 12px;
  color: var(--text-secondary);
  font-weight: 500;
}

.file-content pre {
  background: white;
  padding: 20px;
  border-radius: 8px;
  font-size: 14px;
  line-height: 1.8;
  white-space: pre-wrap;
  word-wrap: break-word;
  max-height: 500px;
  overflow-y: auto;
  border: 1px solid var(--border-color);
}

.actions {
  margin-top: 32px;
  padding-top: 24px;
  border-top: 1px solid var(--border-color);
  display: flex;
  gap: 12px;
}

.actions .el-button {
  border-radius: 8px;
}

@media print {
  .back-btn, .actions {
    display: none;
  }

  .detail-container {
    box-shadow: none;
    padding: 0;
  }

  .law-meta {
    background: none;
    padding: 0 0 16px 0;
  }

  .attachment-section {
    background: none;
    padding: 0;
  }
}
</style>
