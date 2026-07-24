# Apex SSA 开源产品与开发计划

> 状态：**产品方向与 Build in Public 方案已接受；批准执行 Phase 0，不批准提前进入 Phase 1**  
> 版本：1.0  
> 日期：2026-07-23  
> 替代范围：本文件替代 `APEX_MVP_DEVELOPMENT_PLAN.md` 中关于后续产品方向、开源发布和 Agent 的设想；原有任务规划能力继续保留。
> Phase 0 逐任务执行规范：`PHASE0_AI_EXECUTION_PLAN.md`

## 1. 评估结论

当前项目不应直接进入完整“空间态势感知 + 风险预测”功能开发，但可以进入受严格范围约束的 Phase 0。

问题不是行业没有需求。空间拥挤、碰撞预警、风险解释、协调和机动决策都是真实需求。问题是原方案把“通用 SSA 平台、风险预测、任务规划、AI Agent、开源发布”一次性合并，却没有明确第一用户、独特价值、数据许可边界和 GitHub 开箱即用标准。

### 1.1 门槛评分

| 评估项 | 当前评分 | 结论 |
|---|---:|---|
| 行业需求真实性 | 8/10 | 真实，但基础碰撞预警正逐渐成为公共或成熟商业服务 |
| Market-fit 证据 | 3/10 | 没有用户访谈、工作流观察、设计伙伴或使用数据 |
| 开发计划合理性 | 5/10 | 方向正确，范围过宽，安全边界和阶段门槛不足 |
| 开源精神 | 2/10 | README 仍标记 Proprietary，根目录无 LICENSE |
| GitHub 开箱即用 | 3/10 | 首次运行要求手工配置数据库、JWT、OpenAI Key、迁移和 Seed |
| 用户中心 | 4/10 | 以功能清单为主，尚未以具体用户任务和决策流程组织 |

**Gate：CONDITIONAL GO。** 允许执行 Phase 0 的仓库可信度修复、组织/星座隔离、合成事件回放、假设性规划影响和 Build in Public 验证；在公开行为证据 Gate 通过前，不实现 Phase 1 的标准 CDM/OMM 持久化、computed Pc、真实机动候选或 Agent。

## 2. 新的产品定位

### 2.1 推荐定位

**Apex 是面向小型卫星运营方、大学/CubeSat 团队和研究人员的开源、可审计碰撞风险决策工作台。**

它不是新的全球空间监视网络，也不承诺替代政府或商业 SSA 服务。它把用户已有或公开可用的轨道、CDM 和任务计划数据，转化为可复算的风险趋势、机动候选方案及任务影响报告。

### 2.2 首要用户

首要用户：

- 管理 1 至 20 颗卫星、没有完整自研飞行动力学平台的小型运营团队。
- 需要教学、算法验证和事件回放的大学与研究团队。
- 需要一个中立参考实现来验证 CDM、Pc 和规划影响的工程师。

暂不以大型星座运营方、军用 SSA、传感器网络运营商和全目录实时筛查服务为首要用户。

### 2.3 用户要完成的工作

1. 导入自己的星座和轨道解，保留数据来源与历元。
2. 导入一个 CDM 或示例近距离交会事件。
3. 在 5 分钟内看懂风险、数据质量、趋势和缺失信息。
4. 生成若干受约束的规避候选，不自动执行。
5. 调用现有任务规划器，比较机动前后的任务损失、资源冲突和恢复时间。
6. 导出一份包含输入、算法版本、阈值、人工决定和复算哈希的决策记录。

### 2.4 差异化

- **可审计**：每个风险结论都能追溯到输入、历元、参考系、协方差、算法版本和阈值。
- **可复算**：提供确定性事件回放和黄金样例，不依赖 LLM 才能工作。
- **规划联动**：把碰撞风险决策与项目已有的星座任务规划连接起来。
- **本地优先**：可离线、自托管，无外部 API Key 也能跑完整 Demo。
- **标准与适配器优先**：支持 CCSDS CDM/ODM、OMM/TLE；数据源和模型提供商可插拔。
- **OMM 优先、TLE 兼容**：新对象 ID 和新数据管线不得受传统五位 catalog number 限制。2026 年 CelesTrak 已明确提示新编号进入六位范围，传统 TLE 固定字段不能覆盖所有新对象，因此新导入与测试以 OMM/CSV/JSON 兼容数据结构为主，TLE 只作为遗留格式。

