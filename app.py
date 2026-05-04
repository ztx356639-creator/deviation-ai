"""
DeviationAI - 药企偏差处理系统 (完整版)
模型: qwen2.5:7b
直接运行: python app.py
"""

import re
import uuid
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import aiosqlite, httpx, uvicorn

# ============ 配置 ============
DB_PATH = "deviations.db"
OLLAMA_BASE = "http://localhost:11434"
OLLAMA_MODEL = "qwen2.5:7b"

# ============ Pydantic 模型 ============
class DevCreate(BaseModel):
    deviation_type: str = "其他"
    level: str = "Minor"
    product: str = ""
    batch_no: str = ""
    reporter: str = ""
    occurred_at: str = ""
    discovered_at: str = ""
    description: str = ""
    immediate_action: str = ""
    impact_scope: str = ""
    oos_related: bool = False
    oos_number: str = ""
    needs_capa: bool = False

class DevUpdate(BaseModel):
    deviation_type: str | None = None
    level: str | None = None
    product: str | None = None
    batch_no: str | None = None
    reporter: str | None = None
    occurred_at: str | None = None
    discovered_at: str | None = None
    description: str | None = None
    immediate_action: str | None = None
    impact_scope: str | None = None
    oos_related: bool | None = None
    oos_number: str | None = None
    needs_capa: bool | None = None
    status: str | None = None
    investigation_man: str | None = None
    investigation_machine: str | None = None
    investigation_material: str | None = None
    investigation_method: str | None = None
    investigation_environment: str | None = None
    investigation_measurement: str | None = None
    root_cause: str | None = None
    root_cause_type: str | None = None
    corrective_action: str | None = None
    preventive_action: str | None = None
    capa_owner: str | None = None
    capa_deadline: str | None = None
    capa_verification: str | None = None
    capa_status: str | None = None
    closed_at: str | None = None
    impact_assessment: str | None = None
    batch_disposition: str | None = None
    attachments: str | None = None

# ============ 数据库 ============
FIELDS = [
    "deviation_type","level","product","batch_no","reporter",
    "occurred_at","discovered_at","description","immediate_action",
    "impact_scope","oos_related","oos_number","needs_capa","status",
    "investigation_man","investigation_machine","investigation_material",
    "investigation_method","investigation_environment","investigation_measurement",
    "root_cause","root_cause_type","corrective_action","preventive_action",
    "capa_owner","capa_deadline","capa_verification","capa_status",
    "closed_at","impact_assessment","batch_disposition","attachments"
]

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        cols = ["id TEXT PRIMARY KEY","code TEXT UNIQUE NOT NULL"] + \
               [f"{f} TEXT" for f in FIELDS] + \
               ["created_at TEXT","updated_at TEXT"]
        await db.execute(f"CREATE TABLE IF NOT EXISTS deviations ({','.join(cols)})")
        await db.commit()

async def next_code():
    yr = datetime.now().year
    async with aiosqlite.connect(DB_PATH) as db:
        c = await db.execute(f"SELECT code FROM deviations WHERE code LIKE ? ORDER BY code DESC LIMIT 1", (f"DEV-{yr}-%",))
        r = await c.fetchone()
        n = int(r[0].split("-")[-1]) + 1 if r else 1
    return f"DEV-{yr}-{n:04d}"

# ============ Ollama ============
async def ollama(prompt, system=None):
    async with httpx.AsyncClient(timeout=180.0) as c:
        try:
            r = await c.post(f"{OLLAMA_BASE}/api/generate",
                json={"model":OLLAMA_MODEL,"prompt":prompt,"system":system,"stream":False})
            r.raise_for_status()
            return r.json().get("response","").strip()
        except httpx.ConnectError:
            raise HTTPException(503,"Ollama 未运行，请执行: ollama serve")
        except Exception as e:
            raise HTTPException(500,f"AI 调用失败: {e}")

SYS_CLASSIFY = """你是制药行业GMP合规专家。根据偏差描述输出：

偏差类型：OOS/设备故障/操作偏差/物料异常/其他
等级：Critical/Major/Minor
原因：[一句话理由]

直接输出，不要其他内容。"""

SYS_5M1E = """你是药企质量专家。根据偏差信息，按5M1E框架填写调查：

人员(MAN)：培训/资质/操作记录调查说明
机器(MACHINE)：设备状态/校准/维护调查说明
物料(MATERIAL)：供应商/COA/储存调查说明
方法(METHOD)：SOP版本/参数/验证调查说明
环境(ENVIRONMENT)：温湿度/洁净区调查说明
测量(MEASUREMENT)：仪器/标准品调查说明

每个字段输出2-3句话，用专业GMP语言。没有信息的字段填"待查"。

输出格式：
MAN:[内容]
MACHINE:[内容]
MATERIAL:[内容]
METHOD:[内容]
ENVIRONMENT:[内容]
MEASUREMENT:[内容]"""

