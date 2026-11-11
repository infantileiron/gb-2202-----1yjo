# 澄远配送 · 履约时延拆解

把配送里程碑转为可复核的阶段时延与尾部分位报告。面向澄远配送24人城配分析组，使用模拟数据演示，不连接实际物流或个人数据。

## 业务场景

原流程由各站导出 `cy_milestones_20261109.csv`，用Excel分别计算均值后合并。三个痛点是时间时区不统一、平均值掩盖长尾、阶段归责缺少可复核口径。上游为配送事件记录；本项目替代分站手工汇总与统计复核；下游为运营组讨论交接改进措施。

本项目负责分析，不派单、不联系配送人员。六个核心实体贯穿数据库、Python模型/Schema/Service/Controller/Route、前端API/Store/页面：MilestoneDataset（观测）、RouteGroup（线路范围）、DelayStudy（研究配置）、DelayRun（异步结果）、ActionReview（行动复核）、Report（已审快照）。

## 启动

```sh
cp .env.example .env
docker compose up -d --build --wait
# 启动会幂等植入模拟数据；也可手动执行
docker compose exec -T backend python -m scripts.seed_demo
```

前端 http://localhost:18211 ，后端文档 http://localhost:19211/docs ，MySQL宿主端口17711。Nginx将 `/api/` 去前缀转发到Python，开发模式Vite也执行相同转发。健康检查端点 `/health` 验证数据库与Redis连接。

五个服务为frontend、backend、worker、db、redis，全部具有healthcheck，具名数据库卷、Redis卷及共享artifact卷。完成后 `docker compose down -v --remove-orphans` 会删除演示数据；需要保留数据时去掉 `-v`。

## 技术与目录

| 层 | 实际版本/实现 |
|---|---|
| 前端 | Vue 3.5.13、TypeScript5.7、Vite6、Vue Router4 |
| Python | Python3.12、FastAPI0.115.6、SQLAlchemy2、NumPy2.2.1 |
| 存储 | MySQL8.4 LTS（采用本机已有MySQL8版本）、Redis7.4 |
| 队列 | Redis列表+独立Python worker，运行状态与结果写回MySQL |
| 网关 | Nginx1.28，前端静态资源与SPA回落 |

- `backend/src/{models,schemas,services,controllers,routes}`：六实体职责分层。
- `backend/src/config`：环境变量与数据库；`middlewares`：审计、全局错误；`utils`：JWT、口令哈希与队列。
- `backend/scripts/seed_demo.py`：固定随机种子、自然键检测、保留用户修改的种子脚本。
- `backend/migrations/001_schema.sql`：基线建表说明；启动用SQLAlchemy元数据创建新表。
- `backend/migrations/002_supplements.sql`：补报修订的存量库升级脚本（新增 datasets.version/revisions、dataset_supplements 表、runs.dataset_version/dataset_snapshot），升级前先备份。
- `frontend/src/{api,stores,types,constants,hooks,utils,pages,router}`；`components`有共享分位表和贡献条，跨总览、结果、报告复用。
- 测试脚本、截图、运行报告在批次外层 `test-artifacts/gb-2202`，不混入本源码。

本地开发：Python安装requirements后从backend目录运行 `uvicorn src.main:app --reload`；将DATABASE_URL指向本地MySQL、REDIS_URL指向可用Redis，另起 `python -m src.worker`。前端 `npm install && npm run dev`。前端构建命令包含 `vue-tsc --noEmit`。

## 账号和权限

统一演示密码 `DelayDemo2026!`。口令为带独立salt的PBKDF2-SHA256摘要；JWT有效期8小时。

| 账号/角色 | 主要动作 | 权限 |
|---|---|---|
| admin@delay.demo / admin | 管理员复核与归档 | 所有分析写入、批准复核、生成报告、审计 |
| analyst@delay.demo / analyst | 配置与计算 | 上传观测、建线路/研究、异步运行、提交行动；不能批准或归档 |
| viewer@delay.demo / viewer | 阅读与下载 | 读取已入库数据/结果/报告和下载CSV；所有写入服务端403 |

接口未认证401，错角色403；报告必须关联已批准复核，未审状态409。用户重试同一复核的报告创建返回同一快照，避免重复档案。

环境变量：COMPOSE_PROJECT_NAME、FRONTEND_PORT、BACKEND_PORT、DB_PORT、JWT_SECRET、SEED_DEMO；DATABASE_URL及REDIS_URL由Compose内部配置。演示JWT与数据库口令用于本地模拟环境，部署时改为独立配置。`.env`不进入源码包。

共享枚举的位置：角色和运行状态在 `backend/src/constants/enums.py` 与 `frontend/src/constants/enums.ts`；里程碑顺序、阶段顺序分别在上述文件的MILESTONES/PHASES和milestones/phases；前端Role类型见types/domain.ts。

