<template>
  <div class="detail" v-if="deviation">
    <!-- 返回按钮 -->
    <button class="back-btn" @click="$router.push('/')">← 返回列表</button>

    <!-- 基本信息卡片 -->
    <div class="info-card">
      <div class="info-header">
        <div>
          <span class="code">{{ deviation.code }}</span>
          <h2>{{ deviation.title }}</h2>
        </div>
        <div class="info-actions">
          <select v-model="deviation.status" @change="updateField('status', deviation.status)" class="status-select">
            <option>待处理</option>
            <option>调查中</option>
            <option>待审批</option>
            <option>已完成</option>
          </select>
        </div>
      </div>

      <div class="info-grid">
        <div class="info-item">
          <label>分类</label>
          <span v-if="!editingCategory" :class="['tag', deviation.category]">{{ deviation.category || '未分类' }}</span>
          <select v-else v-model="deviation.category" @change="updateField('category', deviation.category)" class="inline-edit">
            <option value="设备故障">设备故障</option>
            <option value="物料问题">物料问题</option>
            <option value="操作失误">操作失误</option>
            <option value="系统偏差">系统偏差</option>
            <option value="其他">其他</option>
          </select>
        </div>
        <div class="info-item">
          <label>优先级</label>
          <span :class="['priority', `p-${deviation.priority}`]">{{ deviation.priority || '—' }}</span>
        </div>
        <div class="info-item">
          <label>严重程度</label>
          <span>{{ deviation.severity || '—' }}</span>
        </div>
        <div class="info-item">
          <label>创建时间</label>
          <span>{{ formatDate(deviation.created_at) }}</span>
        </div>
      </div>

      <div class="description-block">
        <label>偏差描述</label>
        <textarea v-model="deviation.description" @blur="updateField('description', deviation.description)" rows="4" placeholder="请描述偏差详情..."></textarea>
      </div>
    </div>

    <!-- AI 操作区 -->
    <div class="ai-section">
      <div class="section-title">🤖 AI 智能辅助</div>
      <div class="ai-buttons">
        <button class="ai-btn" @click="runClassify" :disabled="aiLoading">
          <span class="ai-icon">🏷️</span>
          <div>
            <div class="ai-btn-title">智能分类</div>
            <div class="ai-btn-desc">AI 自动判断类别、优先级、严重程度</div>
          </div>
        </button>
        <button class="ai-btn" @click="runRootCause" :disabled="aiLoading">
          <span class="ai-icon">🔍</span>
          <div>
            <div class="ai-btn-title">根因分析 (5 Why)</div>
            <div class="ai-btn-desc">AI 引导式分析，推导根本原因并给出 CAPA</div>
          </div>
        </button>
        <button class="ai-btn" @click="runReport" :disabled="aiLoading">
          <span class="ai-icon">📋</span>
          <div>
            <div class="ai-btn-title">生成报告</div>
            <div class="ai-btn-desc">生成符合 GMP 格式的偏差调查报告</div>
          </div>
        </button>
      </div>
      <div v-if="aiLoading" class="ai-loading">
        <div class="spinner"></div>
        <span>AI 分析中，请稍候...</span>
      </div>
      <div v-if="aiError" class="ai-error">{{ aiError }}</div>
    </div>

    <!-- 根因分析结果 -->
    <div v-if="rootCauseResult" class="result-card">
      <div class="result-header">
        <span class="result-title">🔍 根因分析结果</span>
        <button class="apply-btn" @click="applyRootCause">应用到此记录</button>
      </div>
      <div class="markdown-content" v-html="renderMarkdown(rootCauseResult)"></div>
    </div>

    <!-- 分类结果 -->
    <div v-if="classifyResult" class="result-card">
      <div class="result-header">
        <span class="result-title">🏷️ 智能分类结果</span>
        <button class="apply-btn" @click="applyClassify">应用到此记录</button>
      </div>
      <div class="classify-result">
        <div class="classify-item"><span>分类</span><strong>{{ classifyResult.category }}</strong></div>
        <div class="classify-item"><span>优先级</span><strong>{{ classifyResult.priority }}</strong></div>
        <div class="classify-item"><span>严重程度</span><strong>{{ classifyResult.severity }}</strong></div>
        <div class="classify-item" style="grid-column: 1/-1;"><span>理由</span><em>{{ classifyResult.reason }}</em></div>
      </div>
    </div>

    <!-- 偏差报告预览 -->
    <div v-if="reportContent" class="result-card">
      <div class="result-header">
        <span class="result-title">📋 GMP 偏差报告</span>
        <button class="apply-btn" @click="downloadReport">下载 Markdown</button>
      </div>
      <div class="markdown-content" v-html="renderMarkdown(reportContent)"></div>
    </div>

    <!-- 根本原因 & CAPA 编辑区 -->
    <div class="edit-card">
      <div class="edit-row">
        <label>根本原因</label>
        <textarea v-model="deviation.root_cause" @blur="updateField('root_cause', deviation.root_cause)" rows="4" placeholder="记录根本原因分析结果..."></textarea>
      </div>
      <div class="edit-row">
        <label>CAPA（纠正预防措施）</label>
        <textarea v-model="deviation.capa" @blur="updateField('capa', deviation.capa)" rows="4" placeholder="记录纠正和预防措施..."></textarea>
      </div>
    </div>
  </div>
  <div v-else class="loading">加载中...</div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'