SYS_ROOTCAUSE = """你是药企质量专家，使用5-Why分析法分析偏差。

输入偏差描述，输出5层追问+根本原因+CAPA建议。

格式：
Why1：[问题]
答：[回答]
Why2：...
答：...
Why3：...
答：...
Why4：...
答：...
Why5：...

根本原因：[一句话]
原因类型：人员行为/设备设施/产品物料/文件记录/环境/其他

纠正措施(CA)：[本次处置]
预防措施(PA)：[系统改进]"""

SYS_REPORT = """生成GMP偏差调查报告，包含所有字段。

偏差编号：[编号]
偏差标题：[标题]
偏差类型：[类型]
等级：[Critical/Major/Minor]
发生时间：[时间]
发现时间：[时间]
产品/批号：[产品]/[批号]
报告人：[人]

一、偏差描述（5W2H）
[内容]

二、即时处置措施
[内容]

三、影响范围评估
[内容]

四、5M1E调查
[内容]

五、根本原因分析
[内容]

六、CAPA计划
纠正措施：[CA内容]
预防措施：[PA内容]
责任人：[姓名]
完成时限：[日期]
验证方式：[方式]

七、偏差关闭与影响性评估
[内容]

八、批次处置结论
[内容]

九、附件清单
[内容]

输出完整报告，正文格式，不要其他说明。"""

# ============ FastAPI ============
app = FastAPI(title="DeviationAI")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.on_event("startup")
async def _(): await init_db()

def row_to_dev(r):
    d = dict(zip(["id","code"] + FIELDS + ["created_at","updated_at"], r))
    return d

@app.post("/api/deviations")
async def create(d: DevCreate):
    now = datetime.now().isoformat()
    code = await next_code()
    id = str(uuid.uuid4())
    vals = [id, code] + [getattr(d, f, "") or "" for f in FIELDS] + [now, now]
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            f"INSERT INTO deviations (id,code,{','.join(FIELDS)},created_at,updated_at) VALUES ({','.join(['?']*len(vals))})",
            vals)
        await db.commit()
    return row_to_dev([id, code] + [getattr(d, f, "") or "" for f in FIELDS] + [now, now])

@app.get("/api/deviations")
async def list(status: str = "", category: str = "", level: str = "", page: int = 1, size: int = 50):
    conds, ps = [], []
    if status:  conds.append("status=?"), ps.append(status)
    if category: conds.append("deviation_type=?"), ps.append(category)
    if level: conds.append("level=?"), ps.append(level)
    w = " AND ".join(conds) if conds else "1=1"
    async with aiosqlite.connect(DB_PATH) as db:
        c = await db.execute(
            f"SELECT * FROM deviations WHERE {w} ORDER BY created_at DESC LIMIT ? OFFSET ?",
            ps + [size, (page-1)*size])
        rows = await c.fetchall()
    total = await (await db.execute(f"SELECT COUNT(*) FROM deviations WHERE {w}", ps)).fetchone()[0]
    return {"list": [row_to_dev(r) for r in rows], "total": total, "page": page, "size": size}

