# DeviationAI - 药企偏差处理系统

## 项目概述

基于本地 Ollama 大模型的药企偏差处理辅助工具，支持偏差报告自动撰写、智能分类、根因分析建议。

## 技术架构

- **后端**：Python 3.11 + FastAPI + SQLite
- **AI 引擎**：Ollama (本地大模型，默认 qwen2.5:7b)
- **存储**：SQLite (本地文件数据库)
- **前端**：Vite + Vue 3（浏览器访问，或 Electron 桌面客户端）

## 功能模块

### 1. 偏差登记
- 偏差编号（DEV-YYYY-NNNN，自动生成）
- 发生时间 / 发现时间
- 偏差类型（OOS / 设备故障 / 操作偏差 / 物料异常 / 其他）
- 偏差等级（Critical / Major / Minor）
- 涉及产品 / 批号
- 报告人

### 2. 初步评估（24h内）
- 偏差描述（5W2H：何时/何地/何人/何事/为何/如何/多少）
- 即时处置措施
- 影响范围（涉及批次/是否已放行/是否US市场）
- 是否触发OOS → 关联OOS编号
- 是否需要启动CAPA

### 3. 调查执行（5M1E）
- 人员（Man）— 培训/资质/操作记录
- 机器（Machine）— 设备状态/校准/维护
- 物料（Material）— 供应商/COA/储存
- 方法（Method）— SOP版本/参数/验证
- 环境（Environment）— 温湿度/洁净区
- 测量（Measurement）— 仪器/标准品

### 4. 根本原因分析
- 5-Why逐层追问（AI 辅助）
- 根本原因分类
  - 人员行为
  - 设备设施
  - 产品物料
  - 文件记录
  - 环境/其他
- 结论锁定

### 5. CAPA制定
- 纠正措施（CA）— 本次处置
- 预防措施（PA）— 系统改进
- 责任人 / 完成时限 / 验证方式
- CAPA状态（Open / In Progress / Closed）

### 6. 闭合与归档
- 偏差关闭日期
- 影响性评估结论
- 批次处置结论
- 附件清单

## 数据模型

### Deviation (偏差记录)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| code | String | 偏差编号 DEV-YYYY-NNNN |
| deviation_type | String | 偏差类型 |
| level | String | Critical/Major/Minor |
| product | String | 涉及产品 |
| batch_no | String | 批号 |
| reporter | String | 报告人 |
| occurred_at | DateTime | 发生时间 |
| discovered_at | DateTime | 发现时间 |
| description | Text | 偏差描述(5W2H) |
| immediate_action | Text | 即时处置措施 |
| impact_scope | String | 影响范围 |
| oos_related | Boolean | 是否关联OOS |
| oos_number | String | OOS编号 |
| needs_capa | Boolean | 是否启动CAPA |
| status | String | 状态 |
| # 5M1E 调查 | | |
| investigation_man | Text | 人员调查 |
| investigation_machine | Text | 设备调查 |
| investigation_material | Text | 物料调查 |
| investigation_method | Text | 方法调查 |
| investigation_environment | Text | 环境调查 |
| investigation_measurement | Text | 测量调查 |
| # 根因分析 | | |
| root_cause | Text | 根本原因 |
| root_cause_type | String | 原因分类 |
| # CAPA | | |
| corrective_action | Text | 纠正措施(CA) |
| preventive_action | Text | 预防措施(PA) |
| capa_owner | String | CAPA责任人 |
| capa_deadline | DateTime | CAPA时限 |
| capa_verification | String | 验证方式 |
| capa_status | String | Open/In Progress/Closed |
| # 关闭 | | |
| closed_at | DateTime | 关闭日期 |
| impact_assessment | String | 影响性评估 |
| batch_disposition | String | 批次处置结论 |
| attachments | String | 附件清单 |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

## API 接口

### 偏差 CRUD
- `POST /api/deviations` - 创建偏差
- `GET /api/deviations` - 获取列表（支持过滤）
- `GET /api/deviations/{id}` - 获取详情
- `PUT /api/deviations/{id}` - 更新偏差
- `DELETE /api/deviations/{id}` - 删除偏差

### AI 智能辅助
- `POST /api/deviations/{id}/classify` - 智能分类 + 定级
- `POST /api/deviations/{id}/root-cause` - 根因分析 (5 Why)
- `POST /api/deviations/{id}/report` - 生成 GMP 报告

### 系统
- `GET /api/health` - 健康检查 + Ollama 状态

## 快速启动

### 1. 安装 Ollama
```
winget install Ollama
ollama pull qwen2.5:7b
ollama serve
```

### 2. 启动后端
```
cd C:\Users\PC\.openclaw\workspace\deviation-ai
python app.py
```

### 3. 启动前端
```
cd frontend
npm install
npm run dev
```

### 4. 访问
```
浏览器打开 http://localhost:5173
```

## 偏差状态流转

```
新建 → 初步评估(待处理) → 调查中 → 根因分析中 → CAPA制定中 → 待审批 → 已完成
```

## AI Prompt 设计

- **智能分类**：输入描述 → 输出类型+等级+理由
- **5 Why 分析**：输入偏差描述 → 逐层追问+根本原因+CAPA
- **GMP 报告生成**：输入所有字段 → 输出完整偏差调查报告