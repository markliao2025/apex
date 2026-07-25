# Apex

[![CI](https://github.com/markliao2025/apex/actions/workflows/ci.yml/badge.svg)](https://github.com/markliao2025/apex/actions/workflows/ci.yml)
[![Security](https://github.com/markliao2025/apex/actions/workflows/security.yml/badge.svg)](https://github.com/markliao2025/apex/actions/workflows/security.yml)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)

**开源、可审计的星座管理与空间风险决策工作台。**

Apex 面向小型卫星团队、研究者和开源贡献者，把星座资产管理、任务规划、合成交会
事件回放、计划影响分析和证据导出连接成一条可重复的工作流。Phase 0 的目标不是
替代飞行动力学系统，而是先建立一套透明、确定、可验证的空间态势感知（SSA）产品
基础。

> **Safety boundary:** synthetic demo only — not for operational or flight-safety
> decisions. Apex Phase 0 does not compute collision probability (Pc), ingest
> operational CDMs, recommend maneuvers, generate post-maneuver trajectories, or
> execute commands.

![Apex Phase 0 暗黑界面概念图](docs/assets/apex-phase0-dark-interface.png)

*Phase 0 暗黑界面设计方向（concept view），不是当前运行截图。图中所有风险值均为
合成输入；该图不代表飞行认证、真实风险预测或机动执行能力。*

## 产品解决什么问题

空间风险数据本身并不等于可执行决策。团队还需要知道数据从哪里来、质量是否足够、
哪些结论是输入值、某次事件会怎样影响既有计划，以及事后能否复现当时的判断。

Apex 将这些环节放进同一个工作台：

1. 用 Organization、角色和 Constellation 明确资产与数据访问范围；
2. 回放版本固定的合成交会事件，而不是依赖不可复现的临时数据；
3. 显示 provided Pc、接近距离、相对速度、数据质量和来源限制；
4. 将“假设卫星在某时间窗不可用”映射到确定性的计划 before/after 比较；
5. 导出带哈希、算法版本和安全声明的证据包，便于复核与协作。

这条工作流为后续接入授权 SSA 数据、风险趋势分析和受约束 Agent 奠定基础，但这些
后续能力不属于 Phase 0 的当前承诺。

## 核心产品能力

| 能力 | Phase 0 提供什么 | 为什么重要 |
| --- | --- | --- |
| 星座工作区 | 创建 Organization/Constellation，在角色权限下关联或移除内置目录卫星 | 防止跨组织、跨星座的数据与计划混用 |
| 星座任务规划 | 在明确星座范围内解析任务意图，并用 CP-SAT 生成简化约束下的确定性计划 | 保留原有星座管理与规划主线 |
| 合成交会回放 | 回放 `APEX-SYNTHETIC-001`，展示 provided Pc、接近距离、相对速度和事件时间 | 提供开箱即用、无需敏感数据的 SSA 产品体验 |
| 数据质量解释 | 明示协方差缺失、`apex_computed_pc=false`、来源、单位和算法版本 | 让用户区分输入事实、系统处理与能力限制 |
| 计划影响分析 | 对固定的假设性不可用窗运行 before/after 排程比较 | 把空间风险语境连接到任务资源后果 |
| 证据导出 | 导出 JSON 或 Markdown，保留 fixture SHA-256、证据哈希、限制和安全声明 | 支持复现、审查和 Build in Public |
| 开源交付 | Docker Compose 一键演示、离线测试、迁移、E2E、许可证与安全检查 | 让新用户可以本地验证，而不是只看产品说明 |

Satellite 目录记录不代表卫星所有权。Phase 0 不提供真实轨道文件或 CDM 上传。

## 五分钟体验

前提：Docker 24+ 与 Docker Compose v2。

```bash
git clone https://github.com/markliao2025/apex.git
cd apex
make demo
```

无需创建 `.env`，无需 OpenAI key，默认路径不会访问公网。等待服务健康后打开：

- 前端：<http://localhost:5173>
- API 文档：<http://localhost:8000/docs>
- Readiness：<http://localhost:8000/health/ready>

在登录页选择 **Try the synthetic demo**，然后：

1. 回放 `APEX-SYNTHETIC-001`；
2. 检查 `Pc provided · not computed` 和缺协方差警告；
3. 选择演示星座中的卫星；
4. 比较假设性不可用窗前后的计划；
5. 导出 JSON 或 Markdown 证据包。

默认 Compose 的数据库和 JWT 值只用于本机合成演示，不能用于生产。

## 能力边界

| 标签或能力 | Phase 0 的真实含义 |
| --- | --- |
| `pc_origin=provided` | Pc 来自仓库内的合成 fixture 输入 |
| `apex_computed_pc=false` | Apex 没有独立计算 Pc |
| `covariance_available=false` | 无法从协方差复算 Pc |
| `physics_verified=false` | 影响比较不是机动或轨道安全结论 |
| `synthetic_conjunction_what_if` | 仅为规划资源不可用假设 |
| 风险预测 | 尚未实现；当前是确定性的合成事件回放和计划影响分析 |
| Agent | 尚未实现；当前没有自主决策、工具调用或命令执行 Agent |
| 飞行系统 | 不集成、不下发指令、不生成机动方案，且未通过飞行认证 |

未来 Agent 只能调用有权限、可审计、可回放的 typed tools；LLM 输出不能成为轨道
事实，Agent 也不能绕过权限、伪造 Pc 或自主执行机动。

## 系统架构

```text
React UI
  ├─ Organization / constellation workspace
  ├─ Scoped task planning
  └─ Synthetic conjunction replay + planning impact + evidence export
          │
FastAPI ──┼─ OrganizationMembership authorization
          ├─ deterministic replay / validation
          ├─ CP-SAT scheduling
          └─ stable ErrorEnvelope + trace_id
          │
PostgreSQL (Alembic migration + idempotent offline bootstrap)
```

默认 Compose 启动顺序为：PostgreSQL healthy → migration → offline seed/demo
bootstrap → API ready → frontend。Redis 不在默认运行路径；可用
`--profile optional` 单独启动。

## 开发与验证

本地 Python 工具默认位于 `backend/.venv`：

```bash
make test           # 后端 + 前端非浏览器测试；默认不访问公网
make lint           # Ruff + ESLint
make typecheck      # Mypy + TypeScript
make verify         # lint + typecheck + tests + build + fixture golden hash
make test-e2e       # 对已启动的 demo 运行 API + Playwright 最小用户旅程
make audit-licenses # 检查直接依赖的开源许可证政策
make release-check  # verify + 开源/发布边界检查
```

确定性 fixture 位于
[`fixtures/demo/conjunction/apex-synthetic-001/`](fixtures/demo/conjunction/apex-synthetic-001/)。
任何哈希或黄金结果变化都应作为数据契约变更进行审查。

## API 边界

- `GET /api/v1/organizations`
- `GET|POST /api/v1/constellations`
- `GET|PATCH /api/v1/constellations/{id}`
- `GET|POST /api/v1/constellations/{id}/satellites`
- `DELETE /api/v1/constellations/{id}/satellites/{satellite_id}`
- `POST /api/v1/planning/parse`
- `POST /api/v1/planning/requests`
- `GET /api/v1/demo/status`
- `POST /api/v1/demo/session`
- `POST /api/v1/demo/replays`
- `POST /api/v1/demo/replays/{id}/planning-impact`
- `GET /api/v1/demo/replays/{id}/export?format=json|md`

旧 Planning API 只有在用户恰好可访问一个星座时才会自动选择范围，并返回
`Deprecation: true`；任何时候都不会回退到全库卫星查询。

统一错误结构：

```json
{
  "error": {
    "code": "CONSTELLATION_FORBIDDEN",
    "message": "You do not have access to this constellation.",
    "details": {"constellation_id": "..."},
    "retryable": false,
    "trace_id": "uuid"
  }
}
```

## Build in Public

无法做正式访谈不妨碍验证，但不能把点赞当需求证据。每周公开：

- 一个可运行增量；
- 一段 60–90 秒真实操作视频；
- 一个明确问题；
- 失败、卡住步骤、错误码和匿名使用数据；
- 下一周保留、删除或调整的决定。

模板、指标定义和证据日志见
[Build in Public 指南](docs/build-in-public/README.md)。六个完整日历周后才执行
Market-fit Gate；代码完成不等于 Phase 0 市场验证完成。公开路线图见
[ROADMAP.md](ROADMAP.md)。

## 生产支持状态

Phase 0 支持本地 Docker Compose 合成演示和开发测试。它**不支持**生产级异步任务
可靠性、真实 SSA 数据持久化或飞行安全决策。`docker-compose.prod.yml` 只作为安全
配置参考；在加入可靠队列、备份/恢复演练、监控和 PostgreSQL 迁移测试前，不应宣称
生产就绪。

详见 [支持矩阵与限制](docs/operations/SUPPORT_MATRIX.md)。

## 贡献与开源

项目采用 [Apache-2.0](LICENSE) 许可证，合成 fixture 采用 CC0-1.0。贡献使用 DCO
`Signed-off-by`，见 [CONTRIBUTING.md](CONTRIBUTING.md)。安全问题请按
[SECURITY.md](SECURITY.md) 私下报告。

- 数据与模型政策：[docs/legal/DATA_AND_MODEL_POLICY.md](docs/legal/DATA_AND_MODEL_POLICY.md)
- 第三方与生成资产登记：[docs/legal/THIRD_PARTY_ASSETS.md](docs/legal/THIRD_PARTY_ASSETS.md)
- 架构决策：[docs/architecture/](docs/architecture/)
- Phase 0 执行合同：[PHASE0_AI_EXECUTION_PLAN.md](PHASE0_AI_EXECUTION_PLAN.md)

## License

Code: Apache-2.0. Synthetic demo fixture: CC0-1.0.
