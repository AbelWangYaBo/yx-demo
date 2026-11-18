# 游学/留学机构合规数据管理系统 设计文档

日期：2026-11-17 ｜ 状态：已立项，直接完整实现后统一检查
更新：2026-11-18 ｜ 第二轮：菲律宾游学业务化改造（见 §10-§16），调研依据 `research/04`

## 1. 背景与目标

基于《国务院关于出境入境管理的规定》（国务院令第841号，2026-09-15施行）及配套《从事出境入境中介服务的机构和人员备案管理办法》，为游学/留学机构实现一套数据管理系统，三个硬性目标：

1. **符合备案规范**：支撑 841 号令"机构+人员"双重备案要件（无犯罪记录声明、场所证明、人员管理/教育培训/资料保存/数据安全管理制度），以及游学侧旅行社资质、行前备案（教基一〔2016〕8号）等要求。
2. **操作留痕**：所有写操作产生不可篡改的审计日志（追加写 + 哈希链），满足网安法（2025修正）第23条日志留存≥6个月、《未成年人网络保护条例》第36条"访问未成年人个人信息须审批并记录"。
3. **学员主索引**：按学员唯一标识归集该学员在机构下的全部记录（档案/合同/缴费/服务节点/活动参加/同意书），对标"校外培训家长端"全流程归集模式。

法规依据详见 `research/01~03` 三份报告及 03 号报告末尾的"法规→系统功能映射表"。

## 2. 范围界定

- 本期：单机构自用 + 演示，单体 FastAPI + SQLite（WAL），静态前端无构建步骤。
- 不做：多租户、登录认证（演示定位，接口层预留 actor 参数）、消息推送、对外监管报送自动化（备案材料可导出）。
- 数据全部虚构（机构名、学员名均为示例数据），不含任何真实个人信息。

## 3. 技术栈与结构

- Python（uv 管理）+ FastAPI + SQLAlchemy 2.0 + Alembic + pytest
- 分层规范：`services/` 纯函数业务逻辑，`apis/` 薄路由（1-3 行），`schemas/` Pydantic 模型，`models/` ORM
- 运行数据：`data/yx.db`（gitignore）
- 端口 8120（8000/8001/8770 已占用）
- 前端：`frontend/` 静态页（Vue 3 本地 vendored，无构建），由 FastAPI StaticFiles 挂载；数据严格来自后端接口，字段缺失显示「-」

```
yx-demo/
├── research/          # 调研报告（已完成）
├── docs/design.md     # 本文档
├── alembic/           # 迁移
├── app/
│   ├── main.py        # 应用装配 + 静态挂载
│   ├── db.py
│   ├── models/        # agency, staff, student, consent, program, enrollment,
│   │                  # contract, payment, service_event, audit_log, retention
│   ├── schemas/       # 与 models 对应的 Pydantic
│   ├── services/      # 业务规则（合规校验、归集、审计、退费）
│   └── apis/          # 薄路由
├── frontend/          # index.html + app.js + style.css + vue.global.prod.js
├── scripts/seed.py    # 幂等种子数据（虚构）
├── tests/             # pytest
└── data/              # 运行数据（gitignore）
```

## 4. 数据模型（核心实体）