## 计算口径

### 里程碑配对与分位

输入CSV列为shipment_id、station、milestone、timestamp；里程碑顺序 accepted→collected→sorted→arrived→delivered，对应揽收交接、分拣出库、干线运输、末端交付。时间必须包含UTC偏移，先转换同一时间轴，计算相邻里程碑的分钟差。CSV行可乱序，但里程碑真实时间顺序不能倒置。

一票对应一个站点；重复里程碑、站点不一致、缺失里程碑、负时延整票隔离，报告保留票号及原因，不用零补齐。未知里程碑、无时区时间在导入时422拒绝。每批不超过10000条事件；至少8票完整数据才允许分析。

对每阶段和每票总时延分别求经验P50/P90/P95，使用线性插值（NumPy默认）。总时延严格等于每票四阶段之和；**阶段P95不能相加作为总P95**。

### 补报与修订口径

站点常补报或更正里程碑，不必另建批次：向原批次提交补报CSV即可，在原四列外增加整数 `revision` 列（修订号≥1）。原始入库事件一律视为**修订零**。合并规则：

- 同票同里程碑采用**较新修订号**；较新修订覆盖旧修订，事件数不膨胀。
- **迟到旧记录不覆盖**：补报修订号低于现行修订号时忽略，记 `ignored_stale` 及现行修订号。
- **重复投递不新增事件**：与现行事件或本批次已采纳记录完全一致的行忽略，记 `ignored_duplicate`。
- **同修订号内容冲突整批拒收**：同一（票号,里程碑,修订号）在批次内出现多份不同内容即冲突，返回409并逐条列出冲突行，原批次事件不做任何改动；拒收批次同样留痕。
- 补报可**救回缺节点票**：补齐缺失里程碑后，该票在下一次分析中成为有效样本。

每次补报生成一条 `dataset_supplements` 台账（采纳/忽略/冲突计数与逐行决策、原因、行号），数据集 `version` 随受理批次递增；观测台账页可展开核对每批的采纳、忽略与冲突原因。

**口径隔离**：运行在入队时刻钉住 `dataset_version` 并固化事件快照（`runs.dataset_snapshot`）。排队期间或之后到达的补报不改变该运行；已归档报告保存批准时的不可变快照，同样保留原口径。只有新建运行才使用更新后的数据，结果中同时记录钉住版本与当前版本，页面可核对。

### 重采样尾部贡献

设每票四阶段向量为x，指定尾分位q（0.8至0.99）。每轮对每个阶段独立、有放回抽取n个观测形成合成配送；求总时延q分位B。逐阶段将合成样本中该阶段固定为原始中位数，得到反事实描述量B_j，记录Δ_j=B−B_j。展示各轮Δ_j均值及2.5%/97.5%重采样范围，贡献份额为max(Δ_j,0)/Σmax(Δ,0)。全部无离散时份额为0。

假设为阶段独立重采样；它会移除阶段间相关性，故同时显示真实观测与合成总时延尾分位。区间是重采样波动范围，不是正式置信区间或因果效果；份额不等于实际P95的可加分解，不直接用于个人/站点归责。种子固定即可复现，允许30至1000轮。

## 一天的工作剧本

1. 09:00 分析师登录，查看四站600票完整观测与3票质量反例。
2. 09:03 打开 `cy_milestones_20261109.csv` 原始事件，核验UTC与站点。
3. 09:07 确认城北、河西、临港、城南“四站联运”范围。
4. 09:10 建立P95研究，200轮、seed42，记录口径。
5. 09:12 送入Redis队列，由独立worker计算并写入MySQL。
6. 09:17 检查阶段分位、完整票数、隔离原因与尾部贡献。
7. 09:20 提交“先复核临港交接与末端离散度”的行动说明，列出独立性局限。
8. 09:25 管理员批准复核并保存不可变报告，viewer可下载四阶段CSV；审计保留写入响应。

模拟数据600票、4站、3000条完整里程碑事件，加3票缺失/重复/负时延反例。自然键种子重复运行不新增或覆盖已改说明。

## 已知差异

- MySQL采用8.4 LTS，基线可接受的MySQL8家族；不是8.0镜像。
- 队列是Redis列表，worker在取走任务后崩溃不会自动重投；可新建运行重试，未实现生产级任务租约和取消。
- 目前只对新数据库自动创建表，没有存量数据库版本升级/回滚工具；生产扩容需要正式迁移流程。
- 列表最多返回最新200条实体；尚无服务端全文搜索和分页。事件导入为有限CSV，不接外部实时数据源。
- 双字体通过Google Fonts加载；离线时浏览器回退字体。所有观测均为模拟数据；归因只支持所述描述性分析。

MIT License。真实验收结果见批次 `test-artifacts/gb-2202/TESTING.md`。
