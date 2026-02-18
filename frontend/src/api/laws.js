import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

// 获取法规列表
export const getLaws = (params = {}) => {
  return api.get('/laws', { params }).then(res => res.data)
}

// 获取法规详情
export const getLawDetail = (id) => {
  return api.get(`/laws/${id}`).then(res => res.data)
}

// 搜索法规
export const searchLaws = (keyword, params = {}) => {
  return api.get('/laws/search', { params: { keyword, ...params } }).then(res => res.data)
}

// 获取时间线
export const getTimeline = (params = {}) => {
  return api.get('/laws/timeline', { params }).then(res => res.data)
}

// 获取分类列表
export const getCategories = () => {
  return api.get('/categories').then(res => res.data)
}

// 获取爬取状态
export const getCrawlStatus = () => {
  return api.get('/crawl/status').then(res => res.data)
}

// 触发爬取
export const startCrawl = (category = null) => {
  const params = category ? { category } : {}
  return api.post('/crawl/start', null, { params }).then(res => res.data)
}
