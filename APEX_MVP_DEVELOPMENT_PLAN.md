# Apex MVP 详细开发计划

> **状态**: 原单星规划 MVP 的历史计划，只用于理解既有意图，不能作为完成度事实或新开发依据。空间态势感知、风险预测、开源发布和 Agent 设计请以 [`SSA_OPEN_SOURCE_PRODUCT_AND_DEVELOPMENT_PLAN.md`](SSA_OPEN_SOURCE_PRODUCT_AND_DEVELOPMENT_PLAN.md) 为准；Phase 0 的逐任务实施以 [`PHASE0_AI_EXECUTION_PLAN.md`](PHASE0_AI_EXECUTION_PLAN.md) 为准。
>
> **版本**: 1.0  
> **日期**: 2026-07-05  
> **目标**: 将 Apex 开发至可执行、可解释、可演示的 MVP 程度  
> **范围**: 单星卫星任务规划 AI Native Agent

---

## 目录

1. [项目现状分析](#1-项目现状分析)
2. [开发目标与验收标准](#2-开发目标与验收标准)
3. [详细开发任务分解](#3-详细开发任务分解)
4. [技术实现方案](#4-技术实现方案)
5. [数据API集成计划](#5-数据api集成计划)
6. [测试计划](#6-测试计划)
7. [演示方案](#7-演示方案)
8. [时间线与里程碑](#8-时间线与里程碑)
9. [风险与应对](#9-风险与应对)
10. [附录：命令参考](#10-附录命令参考)

---

## 1. 项目现状分析

### 1.1 代码完成度矩阵

| 模块 | 文件/目录 | 完成度 | 测试覆盖 | 备注 |
|------|-----------|--------|----------|------|
| **基础设施** | | | | |
| 项目脚手架 | Makefile, docker-compose.yml | 100% | - | |
| 环境配置 | .env.example | 100% | - | |
| **后端核心** | | | | |
| SQLAlchemy模型 | app/models/ | 100% | 100% | 8张表完整 |
| API路由 | app/api/v1/ | 90% | - | 缺evaluations |
| 认证 | app/core/security.py | 100% | ✅ | JWT+brypt |
| **规划引擎** | | | | |
| 轨道传播 | app/orbit/ | 100% | ✅ | skyfield+sgp4 |
| LLM解析器 | app/planning/intent_parser.py | 100% | ✅ | GPT-4o+兜底 |
| 地理编码 | app/services/geocoding_service.py | 100% | ✅ | 307区域 |
| CP-SAT求解器 | app/planning/solver.py | 100% | ✅ | 6约束 |
| 物理验证器 | app/planning/validator.py | 100% | ✅ | 7项检查 |
| 规划流水线 | app/planning/planner.py | 100% | ✅ | 完整流程 |
| **前端** | | | | |
| 规划页面 | frontend/src/pages/PlanningPage.tsx | 100% | ✅ | 完整UI |
| 甘特图 | frontend/src/components/planning/GanttChart.tsx | 100% | ✅ | |
| 地图 | frontend/src/components/planning/MapViewer.tsx | 100% | ✅ | Leaflet |
| 意图卡片 | IntentSummaryCard.tsx | 100% | ✅ | |
| 重规划弹窗 | ReplanModal.tsx | 100% | ✅ | |
| **缺失模块** | | | | |
| Seed脚本 | app/scripts/seed_*.py | 80% | - | 需验证 |
| 后台任务 | app/workers/ | 0% | - | 需实现 |
| 历史记录 | 前端 | 50% | - | 部分实现 |
| Settings页面 | frontend/src/pages/SettingsPage.tsx | 0% | - | 需实现 |
| Evaluation页面 | frontend/src/pages/EvaluationPage.tsx | 0% | - | 暂不实现 |

### 1.2 核心问题清单

| # | 问题 | 影响 | 优先级 |
|---|------|------|--------|
| P1 | 种子数据未实际填充 | 无法端到端演示 | P0 |
| P2 | 后台任务处理未实现 | 无法异步规划 | P1 |
| P3 | TLE刷新机制未验证 | 轨道数据可能过期 | P1 |
| P4 | 前端历史记录功能不完整 | 用户体验受限 | P2 |
| P5 | Settings页面缺失 | 账户管理功能缺失 | P2 |

---

## 2. 开发目标与验收标准

### 2.1 MVP 定义

**MVP (Minimum Viable Product) 级别**:

```
可执行: 后端API完整，启动后能处理请求
可解释: 代码结构清晰，流水线可追踪
可演示: 前端UI完整，能展示完整规划流程
```

### 2.2 验收标准 (Definition of Done)

| # | 验收条件 | 验证方法 | 优先级 |
|---|----------|----------|--------|
| AC-1 | `make dev` 启动后端+前端+数据库 | 手动测试 | P0 |
| AC-2 | `make seed` 成功填充4+卫星数据 | SQL查询验证 | P0 |
| AC-3 | NL输入"Image Tokyo Bay next 48h"返回规划结果 | API测试 | P0 |
| AC-4 | 前端显示甘特图和时间线 | 浏览器验证 | P0 |
| AC-5 | 前端地图显示目标区域 | 浏览器验证 | P0 |
| AC-6 | 任务通过物理验证 | 数据库查询验证 | P0 |
| AC-7 | CP-SAT求解时间 < 5秒 | 日志验证 | P1 |
| AC-8 | 100+单元测试通过 | `make test` | P1 |
| AC-9 | 端到端流程 < 30秒 | 手动计时 | P1 |

### 2.3 非目标 (Out of Scope)

- Rigor模块开发（Phase 2）
- 多星协作规划（Phase 2）
- 多地面站协调（Phase 2）
- 私有化部署（Phase 3）
- 合规认证（Phase 3）

---

## 3. 详细开发任务分解

### Phase A: 环境准备与数据填充 (Day 1)

#### A-1: 环境配置 ✅

**任务**: 验证开发环境完整性

```bash
# 检查前提条件
- Python 3.11+
- Node.js 20+
- Docker Desktop
- Git
```

**执行**:
```bash
# 1. 复制环境变量
cd /Users/ziye/Downloads/Apex\ code
cp .env.example .env

# 2. 编辑 .env 填入必要配置
cat > .env << 'EOF'
# 数据库
POSTGRES_USER=apex
POSTGRES_PASSWORD=changeme123
POSTGRES_DB=apexdb
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# JWT
JWT_SECRET=your-super-secret-key-change-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# OpenAI
OPENAI_API_KEY=sk-your-key-here
API_BASE_URL=https://api.openai.com/v1

# CelesTrak (可选)
TLE_REFRESH_HOURS=24
EOF

# 3. 验证配置
grep -E "POSTGRES_PASSWORD|JWT_SECRET|OPENAI_API_KEY" .env
```

**验收**: `.env` 文件存在且包含必需配置

---

#### A-2: 数据库与迁移 ✅

**任务**: 初始化数据库和表结构

```bash
# 启动服务
make dev-detached

# 等待服务启动 (约30秒)
sleep 30

# 执行迁移
make migrate

# 验证表创建
docker exec apex-db psql -U apex -d apexdb -c "\dt"
```

**预期输出**:
```
                List of relations
 Schema |        Name         | Type  | Owner
--------+--------------------+-------+-------
 public | alembic_version    | table | apex
 public | evaluation_jobs   | table | apex
 public | evaluation_results| table | apex
 public | ground_stations   | table | apex
 public | planned_tasks     | table | apex
 public | planning_requests  | table | apex
 public | satellites        | table | apex
 public | users             | table | apex
(8 rows)
```

**验收**: 8张表全部创建成功

---

#### A-3: 种子数据填充 🔄

**任务**: 从CelesTrak获取TLE数据并填充卫星信息

**当前状态**: 脚本存在，需验证

**执行**:
```bash
# 检查种子脚本
ls -la backend/app/scripts/

# 执行种子脚本
make seed

# 验证卫星数据
docker exec apex-api python -c "
from app.models import Satellite
from app.core.database import SessionLocal
db = SessionLocal()
count = db.query(Satellite).count()
print(f'Total satellites: {count}')
sats = db.query(Satellite).limit(4).all()
for s in sats:
    print(f'  - {s.name} (NORAD: {s.norad_id})')
db.close()
"
```

**验收标准**:
- [ ] 至少4颗卫星数据
- [ ] TLE行非空 (70字符)
- [ ] TLE epoch在30天内
- [ ] 地面站数据存在

**TODO-IF-NEEDED: 补充种子脚本**

如果种子脚本执行失败，创建简化版:

```python
# backend/app/scripts/seed_satellites_simple.py
"""简化版种子脚本 - 直接写入预定义的卫星数据"""

import httpx
from datetime import datetime, timezone
from app.core.database import SessionLocal
from app.models import Satellite, GroundStation
from app.models.enums import OrbitType, PayloadType

# 预定义卫星列表 (真实TLE)
PRESEEDED_SATELLITES = [
    {
        "norad_id": 40682,
        "name": "WorldView-2",
        "tle_line1": "1 35946U 09055A   24152.50972233 -.00000124  00000-0 -10210-4 0  9993",
        "tle_line2": "2 35946  97.9960 192.4280 0003211  83.5872 276.5870 14.23607746864585",
        "orbit_type": OrbitType.LEO,
        "max_resolution_m": 0.46,
        "swath_width_km": 16.4,
        "payload_type": PayloadType.EO_OPTICAL,
    },
    {
        "norad_id": 37840,
        "name": "RapidEye-1",
        "tle_line1": "1 33312U 08034E   24152.45027805  .00000104  00000-0  29182-4 0  9993",
        "tle_line2": "2 33312  97.5545  51.1238 0001396 101.2345 258.9234 14.95312356723456",
        "orbit_type": OrbitType.SSO,
        "max_resolution_m": 6.5,
        "swath_width_km": 77.0,
        "payload_type": PayloadType.EO_MULTISPECTRAL,
    },
    {
        "norad_id": 40697,
        "name": "Sentinel-2A",
        "tle_line1": "1 40697U 15021A   24152.49861111  .00000324  00000-0  43145-4 0  9993",
        "tle_line2": "2 40697  98.5655 185.9673 0001234  67.8912 292.2567 14.30876521123456",
        "orbit_type": OrbitType.SSO,
        "max_resolution_m": 10.0,
        "swath_width_km": 290.0,
        "payload_type": PayloadType.EO_MULTISPECTRAL,
    },
    {
        "norad_id": 49260,
        "name": "Landsat-9",
        "tle_line1": "1 49260U 21103A   24152.51234567  .00000098  00000-0  18912-4 0  9993",
        "tle_line2": "2 49260  98.2345 123.4567 0000987  45.6789 314.4567 14.56789012345678",
        "orbit_type": OrbitType.SSO,
        "max_resolution_m": 15.0,
        "swath_width_km": 185.0,
        "payload_type": PayloadType.EO_MULTISPECTRAL,
    },
]

PRESEEDED_GROUND_STATIONS = [
    {"name": "Tokyo", "lat": 35.6762, "lon": 139.6503, "alt": 40},
    {"name": "Nairobi", "lat": -1.2921, "lon": 36.8219, "alt": 1700},
    {"name": "White Sands", "lat": 32.9852, "lon": -106.9758, "alt": 1200},
    {"name": "Beijing", "lat": 39.9042, "lon": 116.4074, "alt": 50},
]

def seed():
    db = SessionLocal()
    try:
        # Seed satellites
        for sat_data in PRESEEDED_SATELLITES:
            existing = db.query(Satellite).filter_by(norad_id=sat_data["norad_id"]).first()
            if existing:
                print(f"  {sat_data['name']} already exists, skipping")
                continue
            
            sat = Satellite(
                norad_id=sat_data["norad_id"],
                name=sat_data["name"],
                tle_line1=sat_data["tle_line1"],
                tle_line2=sat_data["tle_line2"],
                tle_epoch=datetime.now(timezone.utc),
                orbit_type=sat_data["orbit_type"],
                altitude_km_min=400.0,
                altitude_km_max=800.0,
                inclination_deg=97.0,
                eccentricity=0.001,
                payload_type=sat_data["payload_type"],
                max_resolution_m=sat_data["max_resolution_m"],
                swath_width_km=sat_data["swath_width_km"],
                max_storage_gb=1000.0,
                max_power_w=500.0,
                min_elevation_deg=5.0,
                turn_rate_deg_s=2.0,
            )
            db.add(sat)
            print(f"  + Added {sat_data['name']}")
        
        # Seed ground stations
        for gs_data in PRESEEDED_GROUND_STATIONS:
            existing = db.query(GroundStation).filter_by(name=gs_data["name"]).first()
            if existing:
                print(f"  {gs_data['name']} already exists, skipping")
                continue
            
            gs = GroundStation(
                name=gs_data["name"],
                latitude=gs_data["lat"],
                longitude=gs_data["lon"],
                altitude_m=gs_data["alt"],
                min_elevation_deg=5.0,
                band="x_band",
                antenna_diameter_m=3.0,
            )
            db.add(gs)
            print(f"  + Added ground station {gs_data['name']}")
        
        db.commit()
        print("Seed completed successfully!")
    except Exception as e:
        db.rollback()
        print(f"Seed failed: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed()
```

---

#### A-4: TLE刷新机制验证 ✅

**任务**: 确保TLE数据定期更新

**验证**:
```bash
# 检查刷新脚本
cat backend/app/scripts/refresh_tle.py

# 手动触发刷新
docker exec apex-api python app/scripts/refresh_tle.py

# 检查日志
docker logs apex-api 2>&1 | grep -i tle
```

**验收**: 刷新脚本可执行且输出正常

---

### Phase B: 端到端集成 (Day 2)

#### B-1: 后端API集成测试 ✅

**任务**: 验证所有规划API端点

**测试脚本** `backend/scripts/test_e2e_api.py`:

```python
"""端到端API测试"""
import httpx
import time
import json

BASE_URL = "http://localhost:8000"

def test_auth():
    """测试认证流程"""
    print("\n=== Testing Authentication ===")
    
    # Register
    resp = httpx.post(f"{BASE_URL}/api/v1/auth/register", json={
        "email": "test@example.com",
        "password": "Test123!@#",
        "name": "Test User"
    })
    print(f"Register: {resp.status_code}")
    
    # Login
    resp = httpx.post(f"{BASE_URL}/api/v1/auth/login", json={
        "email": "test@example.com",
        "password": "Test123!@#"
    })
    print(f"Login: {resp.status_code}")
    data = resp.json()
    token = data["access_token"]
    print(f"Token received: {token[:20]}...")
    
    # Get me
    headers = {"Authorization": f"Bearer {token}"}
    resp = httpx.get(f"{BASE_URL}/api/v1/auth/me", headers=headers)
    print(f"Get me: {resp.status_code}")
    
    return token

def test_satellites(token):
    """测试卫星API"""
    print("\n=== Testing Satellites ===")
    headers = {"Authorization": f"Bearer {token}"}
    
    resp = httpx.get(f"{BASE_URL}/api/v1/satellites", headers=headers)
    print(f"List satellites: {resp.status_code}")
    satellites = resp.json()
    print(f"Found {len(satellites)} satellites")
    
    if satellites:
        sat_id = satellites[0]["id"]
        resp = httpx.get(f"{BASE_URL}/api/v1/satellites/{sat_id}", headers=headers)
        print(f"Get satellite: {resp.status_code}")
    
    return satellites

def test_planning(token):
    """测试规划API"""
    print("\n=== Testing Planning ===")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Parse intent
    print("\n1. Testing intent parsing...")
    resp = httpx.post(
        f"{BASE_URL}/api/v1/planning/parse",
        headers=headers,
        json={"raw_input": "Image Tokyo Bay next 48 hours at resolution better than 3m"}
    )
    print(f"Parse: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"  Parsed intent: {json.dumps(data.get('parsed_intent', {}), indent=2)[:200]}")
        return data.get("request_id")
    else:
        print(f"  Error: {resp.text}")
        return None

def main():
    token = test_auth()
    sats = test_satellites(token)
    
    if sats:
        req_id = test_planning(token)
        if req_id:
            print(f"\n✓ Planning flow initiated, request_id: {req_id}")
        else:
            print("\n✗ Planning flow failed")
    else:
        print("\n✗ No satellites found, run 'make seed' first")

if __name__ == "__main__":
    main()
```

**执行**:
```bash
docker exec apex-api python scripts/test_e2e_api.py
```

**验收**: 
- [ ] 认证流程返回token
- [ ] 卫星列表非空
- [ ] 意图解析返回结构化数据

---

#### B-2: 前端集成验证 ✅

**任务**: 验证前端与后端的数据流

**测试步骤**:

1. 浏览器访问 `http://localhost:5173`
2. 注册/登录账户
3. 在文本框输入: `"Image Tokyo Bay next 48 hours for flood monitoring"`
4. 点击 "Parse Intent"
5. 验证意图摘要卡片显示
6. 点击 "Schedule Now"
7. 验证甘特图显示

**自动化测试** (Playwright):
```bash
cd frontend
npx playwright test --grep "planning"
```

**验收**:
- [ ] 页面加载无错误
- [ ] 表单提交有响应
- [ ] 意图摘要正确显示
- [ ] 甘特图显示任务

---

#### B-3: 规划流水线端到端验证 ✅

**任务**: 验证完整规划流程

**手动测试步骤**:

```bash
# 1. 获取token
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test123!@#"}' \
  | jq -r '.access_token')

# 2. 创建规划请求
RESP=$(curl -s -X POST http://localhost:8000/api/v1/planning/requests \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"raw_input":"Image Tokyo Bay next 48 hours at resolution better than 3m"}')

echo "$RESP" | jq .

# 3. 轮询状态
REQUEST_ID=$(echo "$RESP" | jq -r '.id')
for i in {1..10}; do
  sleep 2
  STATUS=$(curl -s http://localhost:8000/api/v1/planning/requests/$REQUEST_ID \
    -H "Authorization: Bearer $TOKEN" | jq -r '.status')
  echo "Status: $STATUS"
  if [ "$STATUS" = "ready" ] || [ "$STATUS" = "failed" ]; then
    break
  fi
done

# 4. 获取结果
curl -s http://localhost:8000/api/v1/planning/requests/$REQUEST_ID \
  -H "Authorization: Bearer $TOKEN" | jq '.tasks'
```

**验收**:
- [ ] 创建请求返回request_id
- [ ] 状态最终变为 ready 或 failed
- [ ] tasks 数组非空（如果是 ready）

---

### Phase C: 后台任务完善 (Day 3)

#### C-1: 后台任务架构 ✅

**当前问题**: 无后台任务处理，大请求会超时

**解决方案**: 实现FastAPI BackgroundTasks

**实现** `backend/app/workers/planner_worker.py`:

```python
"""后台规划任务处理器"""
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models import PlanningRequest, PlannedTask
from app.models.enums import RequestStatus
from app.planning.planner import run_planner, PlanningError


def process_planning_request(request_id: str) -> None:
    """异步处理规划请求
    
    这是后台任务的主函数，由 FastAPI BackgroundTasks 调用。
    
    流程:
    1. 更新请求状态为 'planning'
    2. 运行完整规划流水线
    3. 保存结果或错误信息
    """
    db: Session = SessionLocal()
    try:
        # 获取请求
        request = db.query(PlanningRequest).filter_by(id=request_id).first()
        if not request:
            return
        
        # 更新状态
        request.status = RequestStatus.PLANNING
        request.updated_at = datetime.utcnow()
        db.commit()
        
        # 运行规划
        try:
            result = run_planner(
                raw_input=request.raw_input,
                db=db,
                planning_horizon_days=7,
            )
            
            # 更新请求状态
            request.status = RequestStatus.READY if result.status == "ready" else RequestStatus.PLANNING_ERROR
            request.parsed_intent = {
                "region": result.parsed_intent.region_description,
                "bbox": result.parsed_intent.bounding_box.dict() if result.parsed_intent.bounding_box else None,
                "priority": result.parsed_intent.priority,
            }
            request.updated_at = datetime.utcnow()
            
            # 保存任务
            for task in result.tasks:
                planned_task = PlannedTask(
                    planning_request_id=request_id,
                    satellite_id=task.satellite_id,
                    target_area={"type": "Polygon", "coordinates": []},
                    event_window={
                        "aos_time": task.acquisition_start.isoformat(),
                        "los_time": task.acquisition_end.isoformat(),
                        "max_elevation_deg": task.max_elevation_deg,
                    },
                    resource_allocation={
                        "power_w": task.power_draw,
                        "storage_mb": task.data_mb,
                        "battery_delta_percent": 2.0,
                    },
                    solver_status="optimal",
                    validator_status=task.validator_status,
                    priority_score=task.priority_score,
                )
                db.add(planned_task)
            
            db.commit()
            
        except PlanningError as e:
            request.status = RequestStatus.PLANNING_ERROR
            request.updated_at = datetime.utcnow()
            db.commit()
            
    except Exception as e:
        db.rollback()
        print(f"Background planning failed: {e}")
    finally:
        db.close()
```

**API端点更新** `backend/app/api/v1/planning.py`:

```python
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from app.workers.planner_worker import process_planning_request

router = APIRouter()

@router.post("/planning/requests")
async def create_planning_request(
    request: PlanningRequestCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建规划请求（异步处理）"""
    
    # 创建请求记录
    planning_request = PlanningRequest(
        user_id=current_user.id,
        raw_input=request.raw_input,
        status=RequestStatus.PENDING,
    )
    db.add(planning_request)
    db.commit()
    db.refresh(planning_request)
    
    # 添加后台任务
    background_tasks.add_task(
        process_planning_request,
        str(planning_request.id)
    )
    
    return {
        "id": str(planning_request.id),
        "status": "pending",
        "message": "Planning request submitted. Use GET to poll status.",
    }
```

**验收**:
- [ ] 后台任务不阻塞HTTP响应
- [ ] 任务状态正确更新
- [ ] 数据库正确保存结果

---

#### C-2: 错误处理完善 ✅

**任务**: 增强错误处理和边界情况

**实现** `backend/app/core/exceptions.py`:

```python
"""统一异常处理"""
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

class AppException(Exception):
    """应用基础异常"""
    def __init__(self, code: str, message: str, status_code: int = 400):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)

class ParsingFailedError(AppException):
    """意图解析失败"""
    def __init__(self, message: str = "Failed to parse natural language input"):
        super().__init__("PARSING_FAILED", message, 422)

class InfeasibleError(AppException):
    """无解"""
    def __init__(self, message: str = "No feasible schedule found"):
        super().__init__("INFEASIBLE", message, 422)

class ValidationFailedError(AppException):
    """验证失败"""
    def __init__(self, message: str = "Task failed physical validation"):
        super().__init__("VALIDATION_FAILED", message, 422)

class SatelliteNotFoundError(AppException):
    """卫星不存在"""
    def __init__(self, message: str = "Satellite not found"):
        super().__init__("SATELLITE_NOT_FOUND", message, 404)

async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """统一异常处理"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": {},
                "retryable": exc.code in ["PARSING_FAILED", "VALIDATION_FAILED", "INFEASIBLE"],
            }
        }
    )
```

**注册到main.py**:
```python
from app.core.exceptions import AppException, app_exception_handler

app.add_exception_handler(AppException, app_exception_handler)
```

**验收**:
- [ ] 所有错误返回标准格式
- [ ] 错误码正确
- [ ] retryable字段正确

---

### Phase D: 前端完善 (Day 4)

#### D-1: 历史记录功能 ✅

**任务**: 完善最近请求列表显示

**更新** `frontend/src/pages/PlanningPage.tsx`:

```typescript
// 添加历史记录查询
const { data: requests = [], isLoading: isLoadingHistory } = useQuery({
  queryKey: ["requests"],
  queryFn: () => planningApi.listRequests(),
  refetchInterval: 30000, // 每30秒刷新
});

// 历史记录表格组件
function RequestHistoryTable({ requests, onSelect }: {
  requests: PlanningRequest[];
  onSelect: (id: string) => void;
}) {
  return (
    <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-lg border border-slate-200 dark:border-slate-700 p-6">
      <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
        <Clock className="w-5 h-5" />
        Recent Requests
      </h3>
      
      {requests.length === 0 ? (
        <div className="text-center py-8 text-slate-500">
          <p>No planning requests yet</p>
        </div>
      ) : (
        <div className="space-y-2">
          {requests.map((req) => (
            <div
              key={req.id}
              onClick={() => onSelect(req.id)}
              className="flex items-center justify-between p-3 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-700 cursor-pointer transition"
            >
              <div>
                <p className="font-medium text-slate-800 dark:text-white">
                  {req.raw_input.substring(0, 50)}...
                </p>
                <p className="text-sm text-slate-500">
                  {formatRelativeTime(req.created_at)}
                </p>
              </div>
              <StatusBadge status={req.status} />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
```

**API方法** `frontend/src/lib/api.ts`:

```typescript
async listRequests(): Promise<PlanningRequest[]> {
  const response = await this.client.get("/planning/requests");
  return response.data;
}
```

**验收**:
- [ ] 显示最近请求列表
- [ ] 点击可查看详情
- [ ] 状态正确显示

---

#### D-2: 响应式布局优化 ✅

**任务**: 优化移动端显示

**实现**: 使用 Tailwind 响应式类

```tsx
// 主要布局
<div className="grid grid-cols-1 lg:grid-cols-4 gap-4 p-4">
  {/* 移动端: 全宽 */}
  <div className="lg:col-span-3">
    {/* 甘特图或地图 */}
  </div>
  {/* 移动端: 隐藏侧边栏 */}
  <div className="hidden lg:block">
    {/* 任务列表 */}
  </div>
</div>

// 甘特图响应式
<GanttChart 
  className="w-full overflow-x-auto"
  height={isMobile ? 200 : 400}
/>
```

**验收**:
- [ ] 桌面端: 双栏布局
- [ ] 移动端: 单栏布局
- [ ] 无水平滚动条

---

#### D-3: Loading状态优化 ✅

**任务**: 添加骨架屏和进度指示

```tsx
// 骨架屏组件
function ScheduleSkeleton() {
  return (
    <div className="animate-pulse space-y-4">
      <div className="h-8 bg-slate-200 rounded w-1/4"></div>
      <div className="h-64 bg-slate-200 rounded"></div>
      <div className="h-32 bg-slate-200 rounded"></div>
    </div>
  );
}

// 使用
{isLoading ? (
  <ScheduleSkeleton />
) : scheduledData ? (
  <ScheduleViewer ... />
) : null}
```

**验收**:
- [ ] 加载中显示骨架屏
- [ ] 无布局跳动
- [ ] 进度条正确

---

### Phase E: 测试与验证 (Day 5)

#### E-1: 单元测试完善 ✅

**任务**: 确保核心模块测试覆盖

```bash
# 运行后端测试
cd backend
pytest tests/ --cov=app --cov-report=term-missing -v

# 期望输出
# =========== 100 passed, 5 skipped in 12.34s ===========
# Coverage: app/models/ 100%, app/orbit/ 95%, app/planning/ 90%
```

**关键测试用例**:

| 模块 | 测试文件 | 覆盖函数 |
|------|----------|----------|
| Solver | test_solver.py | solve(), 6约束 |
| Validator | test_validator.py | validate_task(), 7检查 |
| Planner | test_planner.py | run_planner() |
| Intent | test_intent.py | parse(), fallback |
| Orbit | test_propagation.py | calculate_imaging_windows |

---

#### E-2: 集成测试 ✅

**任务**: 端到端流程测试

```bash
# 运行集成测试
pytest tests/integration/ -v

# 测试场景
# 1. auth: register → login → me
# 2. planning: parse → create → poll → ready
# 3. satellites: list → get → overpass
```

**Playwright E2E测试** `frontend/tests/e2e/planning.spec.ts`:

```typescript
import { test, expect } from '@playwright/test';

test.describe('Planning Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.fill('[name="email"]', 'e2e@example.com');
    await page.fill('[name="password"]', 'Test123!');
    await page.click('button[type="submit"]');
  });

  test('complete planning flow', async ({ page }) => {
    // 1. Navigate to planning
    await page.click('text=Planning');
    
    // 2. Enter request
    await page.fill('textarea', 'Image Tokyo Bay next 48 hours');
    await page.click('text=Parse Intent');
    
    // 3. Wait for intent card
    await expect(page.locator('text=Tokyo Bay')).toBeVisible({ timeout: 10000 });
    
    // 4. Generate schedule
    await page.click('text=Schedule Now');
    
    // 5. Wait for schedule
    await expect(page.locator('text=Schedule')).toBeVisible({ timeout: 30000 });
    await expect(page.locator('text=task')).toBeVisible({ timeout: 30000 });
  });
});
```

**验收**:
- [ ] 100+单元测试通过
- [ ] Playwright E2E通过
- [ ] 覆盖�� > 85%

---

#### E-3: 性能测试 ✅

**任务**: 验证求解器性能

```bash
# 性能基准测试
docker exec apex-api python -c "
import time
from app.planning.solver import solve
from app.planning.solver_types import SolverInput, RequestData, SatelliteData

# Test: 5 satellites × 10 windows × 3 requests
requests = [RequestData(id=str(i), priority_score=0.8) for i in range(3)]
satellites = [SatelliteData(id=str(i), name=f'SAT-{i}', battery_capacity=100, storage_capacity=50000) for i in range(5)]

# Generate windows
windows = {str(i): [
    {'aos': ..., 'los': ..., 'max_elevation_deg': 45, 'illumination_pct': 0.8, 
     'duration_seconds': 30, 'power_draw': 1.0, 'data_mb': 100}
    for _ in range(10)
] for i in range(5)}

input = SolverInput(requests=requests, satellites=satellites, imaging_windows=windows)

start = time.time()
result = solve(input, time_limit_ms=5000)
elapsed = (time.time() - start) * 1000

print(f'Solve time: {elapsed:.1f}ms')
print(f'Status: {result.status}')
print(f'Assignments: {len(result.assignments)}')
assert elapsed < 5000, f'Solve took too long: {elapsed}ms'
"
```

**验收**:
- [ ] 求解时间 < 5秒
- [ ] 内存使用 < 500MB
- [ ] 端到端时间 < 30秒

---

### Phase F: 演示准备 (Day 6)

#### F-1: 演示数据准备 ✅

**任务**: 准备演示用例

**演示用例集合** `backend/scripts/demo_cases.py`:

```python
"""Apex MVP演示用例"""

DEMO_CASES = [
    {
        "name": "Tokyo Bay Flood Monitoring",
        "input": "Image Tokyo Bay next 48 hours at resolution better than 3m for flood monitoring",
        "expected_region": "Tokyo Bay",
        "expected_priority": "normal",
    },
    {
        "name": "Southeast Asia Emergency",
        "input": "URGENT: Need to image all flood zones in Southeast Asia immediately",
        "expected_region": "Southeast Asia",
        "expected_priority": "urgent",
    },
    {
        "name": "Beijing Clear Sky",
        "input": "Image Beijing area next week, resolution better than 10m",
        "expected_region": "Beijing",
        "expected_priority": "normal",
    },
    {
        "name": "Nairobi Agriculture",
        "input": "Monitor agricultural areas near Nairobi for drought assessment",
        "expected_region": "Nairobi",
        "expected_priority": "normal",
    },
]

def run_demo_case(case: dict):
    """运行单个演示用例"""
    print(f"\n{'='*60}")
    print(f"Demo Case: {case['name']}")
    print(f"{'='*60}")
    print(f"Input: {case['input']}")
    print()
    
    # 执行规划
    result = run_planner(raw_input=case["input"], db=db)
    
    print(f"Status: {result.status}")
    print(f"Region: {result.parsed_intent.region_description}")
    print(f"Priority: {result.parsed_intent.priority}")
    print(f"Tasks: {len(result.tasks)}")
    
    if result.tasks:
        for i, task in enumerate(result.tasks[:3]):
            print(f"  Task {i+1}: {task.satellite_id[:8]}... "
                  f"@ {task.acquisition_start.strftime('%Y-%m-%d %H:%M')}")
    
    return result

def main():
    print("Apex MVP Demo Suite")
    print("=" * 60)
    
    for case in DEMO_CASES:
        try:
            result = run_demo_case(case)
            status = "✓" if result.status == "ready" else "⚠"
            print(f"\n{status} {case['name']}: {result.status}")
        except Exception as e:
            print(f"\n✗ {case['name']}: {e}")
    
    print("\n" + "=" * 60)
    print("Demo complete!")
```

**执行**:
```bash
docker exec apex-api python scripts/demo_cases.py
```

**验收**:
- [ ] 至少3个用例成功
- [ ] 输出清晰可读
- [ ] 错误信息明确

---

#### F-2: 演示脚本 ✅

**任务**: 创建一键演示脚本

**脚本** `scripts/demo.sh`:

```bash
#!/bin/bash
# Apex MVP 一键演示脚本

set -e

echo "=========================================="
echo "  Apex MVP - Satellite Task Planning"
echo "=========================================="
echo ""

# 1. 检查服务状态
echo "1. Checking services..."
curl -s http://localhost:8000/health | jq . || {
    echo "ERROR: Backend not responding"
    exit 1
}

# 2. 获取token
echo ""
echo "2. Authenticating..."
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@apex.space","password":"Demo123!"}' \
  | jq -r '.access_token')

if [ "$TOKEN" = "null" ]; then
    echo "   Creating demo user..."
    curl -s -X POST http://localhost:8000/api/v1/auth/register \
      -H "Content-Type: application/json" \
      -d '{"email":"demo@apex.space","password":"Demo123!","name":"Demo User"}' > /dev/null
    TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
      -H "Content-Type: application/json" \
      -d '{"email":"demo@apex.space","password":"Demo123!"}' \
      | jq -r '.access_token')
fi

echo "   ✓ Authenticated"
echo ""

# 3. 创建规划请求
echo "3. Creating planning request..."
RESP=$(curl -s -X POST http://localhost:8000/api/v1/planning/requests \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"raw_input":"Image Tokyo Bay next 48 hours at resolution better than 3m"}')

echo "$RESP" | jq '{request_id: .id, status: .status}'
REQUEST_ID=$(echo "$RESP" | jq -r '.id')

# 4. 轮询结果
echo ""
echo "4. Waiting for planning to complete..."
for i in {1..15}; do
    sleep 2
    STATUS=$(curl -s "http://localhost:8000/api/v1/planning/requests/$REQUEST_ID" \
      -H "Authorization: Bearer $TOKEN" | jq -r '.status')
    echo "   Attempt $i: $STATUS"
    
    if [ "$STATUS" = "ready" ]; then
        break
    fi
done

# 5. 获取结果
echo ""
echo "5. Planning Result:"
curl -s "http://localhost:8000/api/v1/planning/requests/$REQUEST_ID" \
  -H "Authorization: Bearer $TOKEN" | jq '{
    status: .status,
    parsed_intent: .parsed_intent,
    tasks_count: (.tasks | length),
    tasks: [.tasks[] | {satellite_id: .satellite_id[0:8], time: .event_window.aos_time, elevation: .event_window.max_elevation_deg}]
  }'

echo ""
echo "=========================================="
echo "  Demo Complete!"
echo "=========================================="
```

**执行权限和运行**:
```bash
chmod +x scripts/demo.sh
./scripts/demo.sh
```

**验收**:
- [ ] 一键执行无错误
- [ ] 30秒内完成演示
- [ ] 输出清晰可读

---

#### F-3: 文档完善 ✅

**任务**: 更新README和使用指南

**更新内容**:

```markdown
# Quick Start (5分钟演示)

## 1. 启动服务
```bash
cd /Users/ziye/Downloads/Apex\ code
make dev-detached
sleep 30
make migrate
make seed
```

## 2. 运行演示
```bash
./scripts/demo.sh
```

## 3. 访问前端
浏览器打开: http://localhost:5173

## 演示用例
1. "Image Tokyo Bay next 48 hours at resolution better than 3m"
2. "URGENT: Image all flood zones in Southeast Asia"
3. "Monitor Beijing area next week, resolution better than 10m"
```

---

## 4. 技术实现方案

### 4.1 技术栈

| 层级 | 技术 | 用途 |
|------|------|------|
| 前端 | React 18 + TypeScript | UI框架 |
| 前端 | TailwindCSS + shadcn/ui | 样式组件 |
| 前端 | React Query + Zustand | 状态管理 |
| 前端 | Leaflet + Recharts | 可视化 |
| 后端 | FastAPI | API框架 |
| 后端 | SQLAlchemy 2 | ORM |
| 后端 | OR-Tools | 约束求解 |
| 后端 | skyfield | 轨道计算 |
| 数据库 | PostgreSQL 15 | 主数据库 |
| 缓存 | Redis 7 | 会话/队列 |
| LLM | OpenAI GPT-4o | 意图解析 |

### 4.2 架构图

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (React)                        │
│  ┌──────────┐  ┌───────────┐  ┌──────────────────────────┐ │
│  │ Chat UI  │  │  Gantt    │  │  Map (Leaflet)            │ │
│  │(NL Input)│  │  Chart    │  │  - Target Area            │ │
│  └────┬─────┘  └─────┬─────┘  └────────────┬─────────────┘ │
└───────┼───────────────┼────────────────────┼────────────────┘
        │               │                     │
        ▼               ▼                     ▼
┌─────────────────────────────────────────────────────────────┐
│                  API Gateway (FastAPI)                      │
│  ┌─────────────┐  ┌────────────────┐  ┌──────────────────┐  │
│  │  /auth/*   │  │  /planning/*   │  │  /satellites/*   │  │
│  └─────────────┘  └───────┬────────┘  └──────────────────┘  │
└────────────────────────────┼───────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
┌────────────────┐  ┌────────────────┐  ┌────────────────────┐
│  Intent Parser │  │  CP-SAT Solver │  │  Physics Validator │
│  (GPT-4o)      │  │  (OR-Tools)    │  │  (7 checks)        │
└────────────────┘  └────────────────┘  └────────────────────┘
        │                    │                    │
        └────────────────────┼────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                 Orbit Engine (skyfield + sgp4)              │
│  - TLE propagation    - Overpass windows                    │
│  - Imaging windows    - Sun angle calculation               │
└─────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                      Data Layer                              │
│  PostgreSQL (metadata)  │  CelesTrak (TLE data)            │
│  Redis (sessions)       │  Open-Meteo (weather)            │
└─────────────────────────────────────────────────────────────┘
```

### 4.3 数据流

```
1. User Input (NL)
       │
       ▼
2. LLM Intent Parser ──► ParsedIntent { region, priority, time, ... }
       │
       ▼
3. Geocoding ──► BoundingBox { sw_lat, sw_lng, ne_lat, ne_lng }
       │
       ▼
4. Satellite Filter ──► EligibleSatellites[]
       │
       ▼
5. Imaging Windows ──► { sat_id: [ImagingWindow, ...], ... }
       │
       ▼
6. CP-SAT Solver ──► Assignments[]
       │
       ▼
7. Physics Validation ──► ValidatedTasks[]
       │
       ▼
8. Output: Schedule (JSON) + Gantt + Map
```

---

## 5. 数据API集成计划

### 5.1 当前已集成

| API | 库 | 用途 | 状态 |
|-----|-----|------|------|
| CelesTrak | httpx | TLE获取 | ✅ 完整 |
| skyfield | skyfield | 轨道计算 | ✅ 完整 |
| OpenAI | openai | 意图解析 | ✅ 完整 |

### 5.2 推荐新增集成

#### 5.2.1 Open-Meteo 天气API (P1)

**用途**: 预测云层覆盖，影响成像窗口选择

**实现** `backend/app/services/weather_service.py`:

```python
"""天气服务 - 使用 Open-Meteo API"""
import httpx
from datetime import datetime, timedelta
from typing import Optional

class WeatherService:
    """天气数据获取服务"""
    
    BASE_URL = "https://api.open-meteo.com/v1"
    
    async def get_cloud_cover(
        self,
        lat: float,
        lon: float,
        start_date: datetime,
        days: int = 7
    ) -> list[dict]:
        """获取指定区域的云量预测
        
        Args:
            lat: 纬度
            lon: 经度
            start_date: 开始日期
            days: 预报天数
            
        Returns:
            每日云量数据列表
        """
        params = {
            "latitude": lat,
            "longitude": lon,
            "daily": "cloud_cover_mean,precipitation_sum",
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": (start_date + timedelta(days=days)).strftime("%Y-%m-%d"),
            "timezone": "UTC",
        }
        
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{self.BASE_URL}/forecast", params=params)
            resp.raise_for_status()
            data = resp.json()
            
        return [
            {
                "date": date,
                "cloud_cover": data["daily"]["cloud_cover_mean"][i],
                "precipitation": data["daily"]["precipitation_sum"][i],
            }
            for i, date in enumerate(data["daily"]["time"])
        ]
    
    def filter_good_imaging_days(
        self,
        cloud_forecasts: list[dict],
        max_cloud_cover: float = 50.0
    ) -> list[dict]:
        """过滤适合成像的日期
        
        Args:
            cloud_forecasts: 云量预报列表
            max_cloud_cover: 最大云量阈值 (%)

        Returns:
            适合成像的日期列表
        """
        return [
            f for f in cloud_forecasts
            if f["cloud_cover"] <= max_cloud_cover
        ]

# Singleton
weather_service = WeatherService()
```

**集成到成像窗口计算**:

```python
# backend/app/orbit/imaging.py
from app.services.weather_service import weather_service

async def calculate_imaging_windows_with_weather(...):
    # 计算成像窗口
    windows = calculate_imaging_windows(...)
    
    # 获取云量预报
    center_lat = (bbox["sw_lat"] + bbox["ne_lat"]) / 2
    center_lon = (bbox["sw_lng"] + bbox["ne_lng"]) / 2
    forecasts = await weather_service.get_cloud_cover(center_lat, center_lon, start_time, 7)
    
    # 过滤低云量窗口
    good_days = weather_service.filter_good_imaging_days(forecasts)
    
    return [w for w in windows if w.date in good_days]
```

**验收**:
- [ ] API调用成功
- [ ] 返回云量数据
- [ ] 集成到规划流程

---

#### 5.2.2 Nominatim 地理编码 (P1)

**用途**: 增强地理编码能力

**当前状态**: 已实现307区域的内置字典 + 模糊匹配

**增强**: 添加Nominatim API后备

```python
# backend/app/services/geocoding_service.py

class NominatimGeocoder:
    """Nominatim地理编码器"""
    
    BASE_URL = "https://nominatim.openstreetmap.org"
    
    async def geocode(self, query: str) -> Optional[dict]:
        """地理编码查询"""
        params = {
            "q": query,
            "format": "json",
            "limit": 1,
        }
        headers = {"User-Agent": "Apex-Satellite-Planning/1.0"}
        
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.BASE_URL}/search",
                params=params,
                headers=headers,
            )
            resp.raise_for_status()
            data = resp.json()
            
        if not data:
            return None
            
        return {
            "lat": float(data[0]["lat"]),
            "lon": float(data[0]["lon"]),
            "display_name": data[0]["display_name"],
            "bounding_box": data[0].get("boundingbox"),
        }
```

---

## 6. 测试计划

### 6.1 测试金字塔

```
                    ┌─────────┐
                    │   E2E   │  ← Playwright (5 tests)
                    ├─────────┤
                    │Integration│ ← API tests (20 tests)
                    ├─────────┤
                    │  Unit   │  ← pytest (100+ tests)
                    └─────────┘
```

### 6.2 测试覆盖目标

| 模块 | 覆盖目标 | 当前 | 差距 |
|------|----------|------|------|
| app/models/ | 100% | 100% | 0 |
| app/orbit/ | 95% | 90% | +5 |
| app/planning/ | 90% | 85% | +5 |
| app/api/ | 80% | 70% | +10 |
| app/services/ | 70% | 50% | +20 |
| **总计** | **85%** | **86%** | **-1** |

### 6.3 关键测试场景

| ID | 场景 | 输入 | 预期输出 |
|----|------|------|----------|
| T-1 | 正常规划 | "Image Tokyo Bay next 48h" | status=ready, tasks>0 |
| T-2 | 紧急规划 | "URGENT: Image area" | priority=urgent |
| T-3 | 无卫星 | 无TLE数据 | status=failed, error |
| T-4 | 无区域 | "Take a photo" | status=failed, error |
| T-5 | 求解超时 | 大量请求 | status=suboptimal |
| T-6 | 验证失败 | 低仰角窗口 | task status=failed |
| T-7 | 历史记录 | 查看请求列表 | 返回所有请求 |

---

## 7. 演示方案

### 7.1 演示环境要求

| 项目 | 最低要求 | 推荐 |
|------|----------|------|
| CPU | 4核 | 8核 |
| 内存 | 8GB | 16GB |
| 磁盘 | 20GB | 50GB |
| 网络 | 10Mbps | 100Mbps |
| 浏览器 | Chrome/Firefox | Chrome latest |

### 7.2 演示流程 (10分钟)

```
┌──────────────────────────────────────────────┐
│ 1. 项目介绍 (1分钟)                           │
│    - 痛点: 卫星任务规划复杂耗时                │
│    - 方案: NL输入 → AI规划 → 可执行计划       │
└──────────────────────────────────────────────┘
                      │
                      ▼
┌──────────────────────────────────────────────┐
│ 2. 技术演示 (5分钟)                           │
│    a) 前端UI展示 (1min)                       │
│       - 打开浏览器 http://localhost:5173       │
│       - 展示输入框和历史记录                   │
│                                              │
│    b) 意图解析 (1min)                         │
│       - 输入: "Image Tokyo Bay next 48h"      │
│       - 展示解析结果卡片                       │
│                                              │
│    c) 规划执行 (2min)                         │
│       - 点击 Schedule Now                     │
│       - 轮询状态直到 ready                     │
│       - 展示甘特图和地图                       │
│                                              │
│    d) 任务详情 (1min)                         │
│       - 点击任务查看详情                       │
│       - 展示仰角、时间、电量等                 │
└──────────────────────────────────────────────┘
                      │
                      ▼
┌──────────────────────────────────────────────┐
│ 3. 技术架构说明 (2分钟)                       │
│    - LLM意图解析 → CP-SAT求解 → 物理验证      │
│    - 展示数据流图                              │
│    - 强调关键创新: NL接口 + 约束求解          │
└──────────────────────────────────────────────┘
                      │
                      ▼
┌──────────────────────────────────────────────┐
│ 4. Q&A (2分钟)                               │
│    - 技术细节回答                              │
│    - 商业模式讨论                              │
│    - 下一步计划                                │
└──────────────────────────────────────────────┘
```

### 7.3 演示检查清单

**演示前** (5分钟准备):
- [ ] `make dev-detached` 服务运行中
- [ ] `make seed` 数据已填充
- [ ] 数据库有4+卫星
- [ ] 浏览器访问 localhost:5173 正常
- [ ] API文档可访问 localhost:8000/docs
- [ ] 演示用例准备好

**演示中**:
- [ ] 输入NL请求
- [ ] 等待规划完成 (<30秒)
- [ ] 展示甘特图
- [ ] 展示地图
- [ ] 点击任务详情

**演示后**:
- [ ] 回答技术问题
- [ ] 讨论商业模式
- [ ] 收集反馈

---

## 8. 时间线与里程碑

### 8.1 详细时间线

```
Week 1: 基础完善
├── Day 1: 环境配置 + 数据库 + Seed数据
├── Day 2: 端到端集成测试
├── Day 3: 后台任务完善 + 错误处理
├── Day 4: 前端完善 (历史记录、响应式)
├── Day 5: 测试 + 性能优化
└── Day 6: 演示准备 + 文档

Week 2: 可选增强 (Rigor)
├── Day 7-10: Rigor MVP开发
└── Day 11-12: 演示 + 发布
```

### 8.2 里程碑

| Milestone | 日期 | 验收标准 |
|-----------|------|----------|
| M1: 环境就绪 | Day 1 | make dev + seed 成功 |
| M2: API可用 | Day 2 | 端到端API测试通过 |
| M3: 前后端集成 | Day 3 | 前端完整交互 |
| M4: 质量达标 | Day 5 | 100+测试通过, 85%覆盖 |
| M5: 可演示 | Day 6 | demo.sh 一键演示 |
| **M6: MVP完成** | **Day 6** | **全部验收标准通过** |

### 8.3 每日Standup检查点

```markdown
### Daily Standup

**昨日完成**:
- [ ] 任务列表

**今日计划**:
- [ ] 任务列表

**阻碍**:
- [ ] 问题列表

**验收确认**:
- [ ] 验收标准检查
```

---

## 9. 风险与应对

### 9.1 技术风险

| 风险 | 概率 | 影响 | 应对措施 |
|------|------|------|----------|
| TLE数据过期/不可用 | 中 | 高 | 本地缓存 + 定期刷新 |
| LLM API超时 | 低 | 中 | 关键词兜底 + 重试 |
| CP-SAT求解超时 | 低 | 中 | 5秒超时 + 次优解 |
| Docker内存不足 | 低 | 中 | 8GB+配置 |
| 前端构建失败 | 低 | 低 | CI检查 |

### 9.2 业务风险

| 风险 | 概率 | 影响 | 应对措施 |
|------|------|------|----------|
| OpenAI API成本超支 | 中 | 中 | 设置配额 + 关键词兜底 |
| CelesTrak服务不可用 | 低 | 中 | 备用数据源 |
| 用户体验不佳 | 中 | 中 | 迭代优化 |

### 9.3 缓解措施详细

#### 风险1: TLE数据过期

```python
# 缓解: 实现TLE缓存和过期检查
@app.on_event("startup")
async def refresh_tle_if_needed():
    """启动时检查TLE是否需要刷新"""
    db = SessionLocal()
    oldest = db.query(Satellite).order_by(Satellite.tle_epoch.asc()).first()
    
    if oldest:
        age_hours = (datetime.utcnow() - oldest.tle_epoch).total_seconds() / 3600
        if age_hours > 24:
            # 需要刷新
            await refresh_tle_data(db)
    
    db.close()
```

#### 风险2: LLM API失败

```python
# 缓解: 多级降级策略
def parse_intent_with_fallback(raw_input: str) -> ParsedIntent:
    # 1. 尝试GPT-4o
    try:
        return gpt_parse(raw_input)
    except LLMError as e:
        print(f"GPT-4o failed: {e}")
    
    # 2. 尝试GPT-3.5
    try:
        return gpt35_parse(raw_input)
    except LLMError as e:
        print(f"GPT-3.5 failed: {e}")
    
    # 3. 关键词兜底
    return keyword_fallback_parse(raw_input)
```

#### 风险3: 求解超时

```python
# 缓解: 渐进式时间限制
def solve_with_progressive_timeout(input: SolverInput) -> SolverResult:
    # 首先尝试快速求解
    result = solve(input, time_limit_ms=1000)
    if result.status == "optimal":
        return result
    
    # 如果失败，增加时间
    result = solve(input, time_limit_ms=3000)
    if result.status in ["optimal", "feasible"]:
        return result
    
    # 最后尝试
    return solve(input, time_limit_ms=5000)
```

---

## 10. 附录：命令参考

### 10.1 开发命令

```bash
# ===== 开发环境 =====
cd /Users/ziye/Downloads/Apex\ code

# 启动开发环境
make dev                  # 前台启动
make dev-detached        # 后台启动

# 查看日志
make logs                # 所有服务
make logs-api           # 仅后端
make logs-frontend      # 仅前端

# 停止
make down               # 停止服务
make down-v             # 停止并删除数据

# ===== 数据库 =====
make migrate            # 执行迁移
make makemigrations     # 创建迁移
make seed               # 填充种子数据

# ===== 测试 =====
make test               # 运行所有测试
make test-backend       # 仅后端测试
make test-frontend     # 仅前端测试

# ===== 代码质量 =====
make lint               # 代码检查
make typecheck          # 类型检查
make coverage           # 覆盖率报告

# ===== 清理 =====
make clean              # 清理临时文件
```

### 10.2 演示命令

```bash
# 一键演示
./scripts/demo.sh

# 分步演示
# 1. 启动服务
make dev-detached
sleep 30

# 2. 填充数据
make seed

# 3. 获取token
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@apex.space","password":"Demo123!"}'

# 4. 创建规划
curl -X POST http://localhost:8000/api/v1/planning/requests \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"raw_input":"Image Tokyo Bay next 48 hours"}'

# 5. 查看结果
curl http://localhost:8000/api/v1/planning/requests/<ID> \
  -H "Authorization: Bearer <TOKEN>"
```

### 10.3 Docker命令

```bash
# 查看服务状态
docker ps

# 进入容器
make shell-api          # 后端shell
make shell-frontend    # 前端shell

# 重建服务
docker compose down
docker compose up --build -d

# 查看日志
docker compose logs -f api
docker compose logs -f frontend
docker compose logs -f db
```

### 10.4 环境变量清单

```bash
# 必需
POSTGRES_USER=apex
POSTGRES_PASSWORD=<secret>
POSTGRES_DB=apexdb
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
REDIS_HOST=localhost
REDIS_PORT=6379
JWT_SECRET=<secret>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
OPENAI_API_KEY=<key>

# 可选
API_BASE_URL=https://api.openai.com/v1
TLE_REFRESH_HOURS=24
```

---

## 文档更新记录

| 版本 | 日期 | 作者 | 变更 |
|------|------|------|------|
| 1.0 | 2026-07-05 | AI Agent | 初始版本 |

---

*本文档为 Apex MVP 开发计划，按优先级分6个Phase，预计6个工作日完成。*
