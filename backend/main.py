"""
DeviationAI Backend - 药企偏差处理系统后端
基于 FastAPI + Ollama 本地大模型
"""

import json
import uuid
from datetime import datetime
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import aiosqlite
import httpx

# ============ 数据模型 ============

class DeviationCreate(BaseModel):
    title: str
    description: str
    category: Optional[str] = None
    priority: Optional[str] = None
    severity: Optional[str] = None

class DeviationUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[str] = None
    severity: Optional[str] = None
    root_cause: Optional[str] = None
    capa: Optional[str] = None
    status: Optional[str] = None

class DeviationOut(BaseModel):
    id: str
    code: str
    title: str
    description: str
    category: Optional[str] = None
    priority: Optional[str] = None
    severity: Optional[str] = None
    status: str
    root_cause: Optional[str] = None
    capa: Optional[str] = None
    created_at: str
    updated_at: str

# ============ 数据库 ============

DB_PATH = "deviations.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS deviations (
                id TEXT PRIMARY KEY,
                code TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                category TEXT,
                priority TEXT,
                severity TEXT,
                status TEXT DEFAULT '待处理',
                root_cause TEXT,
                capa TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        await db.commit()

async def get_next_code() -> str:
    """生成下一个偏差编号 DEV-YYYY-NNNN"""
    year = datetime.now().year
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT code FROM deviations WHERE code LIKE ? ORDER BY code DESC LIMIT 1",
            (f"DEV-{year}-%",)
        )
        row = await cursor.fetchone()
        if row:
            last_num = int(row[0].split("-")[-1])
            next_num = last_num + 1
        else:
            next_num = 1
    return f"DEV-{year}-{next_num:04d}"

# ============ Ollama AI ============

OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "qwen2.5:7b"  # 默认模型，可配置

async def ollama_generate(prompt: str, system: Optional[str] = None) -> str:
    """调用 Ollama 生成内容"""
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
    }
    if system:
        payload["system"] = system

    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            response = await client.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json=payload
            )
            response.raise_for_status()
            return response.json().get("response", "").strip()
        except httpx.ConnectError:
            raise HTTPException(
                status_code=503,
                detail="无法连接到 Ollama，请确认 Ollama 已启动 (ollama serve)"
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"AI 生成失败: {str(e)}")

# ============ AI 业务逻辑 ============

SYSTEM_CLASSIFY = """你是一位制药行业 GMP 合规专家，负责对偏差报告进行智能分类。

请根据偏差描述，从以下分类中选择最合适的类别：
- 设备故障：设备、仪器、设施相关问题
- 物料问题：原料、辅料、包材、试剂相关问题
- 操作失误：人员操作不当、违反SOP相关
- 系统偏差：程序、方法、文件、验证相关问题
- 其他：上述类别无法涵盖的情况

同时判断严重程度：关键(P1)、主要(P2)、次要(P3)、轻微(P4)

请直接输出以下格式（不要有其他内容）：
分类：[类别]
严重程度：[程度]
优先级：[P1/P2/P3/P4]
原因：[简要说明理由，1-2句话]"""

SYSTEM_ROOT_CAUSE = """你是一位制药行业质量保证专家，擅长偏差调查和根本原因分析（RCA）。

给定一个偏差描述，请你使用 **5 Why 分析法** 进行根因分析。

请按以下格式输出：
---
## 5 Why 分析

**Why 1:** [第一个为什么]
**回答:** [回答]

**Why 2:** [第二个为什么]
**回答:** [回答]

**Why 3:** [第三个为什么]
**回答:** [回答]

**Why 4:** [第四个为什么]
**回答:** [回答]

**Why 5:** [第五个为什么]
**回答:** [根本原因]

## 根本原因总结
[一句话描述根本原因]

## 建议的 CAPA（纠正预防措施）
1. [纠正措施]
2. [预防措施]
3. [预防措施]

## 预防有效性评估建议
[建议如何评估CAPA的有效性]
---"""