## 3. 做什么与不做什么

### 3.1 MVP 范围

- 保留并修复现有星座/卫星任务规划。
- 增加用户、组织、星座和卫星资产边界。
- 支持 OMM/TLE 和 CCSDS CDM 的导入、校验、版本化与来源记录。
- 支持单一受保护星座对外部对象的事件回放和风险趋势。
- 计算并展示 miss distance、TCA、相对速度、Pc、协方差/数据质量和趋势。
- 生成受约束的规避候选，并比较任务规划影响。
- 提供有硬边界的 Ops Copilot，所有建议均需人工批准。
- 提供零密钥 Demo、Docker Compose、测试、文档和开源治理。

### 3.2 NOT in scope

- 自建雷达、光学传感器或完整轨道确定系统。
- 大规模全目录实时 all-on-all 筛查。
- 自动向卫星或地面站下发机动指令。
- 将 TLE 当作高精度碰撞概率的充分输入。
- 在没有可用标注数据前训练黑盒“碰撞预测”模型。
- 重新分发受 Space-Track 或其他协议限制的数据。
- 把 3D 地球、聊天框或多 Agent 数量当成产品差异化。
- 在首个 SSA 版本中继续扩展 Rigor；先保持代码与文档可用，不扩大其范围。

## 4. Agent 设计

### 4.1 设计原则

首版采用**一个有边界的 Ops Copilot + 确定性工具层**，不采用自主多 Agent 群。

LLM 负责理解意图、选择工具、组织证据和解释权衡。轨道传播、近距离交会计算、Pc、约束求解和计划对比必须由版本化的确定性代码完成。

### 4.2 工具接口

| 工具 | 输入 | 输出 | 关键限制 |
|---|---|---|---|
| `import_orbit_solution` | OMM/TLE/状态向量 | 标准化轨道解、校验报告 | 保留原始数据和来源 |
| `import_cdm` | CCSDS CDM | 交会事件、字段质量报告 | 严格 Schema，不执行文本指令 |
| `propagate_orbit` | 轨道解、时间窗、传播器版本 | 状态序列、不确定性元数据 | 输出参考系和历元 |
| `assess_conjunction` | 事件、轨道解、协方差 | TCA、miss distance、Pc、质量等级 | 无协方差时不得伪造 Pc |
| `forecast_risk_trend` | 同一事件的多次评估 | 趋势、区间、升级/缓解信号 | 首版使用透明规则与统计区间 |
| `generate_mitigation_candidates` | 事件、卫星约束、策略 | 候选机动集合 | 只生成，不下发 |
| `compare_plan_impact` | 候选机动、现有计划 | 任务损失、资源冲突、恢复时间 | 复用现有 CP-SAT 规划器 |
| `export_decision_record` | 事件、评估、候选、人工决定 | JSON/PDF/Markdown 证据包 | 包含复算哈希 |

### 4.3 Agent 工作流

```text
事件导入
   |
   v
数据质量检查 --缺字段--> 明确告诉用户缺什么、如何补齐
   |
   v
确定性风险评估
   |
   v
趋势判断 + 证据摘要
   |
   +-- 低风险 --> Watch，设置下一评估时间
   |
   +-- 需关注 --> 生成候选 --> 比较任务影响
                              |
                              v
                         人工批准门
                              |
                   +----------+----------+
                   |                     |
                 拒绝                  批准
                   |                     |
                记录原因       导出建议/交给外部执行系统
```

### 4.4 状态机

```text
DETECTED
  | data complete
  v
ASSESSED --------> WATCH --------> CLOSED
  |
  | threshold crossed
  v
ACTION_RECOMMENDED
  |
  | human only
  v
APPROVED / REJECTED
  |
  v
EXPORTED
```

Agent 无权把事件推进到 `APPROVED`，无权调用 shell、任意 SQL 或飞行指令接口。

### 4.5 每个回答必须包含的证据

- 事件 ID、数据源、数据历元和最后更新时间。
- 使用的传播器、Pc 方法、参数与版本。
- 风险等级与置信/数据质量等级，二者分开展示。
- 缺失数据和这些缺失数据会怎样改变结论。
- 调用过的工具、关键输出和复算哈希。
- “建议，不是飞行指令”的明确安全提示。

### 4.6 Provider 策略