import { marked } from 'marked'

const route = useRoute()
const router = useRouter()
const deviation = ref(null)
const aiLoading = ref(false)
const aiError = ref('')
const classifyResult = ref('')
const rootCauseResult = ref('')
const reportContent = ref('')

async function loadDeviation() {
  try {
    const res = await axios.get(`/api/deviations/${route.params.id}`)
    deviation.value = res.data
  } catch {
    router.push('/')
  }
}

async function updateField(field, value) {
  try {
    await axios.put(`/api/deviations/${deviation.value.id}`, { [field]: value })
  } catch (err) {
    console.error(err)
  }
}

async function runClassify() {
  aiLoading.value = true
  aiError.value = ''
  try {
    const res = await axios.post(`/api/deviations/${deviation.value.id}/classify`)
    classifyResult.value = res.data
    deviation.value.category = res.data.category
    deviation.value.priority = res.data.priority
    deviation.value.severity = res.data.severity
  } catch (err) {
    aiError.value = err.response?.data?.detail || '分类失败，请确认 Ollama 已启动'
  } finally {
    aiLoading.value = false
  }
}

async function runRootCause() {
  aiLoading.value = true
  aiError.value = ''
  try {
    const res = await axios.post(`/api/deviations/${deviation.value.id}/root-cause`)
    rootCauseResult.value = res.data.analysis
  } catch (err) {
    aiError.value = err.response?.data?.detail || '根因分析失败'
  } finally {
    aiLoading.value = false
  }
}

async function runReport() {
  aiLoading.value = true
  aiError.value = ''
  try {
    const res = await axios.post(`/api/deviations/${deviation.value.id}/report`)
    reportContent.value = res.data.report
  } catch (err) {
    aiError.value = err.response?.data?.detail || '报告生成失败'
  } finally {
    aiLoading.value = false
  }
}

function applyClassify() {
  if (classifyResult.value) {
    deviation.value.category = classifyResult.value.category
    deviation.value.priority = classifyResult.value.priority
    deviation.value.severity = classifyResult.value.severity
    updateField('category', classifyResult.value.category)
    updateField('priority', classifyResult.value.priority)
    updateField('severity', classifyResult.value.severity)
  }
}