SYSTEM_REPORT = """你是一位制药行业文档专家，负责生成符合 GMP 规范的偏差调查报告。

请根据提供的信息，生成一份完整的偏差报告。报告应包含以下部分：

1. 偏差基本信息
2. 偏差描述
3. 紧急处置措施
4. 调查过程
5. 根本原因分析
6. CAPA 计划
7. 效果确认
8. 结论

报告应使用专业的GMP术语，语言严谨，结构清晰。
直接输出报告正文，不需要额外说明。"""

async def classify_deviation(title: str, description: str) -> dict:
    """AI 分类偏差"""
    prompt = f"偏差标题：{title}\n偏差描述：{description}"
    result = await ollama_generate(prompt, SYSTEM_CLASSIFY)
    
    # 解析结果
    category = None
    severity = None
    priority = None
    reason = ""
    
    for line in result.split("\n"):
        if line.startswith("分类："):
            category = line.replace("分类：", "").strip()
        elif line.startswith("严重程度："):
            severity = line.replace("严重程度：", "").strip()
        elif line.startswith("优先级："):
            priority = line.replace("优先级：", "").strip()
        elif line.startswith("原因："):
            reason = line.replace("原因：", "").strip()
    
    return {
        "category": category or "其他",
        "severity": severity or "主要",
        "priority": priority or "P2",
        "reason": reason
    }

async def analyze_root_cause(title: str, description: str) -> dict:
    """AI 根因分析"""
    prompt = f"偏差标题：{title}\n偏差描述：{description}"
    result = await ollama_generate(prompt, SYSTEM_ROOT_CAUSE)
    return {"analysis": result}

async def generate_report(deviation: dict) -> str:
    """AI 生成偏差报告"""
    prompt = f"""偏差编号：{deviation['code']}
偏差标题：{deviation['title']}
偏差描述：{deviation['description']}
分类：{deviation.get('category', '')}
严重程度：{deviation.get('severity', '')}
优先级：{deviation.get('priority', '')}
根本原因：{deviation.get('root_cause', '待分析')}
CAPA：{deviation.get('capa', '待制定')}"""
    result = await ollama_generate(prompt, SYSTEM_REPORT)
    return result