| 实体 | 关键字段 | 合规依据 |
|---|---|---|
| Agency 机构合规档案 | 统一社会信用代码、旅行社许可证号、出境游资质、841备案状态/凭证号/日期、场所证明、制度文件清单 | 841号令；旅行社条例 |
| Staff 备案人员 | 姓名、角色(法定代表人/管理人员/顾问)、无犯罪记录声明、人员备案状态、所属机构 | 841号令双重备案 |
| Student 学员主索引 | student_no（唯一业务标识）、姓名、出生日期（判定未成年）、监护人姓名/电话/身份证号、证件号(加密存储标记) | PIPL 第28/31条 |
| Consent 同意管理 | 学员、项目、同意类型(基础服务/敏感处理/信息出境/影像使用)、单独同意标志、签署人、状态(有效/撤回)、撤回时间 | PIPL 第29/31条 |
| Program 活动/项目备案 | 名称、类型(国内研学/出境游学/留学服务)、出发日期、备案日期(校验≥行前30日)、目的地国家/城市数、带队老师数/学员数（师生比校验）、保险单、应急预案、备案状态 | 教基一〔2016〕8号；LB/T 091-2025；2014境外研学指南 |
| Enrollment 报名关系 | 学员↔活动、健康证明、家长告知书签署状态 | 备案材料 |
| Contract 服务合同 | 合同编号(GF-2016-1002骨架)、学员、服务范围勾选、签约/归档日期、阶梯退费规则(JSON)、状态 | GF-2016-1002；会计档案79号令(30年) |
| Payment 缴费凭证 | 合同、类型(服务费/代收代缴)、金额、凭证号、收款方、代收代缴关联收费方证明 | 留学服务"假代缴"风险 |
| ServiceEvent 服务节点 | 学员、合同、节点类型(材料递交/院校申请/offer/递签/签证结果)、发生时间、经办人 | 退费争议举证 |
| AuditLog 审计日志 | actor、action、entity、entity_id、before/after(JSON)、created_at、prev_hash、hash | 网安法第23条；条例第36条 |

### 4.1 审计链设计

- 每条日志 `hash = sha256(prev_hash + actor + action + entity + entity_id + payload_json + created_at)`
- 写路径统一走 `services.audit.record_audit()`，业务 API 全部调用
- **不提供任何修改/删除审计日志的接口**（追加写）；提供 `/api/audit/verify` 校验全链完整性

### 4.2 保存年限策略（retention 常量 + 展示）

| 数据 | 期限 | 依据 |
|---|---|---|
| 网络/操作日志 | ≥6个月（建议2年） | 网安法第23条 |
| PIA 评估报告 | ≥3年 | PIPL 第56条 |
| 合同/会计凭证 | 30年 | 会计档案管理办法79号令 |
| 留学服务合同文本 | ≥5年 | GF-2016-1002 示范文本说明 |

## 5. 合规业务规则（services 实现，先测试后编码）

1. `check_program_filing(program)`：境内研学备案日期须≥出发日前30日；未备案禁止置为"已成团"。
2. `check_study_abroad_rules(program)`：出境游学须出境游资质、目的地≤2国且每国≤4城、时长小学生≤21天/中学生≤42天、带队师生比≥1:10、保险必填（出境须含全球救援）。
3. `check_minor_consent(student, program)`：未成年人参加活动须存在有效监护人同意（含敏感处理单独同意）；撤回后置灰并阻止新报名。
4. `calc_refund(contract, stage)`：按 GF-2016-1002 阶梯退费表计算应退金额。
5. `collect_student_records(student_no)`：聚合该学员全部记录 + 每条带审计溯源计数。
6. 证照/备案有效期预警：agency 与 staff 备案状态、证照到期日 90 天内标黄、过期标红。

## 6. API 一览（/api 前缀，全部写操作记审计）

- GET/POST/PATCH `/api/agency` `/api/staff`
- GET/POST `/api/students`，GET `/api/students/{student_no}`，GET `/api/students/{student_no}/records`（归集）
- GET/POST `/api/consents`，POST `/api/consents/{id}/revoke`
- GET/POST `/api/programs`，PATCH `/api/programs/{id}`（触发合规校验）
- POST `/api/enrollments`（触发未成年人同意校验）
- GET/POST `/api/contracts`，POST `/api/contracts/{id}/refund-quote`
- GET/POST `/api/payments`，GET/POST `/api/service-events`
- GET `/api/audit`（只读、分页），GET `/api/audit/verify`
- GET `/api/compliance/overview`（备案状态/有效期预警/合规检查汇总）
- GET `/api/meta/retention`（保存年限策略）

## 7. 前端页面（单页 6 个 Tab）

1. 合规总览：备案状态卡、有效期预警列表、合规检查结果
2. 机构档案：机构信息 + 备案人员表
3. 学员管理：列表 + 学员 360 视图（归集接口全量展示）
4. 活动备案：列表 + 新建/编辑（实时合规校验结果）
5. 合同与资金：合同列表、退费试算、缴费凭证
6. 审计留痕：日志时间线 + 链完整性校验按钮

