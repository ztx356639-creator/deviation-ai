<template>
  <div class="home">
    <!-- 统计 -->
    <div class="stats">
      <div class="stat-card" v-for="s in statCards" :key="s.label" @click="filterStatus = s.value; load()">
        <div class="stat-num">{{ s.count }}</div>
        <div class="stat-label">{{ s.label }}</div>
      </div>
    </div>

    <!-- 工具栏 -->
    <div class="toolbar">
      <button class="btn-primary" @click="showNew = true">+ 新建偏差</button>
      <div class="filters">
        <select v-model="filterType" @change="load()">
          <option value="">全类型</option>
          <option>OOS</option><option>设备故障</option>
          <option>操作偏差</option><option>物料异常</option><option>其他</option>
        </select>
        <select v-model="filterLevel" @change="load()">
          <option value="">全等级</option>
          <option>Critical</option><option>Major</option><option>Minor</option>
        </select>
        <select v-model="filterStatus" @change="load()">
          <option value="">全状态</option>
          <option>待处理</option><option>调查中</option>
          <option>待审批</option><option>已完成</option>
        </select>
      </div>
    </div>

    <!-- 列表 -->
    <div v-if="loading" class="empty">加载中...</div>
    <div v-else-if="list.length === 0" class="empty">暂无偏差记录</div>
    <div v-else class="card-grid">
      <div v-for="d in list" :key="d.id" class="card" @click="$router.push(`/deviation/${d.id}`)">
        <div class="card-head">
          <span class="code">{{ d.code }}</span>
          <span :class="['badge', d.level]">{{ d.level }}</span>
        </div>
        <div class="card-body">
          <div class="card-type">{{ d.deviation_type }}</div>
          <div class="card-product">{{ d.product || '—'}} {{ d.batch_no ? `/ ${d.batch_no}` : '' }}</div>
          <div class="card-desc">{{ d.description || '无描述' }}</div>
        </div>
        <div class="card-foot">
          <span v-if="d.status" :class="['status', d.status]">{{ d.status }}</span>
          <span v-if="d.needs_capa" class="capa-tag">需CAPA</span>
          <span class="date">{{ formatDate(d.created_at) }}</span>
        </div>
      </div>
    </div>

    <!-- 新建弹窗 -->
    <div v-if="showNew" class="modal-overlay" @click.self="showNew = false">
      <div class="modal">
        <h2>新建偏差记录</h2>
        <div class="form-row">
          <div class="form-group">
            <label>偏差类型 *</label>
            <select v-model="newForm.deviation_type">
              <option>其他</option><option>OOS</option><option>设备故障</option><option>操作偏差</option><option>物料异常</option>
            </select>
          </div>
          <div class="form-group">
            <label>等级</label>
            <select v-model="newForm.level">
              <option>Minor</option><option>Major</option><option>Critical</option>
            </select>
          </div>
        </div>
        <div class="form-row">
          <div class="form-group"><label>产品名称</label><input v-model="newForm.product" placeholder="如：重组人胰岛素"/></div>
          <div class="form-group"><label>批号</label><input v-model="newForm.batch_no" placeholder="如：20260401"/></div>
        </div>
        <div class="form-row">
          <div class="form-group"><label>报告人</label><input v-model="newForm.reporter" placeholder="填写姓名"/></div>
          <div class="form-group"><label>发生时间</label><input v-model="newForm.occurred_at" type="datetime-local"/></div>
        </div>
        <div class="form-group">
          <label>偏差描述 *（5W2H）</label>
          <textarea v-model="newForm.description" rows="4" placeholder="何时/何地/何人/何事/为何/如何/多少"></textarea>
        </div>
        <div class="form-group">
          <label>即时处置措施</label>
          <textarea v-model="newForm.immediate_action" rows="2" placeholder="已采取的紧急措施"></textarea>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label>是否关联OOS</label>
            <label style="display:flex;align-items:center;gap:8px;margin-top:6px">
              <input type="checkbox" v-model="newForm.oos_related"/> 触发OOS
            </label>
          </div>
          <div class="form-group">
            <label>是否需CAPA</label>
            <label style="display:flex;align-items:center;gap:8px;margin-top:6px">
              <input type="checkbox" v-model="newForm.needs_capa"/> 启动CAPA
            </label>
          </div>
        </div>
        <div class="form-actions">
          <button class="btn-cancel" @click="showNew = false">取消</button>
          <button class="btn-primary" @click="createDev" :disabled="!newForm.description">创建</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'

const list = ref([]), loading = ref(false)
const filterType = ref(''), filterLevel = ref(''), filterStatus = ref('')
const showNew = ref(false)
const newForm = ref({ deviation_type:'其他', level:'Minor', product:'', batch_no:'', reporter:'', occurred_at:'', description:'', immediate_action:'', oos_related:false, needs_capa:false })