function applyRootCause() {
  // 简单解析：找 "根本原因总结" 之后的文本作为根本原因，"建议的 CAPA" 之后的文本作为 CAPA
  if (!rootCauseResult.value) return
  const text = rootCauseResult.value
  
  let rootCause = ''
  let capa = ''
  
  const rcMatch = text.match(/根本原因总结\s*[\n\r]+([\s\S]+?)(?=## |$)/)
  if (rcMatch) rootCause = rcMatch[1].trim()
  
  const capaMatch = text.match(/建议的 CAPA\s*[\n\r]+([\s\S]+?)(?=## |$)/)
  if (capaMatch) capa = capaMatch[1].trim()
  
  deviation.value.root_cause = rootCause
  deviation.value.capa = capa
  updateField('root_cause', rootCause)
  updateField('capa', capa)
}

function downloadReport() {
  const blob = new Blob([reportContent.value], { type: 'text/markdown;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${deviation.value.code}-偏差报告.md`
  a.click()
  URL.revokeObjectURL(url)
}

function renderMarkdown(text) {
  return marked(text || '')
}

function formatDate(iso) {
  return new Date(iso).toLocaleString('zh-CN')
}

onMounted(loadDeviation)
</script>

<style scoped>
.detail { max-width: 1000px; margin: 0 auto; }
.back-btn { background: none; border: none; color: #667eea; cursor: pointer; font-size: 14px; margin-bottom: 16px; padding: 8px 0; }
.back-btn:hover { text-decoration: underline; }
.info-card, .edit-card, .result-card { background: white; border-radius: 12px; padding: 24px; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
.info-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px; }
.code { font-family: monospace; font-size: 14px; color: #667eea; font-weight: 700; }
.info-header h2 { font-size: 20px; margin-top: 4px; }
.status-select { padding: 8px 16px; border: 1px solid #e0e0e0; border-radius: 8px; font-size: 14px; cursor: pointer; }
.info-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 20px; }
.info-item { display: flex; flex-direction: column; gap: 4px; }
.info-item label { font-size: 12px; color: #999; font-weight: 600; text-transform: uppercase; }
.info-item span { font-size: 14px; font-weight: 600; }
.tag { display: inline-block; padding: 4px 12px; border-radius: 6px; font-size: 13px; }
.tag.设备故障 { background: #e6f7ff; color: #1890ff; }
.tag.物料问题 { background: #fff7e6; color: #fa8c16; }
.tag.操作失误 { background: #fff1f0; color: #ff4d4f; }
.tag.系统偏差 { background: #f6ffed; color: #52c41a; }
.tag.其他 { background: #f0f0f0; color: #666; }
.priority { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 12px; font-weight: 700; }
.priority.p-P1 { background: #fff1f0; color: #ff4d4f; }
.priority.p-P2 { background: #fff7e6; color: #fa8c16; }
.priority.p-P3 { background: #e6f7ff; color: #1890ff; }
.priority.p-P4 { background: #f6ffed; color: #52c41a; }
.description-block label { display: block; font-size: 12px; color: #999; font-weight: 600; text-transform: uppercase; margin-bottom: 6px; }
.description-block textarea { width: 100%; padding: 10px; border: 1px solid #e0e0e0; border-radius: 8px; font-size: 14px; resize: vertical; font-family: inherit; }
.description-block textarea:focus { outline: none; border-color: #667eea; }
.inline-edit { padding: 4px 8px; border: 1px solid #667eea; border-radius: 6px; font-size: 13px; }

.section-title { font-size: 16px; font-weight: 700; margin-bottom: 16px; color: #333; }
.ai-section { background: linear-gradient(135deg, #f3f0ff 0%, #f0f7ff 100%); border-radius: 12px; padding: 24px; margin-bottom: 20px; }
.ai-buttons { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
.ai-btn { display: flex; align-items: center; gap: 12px; background: white; border: 2px solid transparent; border-radius: 12px; padding: 16px; cursor: pointer; text-align: left; transition: all 0.2s; box-shadow: 0 2px 6px rgba(0,0,0,0.06); }
.ai-btn:hover { border-color: #667eea; transform: translateY(-2px); }
.ai-btn:disabled { opacity: 0.6; cursor: not-allowed; }
.ai-icon { font-size: 28px; }
.ai-btn-title { font-weight: 700; font-size: 14px; color: #333; }
.ai-btn-desc { font-size: 12px; color: #888; margin-top: 2px; }
.ai-loading { display: flex; align-items: center; gap: 12px; margin-top: 16px; color: #667eea; font-weight: 600; }
.spinner { width: 20px; height: 20px; border: 2px solid #e0e0e0; border-top-color: #667eea; border-radius: 50%; animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.ai-error { margin-top: 12px; padding: 12px; background: #fff1f0; border-radius: 8px; color: #ff4d4f; font-size: 14px; }

.result-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.result-title { font-weight: 700; font-size: 15px; }
.apply-btn { background: #667eea; color: white; border: none; padding: 6px 16px; border-radius: 6px; cursor: pointer; font-size: 13px; }
.apply-btn:hover { background: #5a71d4; }
.classify-result { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
.classify-item { display: flex; flex-direction: column; gap: 4px; padding: 12px; background: #f9f9f9; border-radius: 8px; }
.classify-item span { font-size: 12px; color: #888; }
.classify-item strong { font-size: 16px; color: #667eea; }
.classify-item em { font-size: 13px; color: #666; font-style: normal; }

.edit-row { margin-bottom: 20px; }
.edit-row:last-child { margin-bottom: 0; }
.edit-row label { display: block; font-weight: 600; font-size: 14px; margin-bottom: 8px; color: #333; }
.edit-row textarea { width: 100%; padding: 12px; border: 1px solid #e0e0e0; border-radius: 8px; font-size: 14px; resize: vertical; font-family: inherit; }
.edit-row textarea:focus { outline: none; border-color: #667eea; }

.markdown-content :deep(h2) { font-size: 16px; margin: 16px 0 8px; color: #333; }
.markdown-content :deep(p) { font-size: 14px; line-height: 1.7; color: #555; margin-bottom: 8px; }
.markdown-content :deep(strong) { color: #333; }
.loading { text-align: center; padding: 60px; color: #999; }
</style>