## 8. 测试计划（TDD：先红后绿）

- test_compliance_rules：备案30日、出境2国4城/时长/师生比/保险、未成年同意
- test_audit_chain：追加写、哈希链 verify、篡改检测
- test_student_aggregation：归集完整性
- test_refund：阶梯退费各档
- test_api_smoke：核心 API 全流程
- 回归：seed 后全量接口冒烟 + audit/verify 通过

## 9. 关键决策记录

- **后端存储而非 localStorage**：审计链与学员归集是系统合规价值本体，纯前端无法满足网安法日志义务；「演示数据优先前端」偏好仅适用于轻量展示页，此处不适用。
- **不做登录**：演示定位，写操作显式传 actor（前端固定"演示管理员"），接口层已预留。
- **SQLite 而非 PG**：单机演示零依赖；模型层用标准 SQLAlchemy，后续可用 pgloader 迁 PG。
- **未成年人判定按出生日期实时计算**，不落"是否未成年"冗余字段，避免生日过期数据不一致。

---

# 第二轮：菲律宾游学业务化改造（2026-11-18）

定位：demo 主故事线切换为菲律宾游学中介，团体（Junior Camp/研学营）与个人（散客语言研修）
双形态并存；业务+合规双线并重——业务闭环每一步自然带出合规动作。调研依据 `research/04`。
学校名为公开信息，价格为演示虚构值。

## 10. 新增数据模型

| 实体 | 关键字段 | 业务锚点 |
|---|---|---|
| School 学校库 | 地区(宿务/碧瑶/克拉克/马尼拉/怡朗)、风格(斯巴达/半斯巴达/自律型/度假村型)、佣金率%、注册费USD、合作协议、资质核验 | 841号令「与境外机构合作协议」备案要件 |
| Course 课程价目 | 挂学校、课时结构(如 1对1×4+团体×3)、最小周数、房型每周价格JSON、保分条款 | 按周计费+房型差价的真实计价方式 |
| Quotation 报价单 | 编号、学员、学校、课程、周数、房型、入学日期、明细快照JSON、总额USD、状态(草稿/已发送/已确认/已作废) | 「免费测试→出方案报价→比价」获客核心环节 |
| WeeklyReport 在读周报 | 挂报名、周次(0=分班测试)、等级、周测分、出勤%、教师评语、家长反馈时间 | 「在读」阶段填实；青少年营每日群报/成人周报 |

既有实体扩展：
- Program：type 增「语言研修」；新列 school_id/course_id/weeks/room_type；
  语言研修 return_date = 入学日 + weeks×7 - 1（自动算，护照6个月校验复用）。
- Enrollment：新列 quotation_id（报价来源可追溯）。
- Payment：新列 currency(CNY/USD/PHP)；type 细分 定金/服务费/代收代缴-学费/代收代缴-注册费/代收代缴-当地费。
- StudentDocument：doc_type 扩展 签证/SSP/ACR I-Card/WEG/监护同行证明/录取通知书/保险单 等。

## 11. 业务规则（全部来自调研真实条款）

1. 语言研修项目校验：须关联学校+课程+周数+房型；weeks ≥ 课程最小周数（WEEKS_BELOW_MIN）；
   房型须在价目表内（ROOM_TYPE_INVALID）；不要求备案/师生比/应急预案；保险降为 warning。
2. 护照校验扩展：语言研修同样要求护照有效至离校日后 6 个月。
3. WEG 硬校验：报名出境项目（出境游学/语言研修）时未满 15 周岁（按出发日算），
   须已登记 WEG 或监护同行证明材料，否则 WEG_REQUIRED 拦截。
4. 菲律宾行政链进阶段推进（仅语言研修 + 学校位于菲律宾）：
   推进「在读」须已登记 SSP（SSP_REQUIRED）；课程 >59 天（weeks×7>59）还须 ACR I-Card（ACR_REQUIRED）。
