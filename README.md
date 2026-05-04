# DeviationAI - 药企偏差处理系统

基于本地大模型 Ollama 的 GMP 偏差管理工具，支持智能分类、5M1E 调查、5-Why 根因分析、CAPA 全生命周期管理。

---

## 功能模块

| 模块 | 说明 |
|------|------|
| 偏差登记 | 5W2H 结构化描述，DEV-YYYY-NNNN 自动编号 |
| 智能分类 | AI 自动判断偏差类型（OOS/设备故障/操作偏差/物料异常/其他）及等级（Critical/Major/Minor） |
| 初步评估 | 即时处置、影响范围、OOS 关联、美国市场影响评估 |
| 5M1E 调查 | AI 辅助填写 6 个维度（人员/机器/物料/方法/环境/测量） |
| 根因分析 | 5-Why 分析 + 根因分类（人员行为/设备设施/产品物料/文件记录/环境/其他） |
| CAPA 管理 | CA/PA 制定、执行跟踪、状态闭环（Open → In Progress → Closed） |
| GMP 报告 | 一键生成符合药企规范的完整偏差调查报告 |
| 闭合归档 | 批处理决策、影响评估、附件管理 |

---

## 环境要求

- **Python**：3.9+
- **Ollama**：0.22.0+（需提前安装并下载模型）
- **Node.js**：18+（仅前端开发需要）

---

## 快速安装

### 1. 克隆项目

```bash
git clone https://github.com/ztx356639-creator/deviation-ai.git
cd deviation-ai
```

### 2. 安装后端依赖

```bash
pip install fastapi aiosqlite httpx uvicorn
```

### 3. 下载 Ollama 模型

```bash
ollama pull qwen2.5:7b
```

### 4. 启动 Ollama 服务

```bash
ollama serve
```

### 5. 启动后端

```bash
python app.py
```

后端运行在 http://localhost:8000

### 6. 启动前端（如需 GUI 界面）

```bash
cd frontend
npm install
npm run dev
```

浏览器打开 http://localhost:5173

---

## 快捷启动（Windows）

双击运行以下批处理文件：

- `启动后端.bat` — 启动后端服务
- `启动前端.bat` — 启动前端界面
- `打开浏览器.bat` — 打开浏览器访问
- `使用说明.bat` — 查看使用说明

---

## 偏差类型与等级

**类型**：OOS / 设备故障 / 操作偏差 / 物料异常 / 其他

**等级**：
- **Critical（严重）**：影响产品质量，需立即处理
- **Major（主要）**：影响工艺或数据，需调查
- **Minor（次要）**：轻微偏差，记录即可

---

## 状态流转

```
新建 → 待处理 → 调查中 → 根因分析中 → CAPA制定中 → 待审批 → 已完成
```

---

## 技术栈

- **后端**：FastAPI + SQLite + Ollama
- **前端**：Vue 3 + Vite
- **模型**：qwen2.5:7b（Ollama 本地部署）

---

## 注意事项

- 本工具为桌面本地部署，数据存储在本地 `deviations.db`
- AI 功能依赖 Ollama 服务，确保启动前 Ollama 已运行
- 建议定期备份数据库文件
- 本工具仅供学习参考，实际 GMP 偏差处理请遵循企业 SOP