const statCards = computed(() => [
  { label:'全部', value:'', count: list.value.length },
  { label:'待处理', value:'待处理', count: list.value.filter(x=>x.status==='待处理').length },
  { label:'调查中', value:'调查中', count: list.value.filter(x=>x.status==='调查中').length },
  { label:'已完成', value:'已完成', count: list.value.filter(x=>x.status==='已完成').length },
])

async function load() {
  loading.value = true
  try {
    const params = {}
    if (filterType.value) params.category = filterType.value
    if (filterLevel.value) params.level = filterLevel.value
    if (filterStatus.value) params.status = filterStatus.value
    const r = await axios.get('/api/deviations', { params })
    list.value = r.data.list || []
  } finally { loading.value = false }
}

async function createDev() {
  try {
    await axios.post('/api/deviations', newForm.value)
    showNew.value = false
    newForm.value = { deviation_type:'其他', level:'Minor', product:'', batch_no:'', reporter:'', occurred_at:'', description:'', immediate_action:'', oos_related:false, needs_capa:false }
    await load()
  } catch { alert('创建失败') }
}

function formatDate(iso) { return iso ? new Date(iso).toLocaleDateString('zh-CN') : '' }

onMounted(load)
</script>

<style scoped>
.home { max-width: 1400px; margin: 0 auto; }
.stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 24px; }
.stat-card { background: white; border-radius: 12px; padding: 20px; cursor: pointer; transition: 0.2s; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
.stat-card:hover { transform: translateY(-2px); box-shadow: 0 4px 16px rgba(0,0,0,0.1); }
.stat-num { font-size: 32px; font-weight: 700; color: #667eea; }
.stat-label { color: #666; font-size: 13px; margin-top: 4px; }
.toolbar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.filters { display: flex; gap: 10px; }
.filters select { padding: 8px 14px; border: 1px solid #e0e0e0; border-radius: 8px; background: white; font-size: 13px; cursor: pointer; }
.btn-primary { background: linear-gradient(135deg, #667eea, #764ba2); color: white; border: none; padding: 10px 22px; border-radius: 8px; cursor: pointer; font-weight: 600; font-size: 14px; }
.btn-cancel { background: #f0f0f0; border: none; padding: 10px 22px; border-radius: 8px; cursor: pointer; font-size: 14px; }
.card-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 16px; }
.card { background: white; border-radius: 12px; padding: 20px; cursor: pointer; transition: 0.2s; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
.card:hover { transform: translateY(-2px); box-shadow: 0 4px 16px rgba(0,0,0,0.1); }
.card-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
.code { font-family: monospace; font-weight: 700; color: #667eea; font-size: 13px; }
.badge { font-size: 11px; padding: 3px 10px; border-radius: 10px; font-weight: 700; }
.badge.Critical { background: #fff1f0; color: #ff4d4f; }
.badge.Major { background: #fff7e6; color: #fa8c16; }
.badge.Minor { background: #e6f7ff; color: #1890ff; }
.card-type { font-size: 12px; color: #888; margin-bottom: 4px; }
.card-product { font-size: 15px; font-weight: 600; color: #333; margin-bottom: 6px; }
.card-desc { font-size: 13px; color: #666; line-height: 1.5; margin-bottom: 10px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.card-foot { display: flex; align-items: center; gap: 8px; }
.status { font-size: 11px; padding: 3px 10px; border-radius: 10px; font-weight: 600; }
.status.待处理 { background: #fff7e6; color: #fa8c16; }
.status.调查中 { background: #e6f7ff; color: #1890ff; }
.status.待审批 { background: #fff1f0; color: #ff4d4f; }
.status.已完成 { background: #f6ffed; color: #52c41a; }
.capa-tag { background: #f9f0ff; color: #722ed1; font-size: 11px; padding: 3px 8px; border-radius: 4px; font-weight: 600; }
.date { font-size: 12px; color: #aaa; margin-left: auto; }
.empty { text-align: center; padding: 60px; color: #999; }
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.45); display: flex; align-items: center; justify-content: center; z-index: 100; }
.modal { background: white; border-radius: 16px; padding: 28px; width: 560px; max-width: 95vw; max-height: 90vh; overflow-y: auto; }
.modal h2 { margin-bottom: 20px; font-size: 18px; }
.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
.form-group { display: flex; flex-direction: column; gap: 5px; margin-bottom: 14px; }
.form-group label { font-size: 13px; font-weight: 600; color: #555; }
.form-group input, .form-group select, .form-group textarea { padding: 9px 12px; border: 1px solid #e0e0e0; border-radius: 8px; font-size: 13px; font-family: inherit; resize: vertical; }
.form-group input:focus, .form-group select:focus, .form-group textarea:focus { outline: none; border-color: #667eea; }
.form-actions { display: flex; justify-content: flex-end; gap: 10px; margin-top: 16px; }
.form-actions .btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
</style>