- Agent 是可选增强，不是运行系统的前置条件。
- 定义 provider-neutral 接口，支持 OpenAI、兼容 API 和本地模型。
- 无模型或模型失败时，规则化工作流仍可完成导入、评估、候选比较和导出。
- 外部 CDM、TLE、对象名称和备注全部视为不可信数据，不能进入系统提示或改变工具权限。

### 4.7 Agent 执行架构

```text
User request
    |
    v
Intent + policy classifier
    |
    +-- informational --> read-only tools --> evidence composer
    |
    +-- analysis ------> deterministic tools --> result verifier
    |
    +-- recommendation -> candidate tools --> human approval gate
                                               |
                                               v
                                      decision record export
```

Agent 分为五层，不能混在一个 prompt 中：

1. **Policy layer**：决定当前用户、组织、星座和事件权限，以及允许调用的工具集合。
2. **Orchestration layer**：解析用户目标，构造 typed tool input；不做轨道数学。
3. **Deterministic domain layer**：传播、Pc、趋势、候选和规划求解。
4. **Verification layer**：检查单位、时间、参考系、版本、缺失字段、结果范围和哈希。
5. **Presentation layer**：用自然语言解释证据、限制和下一步。

### 4.8 Agent 与工具结果契约

每个工具返回统一 envelope：

```json
{
  "tool": "assess_conjunction",
  "tool_version": "semver",
  "status": "success|partial|failed",
  "input_refs": ["immutable-input-id"],
  "result": {},
  "warnings": [],
  "limitations": [],
  "evidence_hash": "sha256",
  "retryable": false
}
```

约束：

- Agent 只能引用 envelope 中存在的字段；不得补齐不存在的 Pc、协方差、时间或对象属性。
- `partial` 必须在回答首屏可见，不能隐藏在脚注。
- 所有 mutation 工具要求 `organization_id`、actor 和 idempotency key。
- `generate_mitigation_candidates` 的结果永远是 `proposed`；只有人类 actor 可创建 `approved` DecisionRecord。
- Agent 不保管 Space-Track 密码、卫星命令密钥或其他长期凭据。

### 4.9 Agent 的威胁模型与 Evals

Phase 3 上线前必须通过：

| 风险 | 测试 |
|---|---|
| CDM 备注包含 prompt injection | 只作为数据展示，不改变工具与系统指令 |
| 用户要求“直接执行机动” | 明确拒绝执行，只生成候选和导出 |
| 缺协方差却要求 Pc | 不伪造；请求补充数据或解释 provided Pc |
| 模型声称调用未调用的工具 | 审计轨迹校验失败，响应不发布 |
| 跨组织事件 ID | 权限层阻止，Agent 不获得数据 |
| 工具 timeout/partial | Agent 保留状态和限制，不包装成成功 |
| 模型不可用 | 确定性 UI 和 API 全部继续工作 |
| 同一输入重复执行 | 确定性工具输出一致，Agent 引用同一 evidence hash |

评估集至少包含：正常回放、缺字段、冲突单位、过期轨道解、多个连续 CDM、阈值附近事件、无可行候选、planner timeout、恶意文本和越权请求。

### 4.10 Agent 开发 Gate

只有以下条件全部满足才开始 Agent：

- Phase 1/2 的 typed API 已稳定并有黄金测试。
- 非 LLM UI 能独立完成事件导入、评估、规划对比和导出。
- 至少 5 名用户的公开行为表明“解释与工作流编排”是阻力，而不是底层数据缺失。
- 工具调用、权限、审批和审计均可在不依赖 prompt 的代码层强制执行。
- 已有 model-off、tool-error、prompt-injection 和 hallucination eval harness。

## 5. 推荐架构

```text
                          +----------------------+
OMM/TLE/CDM/Fixture ----> | Ingestion + Schema   |
                          | validation/provenance|
                          +----------+-----------+
                                     |
                                     v
 +----------------+       +----------+-----------+       +------------------+
 | Constellation  |<----->| Versioned Domain DB  |<----->| Existing Planner |
 | Management UI  |       | assets/orbits/events |       | CP-SAT + validator|
 +----------------+       +----------+-----------+       +------------------+
                                     |
                    +----------------+----------------+
                    |                                 |
                    v                                 v
           +--------+---------+              +--------+---------+
           | Deterministic SSA|              | Evidence/Audit    |
           | assess + forecast|              | replay + export   |
           +--------+---------+              +------------------+
                    |
                    v
           +--------+---------+
           | Bounded Ops      |
           | Copilot          |
           +------------------+
```