5. 报价单流转：preview 实时算价（不落库）→ 草稿 → 已发送 → 已确认（一个事务生成
   语言研修 Program + Enrollment，未成年无单独同意则 ConsentRequired 拦截）→ 已作废。
6. 报价计算：学费=房型周价×周数；注册费一次性（USD，不退）；当地费预估（PHP≈4,850/周，
   到校现付不进 USD 总额）；预计佣金=学费×佣金率（内部字段）。
7. 退费双轨：通用比例引擎不变；前端预设二选一——留学中介阶梯（GF-2016-1002）/
   菲律宾学校梯度（≥4周95% → 2-4周70% → 1-2周50% → <1周20% → 在读特例40% → 开除0%）。

## 12. API 变更

- GET/POST/PATCH `/api/schools`、`/api/courses`（课程挂学校）
- GET/POST `/api/quotations`，POST `/api/quotations/preview`（实时算价），
  POST `/api/quotations/{id}/confirm`（转报名）、`/void`
- GET/POST `/api/weekly-reports`（可按 enrollment 过滤）
- `/api/enrollments` 支持语言研修直建（带 school_id/course_id/weeks/room_type/start_date，
  事务内先建 Program 再建报名）
- `/api/students/{no}/records` 聚合补全报名 stage/课程/住宿/入学日期快照 + 报价单 + 周报
- `/api/compliance/overview` 增业务统计：在读学员数/待跟进报价/确认报价预计佣金/本月入学

## 13. 前端变更

- 新 tab「学校与课程」：学校卡片 + 课程价目表（房型价格矩阵）+ 新建/编辑弹窗
- 学员详情新 tab「报价单」（级联选校→课程→周数→房型→入学日期，实时明细，确认转报名）
  与「在读周报」（分班测试/周报录入+时间线）
- 报名弹窗双模式：团体营 / 语言研修
- 报名卡片显示菲律宾行政链徽标（SSP/ACR/WEG 按需出现）
- 合同弹窗退费预设二选一；缴费弹窗币种选择
- 总览页增业务统计卡片

## 14. 种子数据（演示故事线，全虚构）

- 机构：已备案（841）+ 出境游资质；学校库 6 所（EV/SMEAG/Philinter/QQ English/PINES/CIA）
  + 各校课程价目（IELTS 保分 12 周/ESL/亲子/商务/密集/冬令营）
- 学员案例 5 个：
  1. 小雨（14岁，亲子）：QQ English Family 8 周——未成年同意+监护同行+材料准备中
  2. 小航（21岁）：EV IELTS 保分 12 周——完整闭环（报价→确认→LOA→签证→缴费USD/PHP→
     行前→入学→SSP+ACR→在读含分班/周报）
  3. 小澈（14岁）：CIA Junior Camp 团体营 3 周——团体线（备案/师生比/WEG/保险）
  4. 小澄（28岁）：SMEAG ESL 4 周开课前 2 周取消——退费案例（合同+定金+试算+已终止）
  5. 小汐（23岁）：意向——免费测试 + 两份报价单比价中（PINES vs SMEAG）
- 保留 1 个境内研学营（备案展示用，无报名）

## 15. 测试计划（先红后绿）

- test_quotation：明细算价/preview/确认转报名/未成年拦截
- test_language_program：weeks<min、房型非法、免备案、护照适用
- test_philippines_chain：SSP/ACR 拦截与放行（12 周触发 ACR、8 周不触发）
- test_weg：<15 岁拦截（WEG/监护同行证明放行）、≥15 不要求
- test_weekly_report：录入 + 学员360聚合
- 回归：既有 30 例 + seed 后全量冒烟

## 16. 关键取舍记录

- SSP/ACR 校验仅对「语言研修 + 菲律宾学校」：团体营多目的地（新加坡等）SSP 非普适，不做全局拦截。
- WEG 放行材料含「监护同行证明」：亲子课程家长同行的真实场景。
- 佣金为内部字段：对学员零服务费模式，佣金是中介-学校间结算，不进学员侧金额展示的主口径。
- 聚合接口补全报名快照字段：修复现有 enrollments 缺 stage/课程/住宿/入学日期的前端展示缺口。