# ============ FastAPI 应用 ============

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(title="DeviationAI API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- 偏差记录 CRUD ----

@app.post("/api/deviations", response_model=DeviationOut)
async def create_deviation(data: DeviationCreate):
    id = str(uuid.uuid4())
    code = await get_next_code()
    now = datetime.now().isoformat()
    
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO deviations (id, code, title, description, category, priority, severity, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, '待处理', ?, ?)
        """, (id, code, data.title, data.description, data.category, data.priority, data.severity, now, now))
        await db.commit()
    
    return DeviationOut(
        id=id, code=code, title=data.title, description=data.description,
        category=data.category, priority=data.priority, severity=data.severity,
        status="待处理", created_at=now, updated_at=now
    )

@app.get("/api/deviations")
async def list_deviations(
    status: Optional[str] = None,
    category: Optional[str] = None,
    priority: Optional[str] = None
):
    conditions = []
    params = []
    if status:
        conditions.append("status = ?")
        params.append(status)
    if category:
        conditions.append("category = ?")
        params.append(category)
    if priority:
        conditions.append("priority = ?")
        params.append(priority)
    
    where = " AND ".join(conditions) if conditions else "1=1"
    
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            f"SELECT * FROM deviations WHERE {where} ORDER BY created_at DESC",
            params
        )
        rows = await cursor.fetchall()
    
    return [
        DeviationOut(
            id=r[0], code=r[1], title=r[2], description=r[3],
            category=r[4], priority=r[5], severity=r[6], status=r[7],
            root_cause=r[8], capa=r[9], created_at=r[10], updated_at=r[11]
        )
        for r in rows
    ]

@app.get("/api/deviations/{deviation_id}")
async def get_deviation(deviation_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT * FROM deviations WHERE id = ?", (deviation_id,))
        row = await cursor.fetchone()
    
    if not row:
        raise HTTPException(status_code=404, detail="偏差记录不存在")
    
    return DeviationOut(
        id=row[0], code=row[1], title=row[2], description=row[3],
        category=row[4], priority=row[5], severity=row[6], status=row[7],
        root_cause=row[8], capa=row[9], created_at=row[10], updated_at=row[11]
    )

@app.put("/api/deviations/{deviation_id}")
async def update_deviation(deviation_id: str, data: DeviationUpdate):
    now = datetime.now().isoformat()
    fields = []
    params = []
    
    for field, value in data.model_dump(exclude_unset=True).items():
        fields.append(f"{field} = ?")
        params.append(value)
    
    fields.append("updated_at = ?")
    params.append(now)
    params.append(deviation_id)
    
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            f"UPDATE deviations SET {', '.join(fields)} WHERE id = ?",
            params
        )
        await db.commit()
    
    return await get_deviation(deviation_id)

@app.delete("/api/deviations/{deviation_id}")
async def delete_deviation(deviation_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM deviations WHERE id = ?", (deviation_id,))
        await db.commit()
    return {"success": True}

# ---- AI 功能 ----

@app.post("/api/deviations/{deviation_id}/classify")
async def classify_deviation_endpoint(deviation_id: str):
    deviation = await get_deviation(deviation_id)
    result = await classify_deviation(deviation.title, deviation.description)
    
    # 更新偏差记录
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            UPDATE deviations SET category = ?, priority = ?, severity = ?, updated_at = ? WHERE id = ?
        """, (result["category"], result["priority"], result["severity"], datetime.now().isoformat(), deviation_id))
        await db.commit()
    
    return result

@app.post("/api/deviations/{deviation_id}/root-cause")
async def root_cause_endpoint(deviation_id: str):
    deviation = await get_deviation(deviation_id)
    result = await analyze_root_cause(deviation.title, deviation.description)
    
    # 解析并更新
    analysis = result["analysis"]
    # 简单提取根本原因和CAPA
    root_cause = ""
    capa = ""
    
    if "根本原因总结" in analysis:
        start = analysis.find("根本原因总结")
        end = analysis.find("## 建议的 CAPA", start) if "## 建议的 CAPA" in analysis[start:] else len(analysis)
        root_cause = analysis[start + len("根本原因总结"):end].strip()
    
    if "建议的 CAPA" in analysis:
        start = analysis.find("建议的 CAPA")
        root_cause_end = analysis.find("根本原因总结")
        if start < root_cause_end or root_cause_end == -1:
            start = root_cause_end + len("根本原因总结\n") if root_cause_end > 0 else start
        end = analysis.find("## 预防有效性", start) if "## 预防有效性" in analysis[start:] else len(analysis)
        capa = analysis[start:end].strip()
    
    if root_cause or capa:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "UPDATE deviations SET root_cause = ?, capa = ?, updated_at = ? WHERE id = ?",
                (root_cause, capa, datetime.now().isoformat(), deviation_id)
            )
            await db.commit()
    
    return result

@app.post("/api/deviations/{deviation_id}/report")
async def generate_report_endpoint(deviation_id: str):
    deviation = await get_deviation(deviation_id)
    dev_dict = deviation.model_dump()
    report = await generate_report(dev_dict)
    return {"report": report}

@app.get("/api/health")
async def health_check():
    """健康检查 + Ollama 连接状态"""
    ollama_status = "disconnected"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            if resp.status_code == 200:
                models = resp.json().get("models", [])
                ollama_status = "connected"
    except:
        pass
    
    return {
        "status": "ok",
        "ollama": ollama_status,
        "model": OLLAMA_MODEL if ollama_status == "connected" else None
    }