建议的领域边界：

- `catalog`：空间对象、卫星资产、星座、轨道解与来源。
- `conjunction`：CDM、交会事件、连续评估与事件生命周期。
- `risk`：确定性指标、数据质量、趋势、阈值和解释。
- `planning`：保留现有意图解析、窗口、CP-SAT 和物理校验。
- `agent`：工具注册、策略、审批门、审计轨迹和模型适配器。
- `adapters`：CelesTrak、Space-Track 用户自备凭据、文件导入和未来数据源。

关键数据模型分阶段演进：

| 阶段 | 模型 | 目的 |
|---|---|---|
| Phase 0 | `Organization`, `OrganizationMembership`, `Constellation`, `ConstellationSatellite` | 先消除全库查询并保留现有 Satellite/Planner |
| Phase 1 | `SpaceObject`, `SpaceAsset`, `OrbitSolution`, `OrbitSource` | 拆开全局对象、用户资产、轨道版本和来源 |
| Phase 1 | `ConjunctionEvent`, `ConjunctionMessage`, `RiskAssessment` | 一个事件可接收多次 CDM/评估 |
| Phase 2 | `RiskTrend`, `MitigationCandidate`, `PlanningImpact` | 趋势、候选和任务影响 |
| Phase 3 | `AgentRun`, `ToolCall`, `Approval`, `DecisionRecord` | Agent 审计、人类审批和证据导出 |

最终状态下，`Satellite` 不再同时承担目录对象、用户资产和规划资源三个概念。迁移采用 strangler 模式：先通过 constellation membership 限定旧表，再建立新表和双读校验，最后迁移 planner，不做一次性重写。

## 6. 第 0 阶段：证明值得做，并把仓库变成可信开源项目

第 0 阶段不是开发漂亮的大屏。它要消除五类致命风险：无人需要、数据不合法、结果不可复算、仓库跑不起来、原有规划不可信。

详细到文件、测试和验收命令的唯一执行规范是：

> `PHASE0_AI_EXECUTION_PLAN.md`

若本节与该文件冲突，以本文件的产品/安全边界为准，以执行规范的任务细节为准。

### 0A. Build in Public Market-fit 证据

用户无法稳定安排正式访谈，因此用“公开 artifact + 可验证用户行为”替代空泛问卷，但不降低证据标准。

证据阶梯：

| 等级 | 行为 | 是否计入 Gate |
|---|---|---|
| E0 | star、like、浏览、转发 | 否 |
| E1 | 在自己的环境完成 Quickstart | 是 |
| E2 | 提交结构化工作流或错误反馈 | 是 |
| E3 | 使用自己的公开、合成或有权分享事件 | 是 |
| E4 | 至少 7 天后再次使用 | 是 |
| E5 | 提交测试向量、adapter 或 PR | 是 |

六周公开节奏：

1. Week 0：零配置 planner、真实限制说明、baseline。
2. Week 1：合成事件回放、provided Pc 标签、证据导出。
3. Week 2：数据质量、缺失协方差、错误样例。
4. Week 3：假设性不可用窗与任务规划影响。
5. Week 4-5：只修复多个用户重复出现的阻力，不扩展大功能。
6. Week 6：公开 GO / ITERATE / PIVOT / STOP EXPANSION 证据报告。

继续 Phase 1 的门槛：

- 10 次独立 Demo 成功。
- 5 份结构化工作流反馈。
- 3 名用户使用自己的公开/合成事件。
- 2 名用户至少 7 天后重复使用。
- 至少 2 份反馈来自 mission ops、flight dynamics、CubeSat 或 SSA 背景人员。
- 至少 1 个外部 PR、测试向量或 adapter contribution。

不能用 stars、维护者代跑、自动化或 AI 生成反馈补数。

### 0B. 开源与法律基线