@app.get("/api/deviations/{id}")
async def get(id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        c = await db.execute("SELECT * FROM deviations WHERE id=?", (id,))
        r = await c.fetchone()
    if not r: raise HTTPException(404, "偏差不存在")
    return row_to_dev(r)

@app.put("/api/deviations/{id}")
async def update(id: str, d: DevUpdate):
    now = datetime.now().isoformat()
    updates, ps = [], []
    for f in FIELDS:
        v = getattr(d, f, None)
        if v is not None:
            updates.append(f"{f}=?"), ps.append(v)
    updates.append("updated_at=?"), ps.append(now), ps.append(id)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(f"UPDATE deviations SET {','.join(updates)} WHERE id=?", ps)
        await db.commit()
    return await get(id)

@app.delete("/api/deviations/{id}")
async def delete(id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM deviations WHERE id=?", (id,))
        await db.commit()
    return {"success": True}

# ---- AI ----

@app.post("/api/deviations/{id}/classify")
async def classify(id: str):
    dev = await get(id)
    desc = f"类型:{dev.get('deviation_type','')}\n描述:{dev.get('description','')}"
    result = await ollama(desc, SYS_CLASSIFY)
    dev_t, lvl, reason = "其他", "Minor", ""
    for line in result.split("\n"):
        if "OOS" in line: dev_t = "OOS"
        elif "设备故障" in line: dev_t = "设备故障"
        elif "操作偏差" in line: dev_t = "操作偏差"
        elif "物料异常" in line: dev_t = "物料异常"
        elif "Critical" in line: lvl = "Critical"
        elif "Major" in line: lvl = "Major"
        elif "Minor" in line: lvl = "Minor"
        if "原因" in line: reason = line.split("原因")[-1].strip()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE deviations SET deviation_type=?,level=?,updated_at=? WHERE id=?",
            (dev_t, lvl, datetime.now().isoformat(), id))
        await db.commit()
    return {"deviation_type": dev_t, "level": lvl, "reason": reason}

@app.post("/api/deviations/{id}/investigate")
async def investigate(id: str):
    dev = await get(id)
    desc = f"产品:{dev.get('product','')}\n偏差描述:{dev.get('description','')}\n即时措施:{dev.get('immediate_action','')}"
    result = await ollama(desc, SYS_5M1E)
    updates = {}
    for line in result.split("\n"):
        if line.startswith("MAN:"): updates["investigation_man"] = line[4:].strip()
        elif line.startswith("MACHINE:"): updates["investigation_machine"] = line[8:].strip()
        elif line.startswith("MATERIAL:"): updates["investigation_material"] = line[9:].strip()
        elif line.startswith("METHOD:"): updates["investigation_method"] = line[7:].strip()
        elif line.startswith("ENVIRONMENT:"): updates["investigation_environment"] = line[12:].strip()
        elif line.startswith("MEASUREMENT:"): updates["investigation_measurement"] = line[12:].strip()
    if updates:
        now = datetime.now().isoformat()
        async with aiosqlite.connect(DB_PATH) as db:
            for k, v in updates.items():
                await db.execute(f"UPDATE deviations SET {k}=?,updated_at=? WHERE id=?", (v, now, id))
            await db.commit()
    return {"investigation": result}

@app.post("/api/deviations/{id}/root-cause")
async def rootcause(id: str):
    dev = await get(id)
    desc = f"偏差类型:{dev.get('deviation_type','')}\n产品:{dev.get('product','')}\n偏差描述:{dev.get('description','')}"
    result = await ollama(desc, SYS_ROOTCAUSE)
    rc, rc_type, ca, pa = "", "", "", ""
    for line in result.split("\n"):
        if "根本原因" in line and ":" in line:
            rc = line.split("根本原因")[-1].strip().lstrip(":").strip()
        if "原因类型" in line:
            rc_type = line.split("原因类型")[-1].strip()
        if "纠正措施" in line and ":" in line:
            ca = line.split("纠正措施")[-1].strip().lstrip(":").strip()
        if "预防措施" in line and ":" in line:
            pa = line.split("预防措施")[-1].strip().lstrip(":").strip()
    if rc or ca or pa:
        now = datetime.now().isoformat()
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "UPDATE deviations SET root_cause=?,root_cause_type=?,corrective_action=?,preventive_action=?,capa_status='Open',updated_at=? WHERE id=?",
                (rc, rc_type, ca, pa, now, id))
            await db.commit()
    return {"analysis": result}

@app.post("/api/deviations/{id}/report")
async def report(id: str):
    dev = await get(id)
    prompt = f"""偏差编号:{dev.get('code','')}
偏差类型:{dev.get('deviation_type','')}
等级:{dev.get('level','')}
发生时间:{dev.get('occurred_at','')}
发现时间:{dev.get('discovered_at','')}
产品/批号:{dev.get('product','')}/{dev.get('batch_no','')}
报告人:{dev.get('reporter','')}
偏差描述:{dev.get('description','')}
即时措施:{dev.get('immediate_action','')}
影响范围:{dev.get('impact_scope','')}
5M1E-人员:{dev.get('investigation_man','')}
5M1E-机器:{dev.get('investigation_machine','')}
5M1E-物料:{dev.get('investigation_material','')}
5M1E-方法:{dev.get('investigation_method','')}
5M1E-环境:{dev.get('investigation_environment','')}
5M1E-测量:{dev.get('investigation_measurement','')}
根本原因:{dev.get('root_cause','')}
原因类型:{dev.get('root_cause_type','')}
纠正措施:{dev.get('corrective_action','')}
预防措施:{dev.get('preventive_action','')}
CAPA责任人:{dev.get('capa_owner','')}
CAPA时限:{dev.get('capa_deadline','')}
CAPA验证:{dev.get('capa_verification','')}
影响性评估:{dev.get('impact_assessment','')}
批次处置:{dev.get('batch_disposition','')}
附件:{dev.get('attachments','')}"""
    return {"report": await ollama(prompt, SYS_REPORT)}

@app.get("/api/health")
async def health():
    s = "disconnected"
    models = []
    try:
        async with httpx.AsyncClient(timeout=5.0) as c:
            r = await c.get(f"{OLLAMA_BASE}/api/tags")
            if r.status_code == 200:
                s = "connected"
                models = [m["name"] for m in r.json().get("models",[])]
    except: pass
    return {"status":"ok","ollama":s,"model":OLLAMA_MODEL if s=="connected" else None,"available_models":models}

# ============ 启动 ============
if __name__ == "__main__":
    print(f"🚀 DeviationAI 后端已启动 http://127.0.0.1:8000")
    print(f"   模型: {OLLAMA_MODEL}")
    print(f"   文档: http://127.0.0.1:8000/docs")
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning")