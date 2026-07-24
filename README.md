# Apex

面向开放协作的星座任务规划与空间风险“决策演示”工作台。

Phase 0 保留了原有星座任务规划，并增加一个完全合成、可重复的交会事件回放：
用户可以看到数据质量、仓库 fixture 的来源和哈希，以及“假设某颗卫星在一个时间窗不可用”
对计划产生的影响。

> **Safety boundary:** synthetic demo only — not for operational or flight-safety
> decisions. Apex Phase 0 does not compute collision probability (Pc), ingest
> operational CDMs, recommend maneuvers, or generate post-maneuver trajectories.

## 五分钟体验

前提：Docker 24+ 与 Docker Compose v2。

```bash
git clone <your-repository-url> apex
cd apex
make demo
```

无需创建 `.env`，无需 OpenAI key，也不会在默认路径访问公网。等待服务健康后打开：

- 前端：http://localhost:5173
- API 文档：http://localhost:8000/docs
- Readiness：http://localhost:8000/health/ready

在登录页选择 **Try the synthetic demo**，然后：

1. 回放 `APEX-SYNTHETIC-001`；
2. 检查 `Pc provided · not computed` 和缺协方差警告；
3. 选择演示星座中的卫星；
4. 比较假设性不可用窗前后的计划；
5. 导出 JSON 或 Markdown 证据包。

默认 Compose 的数据库和 JWT 值只用于本机合成演示，不能用于生产。

## 用户现在能做什么

- 注册后获得隔离的个人 Organization 和默认 Constellation；
- 创建星座，并关联或移除内置演示 Satellite 目录记录；
- 在明确选择的星座范围内解析任务意图和生成计划；
- 回放带 CC0 来源、canonical SHA-256 和黄金输出的合成交会事件；
- 查看 provided Pc、数据质量降级原因和明确限制；
- 运行假设性卫星不可用窗的 before/after 计划比较；
- 导出可复查的演示证据包。

Satellite 目录记录不代表卫星所有权。Phase 0 不提供真实轨道文件或 CDM 上传。

## 关键真实性说明

| 标签 | Phase 0 含义 |
| --- | --- |
| `pc_origin=provided` | Pc 来自合成 fixture 输入 |
| `apex_computed_pc=false` | Apex 没有独立计算 Pc |
| `covariance_available=false` | 无法从协方差复算 Pc |
| `physics_verified=false` | 影响比较不是机动或轨道安全结论 |
| `synthetic_conjunction_what_if` | 仅为规划资源不可用假设 |

目前没有 LLM Agent。Phase 0 先把有权限边界、确定性输入输出和可审计工具契约做实；
Agent 只能在后续阶段调用这些受约束工具，不能绕过权限、伪造 Pc 或自主执行机动。

## 架构

```text
React UI
  ├─ Constellation management
  ├─ Existing scoped planning
  └─ Synthetic replay + planning impact
          │
FastAPI ──┼─ OrganizationMembership authorization
          ├─ deterministic replay/validation
          ├─ CP-SAT scheduling
          └─ stable ErrorEnvelope + trace_id
          │
PostgreSQL (Alembic migration + idempotent offline bootstrap)
```

默认 Compose 启动顺序为：PostgreSQL healthy → migration → offline seed/demo bootstrap
→ API ready → frontend。Redis 不在默认运行路径；可用 `--profile optional` 单独启动。

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
`fixtures/demo/conjunction/apex-synthetic-001/`。任何哈希或黄金结果变化都应作为
数据契约变更进行审查。

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
- 下一周保留/删除/调整的决定。

模板、指标定义和证据日志见 [Build in Public 指南](docs/build-in-public/README.md)。
六个完整日历周后才执行 Market-fit Gate；代码完成不等于 Phase 0 市场验证完成。
公开路线图见 [ROADMAP.md](ROADMAP.md)。

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
- 第三方资产登记：[docs/legal/THIRD_PARTY_ASSETS.md](docs/legal/THIRD_PARTY_ASSETS.md)
- 架构决策：[docs/architecture/](docs/architecture/)
- Phase 0 执行合同：[PHASE0_AI_EXECUTION_PLAN.md](PHASE0_AI_EXECUTION_PLAN.md)

## License

Code: Apache-2.0. Synthetic demo fixture: CC0-1.0.