- 先写 `.gitignore` 和资产边界，再初始化 Git 仓库，建立 `main` 分支和 SemVer 版本策略。
- 默认采用 Apache-2.0；发布前完成依赖、字体、图片、样例数据和星历文件许可证审计。
- 删除 README 的 Proprietary 声明。
- 增加 `LICENSE`, `NOTICE`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, `GOVERNANCE.md`, `CHANGELOG.md`。
- 使用 DCO 或等价的轻量贡献者签署流程，不要求不必要的版权转让。
- 清理或证明 `backend/de421.bsp` 的来源与再分发权。
- Space-Track 仅提供“用户自备账号”的适配器，不提交凭据，不重新分发受限数据。
- 建立 SBOM、依赖扫描、Secret Scan 和 Release Provenance。
- 初始提交不得包含 `dist/`, `htmlcov/`, `__pycache__/`, `*.tsbuildinfo`, `.env` 或未确认来源的二进制。

### 0C. 现有系统可信度修复

必须先修复：

- `replan` 闭包中局部 `req` 在赋值前被读取的问题。
- `seed_satellites.py` 修改全局配置的 `cfg.pop("norad_id")`。
- Seed 将当前时间写入 `tle_epoch`，而不是解析真实 TLE 历元。
- `Satellite` 和 planner 缺少组织/星座/用户范围，当前会查询全部卫星。
- 轨道与成像代码中的宽泛 `except Exception` 和静默失败。
- README 宣称 Celery，但实际使用 FastAPI `BackgroundTasks` 的不一致。
- 后端完整测试在轨道/成像用例中卡住的问题。
- 当前 Ruff 发现的 72 个问题。
- 前端没有有效测试文件的问题。
- Planner 文档声称的 turn-rate/downlink 等约束与实际实现不一致的问题。

质量门槛：

- 后端、前端、集成测试全部有确定的超时并通过。
- Lint、类型检查、迁移检查和 Secret Scan 全绿。
- 关键轨道样例与独立参考值比较，并声明误差预算。
- 现有任务规划端到端路径可复现，不依赖在线 LLM。
- 所有时间使用 timezone-aware UTC，catalog ID 按字符串处理并覆盖六位编号。

### 0D. GitHub 开箱即用

新用户路径必须是：

```bash
git clone <repo>
cd apex
docker compose up --build
```

然后在 5 分钟内打开一个本地 URL，看到：

- 已载入的演示星座。
- 一个可回放的脱敏/合成交会事件。
- 风险与数据质量解释。
- 一个明确标为“假设性不可用时间窗”的规划影响对比；Phase 0 不把它描述为真实机动候选。
- 不需要 OpenAI Key、Space-Track 账号或手工数据库迁移。

实现要求：

- Compose 启动时完成健康检查、迁移和幂等 Demo Seed。
- 默认生成本地开发密钥；生产配置检测到默认密钥时拒绝启动。
- 提供 `make demo`, `make test`, `make lint`, `make reset-demo`。
- README 的前 60 行只保留定位、截图、3 步 Quickstart、预期输出和故障排查入口。
- 支持 macOS/Linux 的 amd64 与 arm64；Windows 至少验证 WSL2。
- GitHub Actions 在干净环境验证 Quickstart、测试、构建和许可证。
- `/health/live` 与 `/health/ready` 分开；迁移或 Seed 失败时 API 不得 ready。
- 默认 Compose 不要求本地 `.env` 存在；production 使用 Demo secret 时必须拒绝启动。

### 0E. 最小公开回放垂直切片

- 只使用仓库内 CC0 合成事件，不接收真实受限 CDM。
- 展示输入自带的 miss distance、相对速度和 `provided Pc`。
- 协方差缺失时明确说明 Apex 无法独立复算 Pc。
- 使用 canonical JSON 和 SHA-256 生成证据哈希。
- 允许把一个卫星在 TCA 周边标记为假设性不可用，调用原 planner 比较 before/after。
- 输出 `physics_verified=false`，不生成真实脉冲或燃料结论。

### 0F. Phase 0 验收

Phase 0 只有同时满足以下条件才完成：

- Build in Public 运行满六周并给出证据 Gate 结论。
- 全新机器按 README 在 5 分钟内完成 Demo。
- 不配置任何付费/私有 API 也能演示核心价值。
- 0C 的 P0/P1 缺陷修复并有回归测试。
- 所有演示数据和二进制资产都有可验证的再分发权。
- 至少 10 次独立 Demo、5 份结构化反馈、3 次自有公开/合成事件回放、2 名重复用户和 1 个外部贡献。
- 用户能独立区分风险、数据质量、provided Pc 和假设性规划影响。

预计代码准备工期：3 至 4 周；Market-fit 验证最短 6 个日历周，不能用更快编码压缩。

## 7. 后续阶段

### Phase 1：标准化数据与可审计事件回放

- 完成 `SpaceObject`, `SpaceAsset`, `OrbitSolution`, `OrbitSource` 拆分。
- OMM 为默认轨道导入，TLE 为兼容输入；实现 CCSDS CDM KVN/XML 导入。
- 每份原文不可变保存，标准化字段另存；记录 source、license/usage boundary、received_at、effective epoch、parser version 和 hash。
- 一个 ConjunctionEvent 可关联多份 ConjunctionMessage。
- 使用公开或合成黄金样例独立复算 miss distance/Pc；方法、参考系、硬体半径和协方差处理版本化。
- 无协方差或不支持的参考系时不得生成 computed Pc。
- 支持 JSON/Markdown 证据包；PDF 不是关键路径。
- 不实现 Agent。

**Phase 1 验收**：

- 至少两种 CDM 编码和 OMM 导入通过 schema/round-trip 测试。
- provided Pc 与 computed Pc 分栏显示，不覆盖原值。
- 黄金样例与独立参考实现的误差在预先声明预算内。
- 同一输入和版本产生相同 canonical output/hash。
- 跨组织隔离测试零失败。

### Phase 2：风险趋势与规划影响

- 将同一事件的连续 CDM/评估按 creation time 和 TCA 对齐。
- 趋势只使用透明规则、统计区间和版本化阈值，不训练黑盒“碰撞预测”。
- 风险与数据质量分别演化；低质量高 Pc 和高质量低 Pc 都能表达。
- 先实现策略级候选：评估时刻、禁用时间窗和 operator constraints。
- 真实轨道机动候选必须通过经过验证的 astrodynamics 模块或外部 provider adapter；不能用 LLM 生成数值脉冲。
- 复用 planner 比较任务覆盖、任务丢失、重新分配、能源、存储和恢复时间。
- 每个候选包含可行/不可行原因和未建模约束。

**Phase 2 验收**：

- 顺序颠倒、重复和缺失 CDM 不破坏事件趋势。
- 阈值附近有边界测试和敏感性说明。
- Planner before/after 使用相同基线与固定时间，结果可复算。
- 没有可行候选时系统明确返回 none，不强行推荐。

### Phase 3：有边界的 Ops Copilot

- 实现第 4 节的五层架构和统一 tool envelope。
- 只开放经过 Schema 验证的 typed tools；模型无 shell、SQL、网络凭据或飞行接口。
- 支持提问、解释、生成候选、比较和导出。
- 每个建议含工具版本、输入引用、限制和 evidence hash。
- 人工审批由数据库权限和状态机强制，prompt 不可绕过。
- 增加 Prompt Injection、错误工具调用、模型不可用、幻觉字段、越权和 timeout Evals。
- 规则化 UI/API 是降级路径；Agent 停机不影响确定性能力。

**Phase 3 验收**：

- Agent 自主创建 approved 决定或执行机动次数为 0。
- Evals 覆盖正常、缺数据、恶意输入、越权和工具故障。
- 回答中每个关键数值能映射到 tool result 字段。
- provider 切换不改变领域工具的输入/输出契约。

### Phase 4：公开 Beta 与社区

- 发布 GitHub Release、容器镜像、架构文档和 Roadmap。
- Good First Issues、插件示例、贡献者指南和公开决策记录。
- 对 Phase 0 的 TTHW、独立用户和重复使用指标做回测。
- 只在真实自托管部署需求出现后增加 Helm/Terraform，不为简历式基础设施扩张范围。
- 发布支持矩阵、数据保留政策、升级/回滚指南和安全响应目标。
- 对外部 adapters 建兼容性测试套件，不把 provider-specific 逻辑放入核心领域层。

## 8. 成功指标

用户价值指标：

- 新用户首次成功回放事件时间少于 5 分钟。
- 外部用户能在没有开发者陪同下解释风险、数据质量和规划影响。
- 同一事件使用同一版本输入时输出可复算。
- 从事件导入到生成决策记录少于 10 分钟，不含外部数据等待。

安全与质量指标：

- Agent 自主批准或执行机动次数始终为 0。
- 所有风险结论具备输入来源、版本、方法和复算哈希。
- 受保护资产跨组织泄露测试为 0 失败。
- 发布门槛无已知 P0/P1 缺陷，无未解释的高危依赖。

开源与 DX 指标：

- 干净环境 Quickstart 成功率至少 90%。
- Issue 首次响应目标 3 个工作日。
- 至少 10 次独立 Demo、2 名重复用户、1 个外部贡献被合并，再宣称通过 Phase 0 Market-fit Gate。

## 9. 决策记录

### 已接受的工作默认值

1. 目标用户先聚焦小型运营方、大学/CubeSat 和研究团队。
2. 产品切口是可审计 CA 决策工作台，不是通用 SSA 大屏。
3. 保留星座任务规划，并把它作为“风险对任务影响”的差异化能力。
4. 首版风险预测是透明的事件趋势和不确定性，不训练黑盒 ML。
5. 首版是单一 Ops Copilot，不做自主多 Agent。
6. 默认 Apache-2.0、本地优先、provider-neutral、无 API Key Demo。
7. 无法依赖正式访谈时，使用六周 artifact-driven Build in Public 获取行为证据。
8. 第 0 阶段先完成开源基线、技术修复、组织/星座隔离、Quickstart 和合成事件垂直切片。
9. Phase 0 的 Pc 只展示为 `provided`，computed Pc 从 Phase 1 开始。
10. OMM 为新数据管线默认格式，TLE 仅兼容遗留对象。

### 未决问题

这些问题不阻止本地 Phase 0 开发，但在首次公开仓库前需要仓库所有者完成：

1. GitHub 用户/组织、仓库名称、可见性和域名。
2. 是否公开现有历史文档与 `outputs/`；默认不提交生成输出。
3. `backend/de421.bsp` 的来源证明；无法证明时从发布包排除。
4. 首次公开 Release 的 maintainer 联系方式和安全报告渠道。

## 10. 参考标准与市场事实

- [CCSDS Conjunction Data Message, 508.0-B-1](https://ccsds.org/publications/allpubs/entry/3064/)
- [CCSDS Orbit Data Messages, 502.0-B-3](https://public.ccsds.org/Pubs/502x0b3e1.pdf)
- [NASA CARA publicly available software and risk-assessment guidance](https://www.nasa.gov/cara/)
- [NOAA Office of Space Commerce TraCSS](https://space.commerce.gov/tracss/)
- [ESA Space Environment Report](https://www.esa.int/Space_Safety/Space_Debris/ESA_s_Space_Environment_Report_2025)
- [CelesTrak GP data formats](https://celestrak.org/NORAD/documentation/gp-data-formats.php)
- [CelesTrak usage policy](https://www.celestrak.org/usage-policy.php)
- [Space-Track](https://www.space-track.org/)
- [GitHub community profile](https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/about-community-profiles-for-public-repositories)
- [GitHub Discussions](https://docs.github.com/en/discussions/collaborating-with-your-community-using-discussions/about-discussions)
- [GitHub artifact attestations](https://docs.github.com/en/actions/concepts/security/artifact-attestations)
- [Open Source Guides: Building Welcoming Communities](https://opensource.guide/building-community/)
- [Libre Space Community](https://community.libre.space/)

本计划中的行业判断是产品决策输入，不代表当前项目已达到飞行认证或可用于自主碰撞规避。

## GSTACK REVIEW REPORT

| Review | Trigger | Why | Runs | Status | Findings |
|---|---|---|---:|---|---|
| Premise / CEO | `office-hours` + plan review | 产品方向与 market-fit | 2 | PHASE 0 CLEARED | 用行为证据替代不可控访谈 |
| Engineering | `plan-eng-review` + 本地代码审计 | 架构、故障、测试、依赖 | 2 | PHASE 0 SPECIFIED | 已形成逐任务执行规范 |
| Design | 决策旅程审查 | 风险、质量、规划影响信息顺序 | 1 | PHASE 0 SPECIFIED | 不以 3D/聊天框为首屏 |
| DX | Quickstart 和 GitHub 审计 | TTHW、License、无密钥 Demo | 2 | PHASE 0 SPECIFIED | 实现尚待执行 |

**VERDICT：CLEARED FOR PHASE 0 ONLY。Phase 1、computed Pc、真实机动候选和 Agent 仍未获准；必须等待六周 Build in Public Gate。**
