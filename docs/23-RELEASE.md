# 23 · 发布清单（可发布级别）

> 这份清单把「能跑」变成「能对外发布」。每次公开更新都按它过一遍；
> 版本纪律部分由 CI 守卫强制执行，其余为人工自检。

## 一、发布物清单

| 类别 | 内容 | 位置 |
|---|---|---|
| 代码 | 流水线 / 三条内容生成线 / 积木库 / QA / 执行报告 | `pipeline/` |
| 门面 | 双语 README、更新日志、贡献指南 | `README.md` `README.en.md` `CHANGELOG.md` `CONTRIBUTING.md` |
| 品牌 | 主标 / 图标 / 分享卡 / 使用规范 | `brand/` `site/og-card.svg` |
| 站点 | 单文件双语展示页 + 自检脚本 | `site/index.html` `site/check.py` |
| 对外定位 | 单一客户与单一档位 | `docs/22-COMMERCIAL.md` |
| 法务 | 许可 / 安全政策 / 行为准则 | `LICENSE` `SECURITY.md` `CODE_OF_CONDUCT.md` |
| MVP 定义 | 产品定义、活跃 / 冻结分层与验收判据 | `docs/24-MVP.md` `scripts/verify.py` |
| 升级计划 | 可选取舍的后续增强（不进发布检查） | `docs/25-ROADMAP.md` |
| 冻结档案 | 00–21 方法论 / 历史样片 / 额外画风（留仓库，不进对外承诺） | `docs/` `projects/_archive/` `styles/` |
| 样片 | 同一主链上不同输入与片长（产物不入库） | `projects/` |

## 二、版本纪律（每次 push GitHub 必做，`verify.py` 有守卫）

1. 按 SemVer 递增根目录 `VERSION`：功能/工具增强 → MINOR，修 bug/文档同步 → PATCH，
   破坏性改动（渲染契约、plan 格式不兼容）→ MAJOR；
2. `CHANGELOG.md` 顶部加 `[X.Y.Z] - 日期` 条目；
3. 提交必须包含 `VERSION` + `CHANGELOG.md`，README 双语版本行同步到 `vX.Y.Z`；
4. 打附注 tag `vX.Y.Z`；
5. `git push origin main && git push origin vX.Y.Z`。

**同步点共 4 个文件**：`VERSION` / `CHANGELOG.md` / `README.md` / `README.en.md`。
站点页脚**不写死版本号**（`site/check.py` 会检查这点），`scripts/verify.py` 的
`version-sync` 卡住 3 个引用文件，缺一处直接 fail。冻结档案不随版本同步。

## 三、静态站点自检

```bash
python scripts/verify.py             # MVP 一键验收（含站点自检）
python site/check.py                 # 单独复检：零外链 / i18n 成对 / 锚点 / meta / 页脚不写死版本
```

再用浏览器打开 `site/index.html` 目检：

- EN / 中文切换是否覆盖全部文案（无残留占位符）；
- 窄屏（375px）不溢出、导航可用；
- `prefers-reduced-motion` 下环境动效停止；
- 站点里的样片分数、定位与服务描述与 `registry.json` / `docs/22` / README 双语一致
  （站点不展示版本号）；
- `og-card.svg` 的数据行与站点一致。

站点是**单文件、零外部依赖**，`site/` 整个目录可直接作为静态站点根目录发布；
`index.html` 单独双击也能离线打开。

## 四、法务与安全

- [ ] `LICENSE` 存在，尾段第三方声明准确（上游风格数值来源）。
- [ ] `SECURITY.md` / `CODE_OF_CONDUCT.md` 有效，举报渠道指向本仓库。
- [ ] `scripts/env.ps1` / `env-creative.ps1` 全部是占位符；`git diff` 与全历史无真实 Key。
- [ ] 不提交渲染产物：`frames/`、`*.png`、`*.wav`、`*.mp4`、`qa.json`、
      `pipeline_report.json`、`_pipeline_events.jsonl`、`review.html`（`.gitignore` 已覆盖）。
- [ ] 对外材料用团队口径（`we` / `our team`），不出现个人/学生/接单表述。

## 五、功能冒烟

```bash
python scripts/verify.py        # 一条命令覆盖前四项（9 项验收，见 docs/24）
powershell -File pipeline/run_all.ps1 -Project projects/demo-hook-compound -SkipRender
```

`verify.py` 内部会跑规划硬闸、单文件 HTML 组装冒烟、`test_edge_v4.py`（7 条）、
`test_generate.py`（8 条）、`site/check.py` 以及版本四处同步；CI 复用同一条命令。
出片那条要求 `exit 0`，且 `pipeline_report.json` 的 `verdict=success`、
`pipeline_version` 等于当前 `VERSION`。失败路径也要抽查一次（QA 拦截应得到 `exit 2` +
`verdict=qa_blocked`）。

`docs/25-ROADMAP.md` 是可选升级计划，**不列入本节检查**，任何计划项都不影响发布判定。

## 六、文档一致性

- 断链扫描：所有 Markdown 的本地链接目标存在（发布前脚本化跑一遍）；
- `docs/` 编号连续、无重号；
- README 双语的目录树、能力数据、版本行一致；
- `CONTRIBUTING.md` 目录地图、`scripts/setup.ps1` 体检表包含新增目录/文件；
- 品牌写法、配色与 `brand/BRAND.md` / `pipeline/palette.json` 一致。

## 七、发布渠道

1. **GitHub Release**：用 `CHANGELOG.md` 对应段落作说明，附同名 tag；
2. **静态站点**：把 `site/` 作为根目录发布（无需构建、无需 Node 服务）；
3. **对外材料**：引用 `brand/` 资产与 `docs/22`，不引用本地绝对路径、不贴客户端截图。

## 八、回滚

- 每个 tag 都是可回滚点；`git revert` 优先于强推。
- `projects/_archive/` 保留历史样片作为回退参考，不清理。
- QA 口径可回退：`--v2` 全口径、`--legacy-edge` 仅边缘检测（`docs/19` / `docs/20`）。
- 报告层可用 `-NoReport` 关闭，不影响主链路。
