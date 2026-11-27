# jcheng-scenarios

**简体中文** | [English](README.md)

JCHENG Robotics 生态的声明式场景库。它把机器人应用场景——环境、语义、任务条件、
能力需求、运行约束与评测指标——记录为带版本的 YAML，并用仓库内 JSON Schema 校验。
本仓库属于 SCEN 层，位于运行时依赖图之外：没有 ROS 节点、没有 DDS 域、没有设备访问、
没有任务执行器，也没有通向运动的路径。

> 状态：**实验性**，截至 2026-11-27，v0.1.0。当前只有 `ore_sorting` 一个参考场景；
> 所有参数都是设计声明，不是测量值；没有任何场景完成设备匹配、被其他仓库加载或
> 被执行评测。
> 本文为英文主文档的中文对照；如有歧义，以英文版为准。

## 范围与边界

| 项 | 本仓库 |
|---|---|
| 层 | SCEN——位于 L0–L4 运行时依赖图之外（见 [`.github` `docs/repo-taxonomy.md`](https://github.com/JCHENG-Robotics/.github/blob/main/docs/repo-taxonomy.md)） |
| 输入 | `registry.yaml`、每个场景的 `scenario.yaml` 及其引用的 6 个子 profile、`schemas/` 下的 JSON Schema |
| 输出 | 通过校验的目录、确定性的文本/JSON 校验报告、进程退出码 |
| 硬件访问 | `none`（`capability.yaml`） |
| 拥有设备 | 无。没有 `/dev/*`、串口、CAN、GPIO 或相机设备。 |
| 运动权限 | `none`；`control_path: none` |
| 禁止 | DDS 或 ROS 2 节点、设备访问、任务执行、控制或意图发布、重复实现 applications/simulation/benchmark 的运行时行为、虚构参数或结果 |

本仓库**不是**运行时能力。没有产品仓库导入它，它不在 `ecosystem.lock.yaml` 中，
也没有通向机器人的路径。它是知识资产：输入文件，输出经过校验的声明。

## v0.1.0 定义的内容

| 组件 | 用途 |
|---|---|
| 场景注册表 | 稳定的场景 ID、版本、路径、交付与验证状态 |
| 场景 Profile | 顶层元数据、provenance、消费方列表与边界声明 |
| 环境 Profile | 坐标系、工位、区域、光照、表面与物理约束 |
| 语义 Profile | 领域类别、可观测属性、关系与禁止推断 |
| 任务规范 | 目标、前置条件、完成条件、失败条件与范围外事项 |
| 能力需求 | 抽象的设备、算法与接口需求；不构成设备声明 |
| 运行约束 | 业务、环境与风险约束，以及安全边界 |
| 评测规范 | 指标、测试层级、数据源类别与报告归属 |

完整字段模型见 [docs/SCENARIO_MODEL.md](docs/SCENARIO_MODEL.md)。层边界与消费方见
[docs/SCEN_LAYER.md](docs/SCEN_LAYER.md)。

## 仓库结构

```text
jcheng-scenarios/
├── capability.yaml            # 准入清单：SCEN 层，无硬件
├── registry.yaml              # 场景注册表（仅 ore_sorting）
├── schemas/                   # 8 份带版本的 JSON Schema
├── scenarios/
│   ├── README.md              # 目录规则与候选场景政策
│   └── ore_sorting/           # 参考场景（7 份 YAML）
├── src/jcheng_scenarios/      # 加载器、Schema 校验、注册表、CLI
├── tests/                     # 契约、Schema、注册表、CLI、边界、文档测试
├── docs/                      # 架构、分层、模型、审计、依赖
├── evidence/                  # 仅离线脚手架证据
└── scripts/check_repo_gate.sh # 仓库门禁
```

## 环境要求

- Python 3.10 或更新版本（CI 覆盖 3.10 与 3.12）。
- PyYAML 6.x 与 jsonschema 4.x；测试使用 pytest。
- 不需要 ROS 发行版、DDS 中间件、GPU 或机器人。

## 快速开始

```bash
python3 -m pip install -e '.[test]'
jcheng-scenarios validate --root .
jcheng-scenarios list --root .
jcheng-scenarios show ore_sorting --root .
python3 -m pytest -q
bash scripts/check_repo_gate.sh
```

`validate` 在遇到第一个非法文档时以非零码退出，并打印每个问题的代码、
仓库相对路径与 JSON 指针。`--json` 输出确定性报告，可用于 CI 或证据归档。

## 验证状态

| 声明 | 层级 | 状态 | 证据 |
|---|---|---|---|
| 仓库门禁、Schema 校验与链接检查 | L0 | Verified | [evidence/20261127_scaffold/gate.txt](evidence/20261127_scaffold/gate.txt) |
| 单元、注册表、CLI 与内容测试 | L1 | Verified | [evidence/20261127_scaffold/pytest.txt](evidence/20261127_scaffold/pytest.txt) |
| 被 applications、simulation 或 benchmark 加载 | L2–L4 | Not applicable | v0.1.0 没有集成 |
| 硬件执行或测量 | L5 | Not applicable | 没有设备或运动路径 |

Schema 通过不等于安全认证、设备兼容性声明或任务验收结果。限制见
[ACCEPTANCE.md](ACCEPTANCE.md)。

## 相关仓库

| 仓库 | 层 | 关系 |
|---|---|---|
| [`jcheng-interfaces`](https://github.com/JCHENG-Robotics/jcheng-interfaces) | L1 | 跨仓库契约。SCEN Schema 是本地 v1，不是契约；其他仓库消费前必须先提案。 |
| [`jcheng-system`](https://github.com/JCHENG-Robotics/jcheng-system) | L2 | 唯一运动权威。场景约束永远不能替代其租约、deadman、限位或停止锁存。 |
| [`jcheng-perception`](https://github.com/JCHENG-Robotics/jcheng-perception) | L3 | 矿石场景理解研究、Scene State Schema 与证据的来源，审计中只读引用。 |
| [`jcheng-applications`](https://github.com/JCHENG-Robotics/jcheng-applications) | L4 | 未来任务规范消费方与编排方。 |
| [`jcheng-simulation`](https://github.com/JCHENG-Robotics/jcheng-simulation) | SIM | 未来环境 Profile 消费方；本仓库不生成仿真资产。 |
| [`jcheng-benchmark`](https://github.com/JCHENG-Robotics/jcheng-benchmark) | BENCH | 未来评测规范消费方与报告归属方。 |
| `jcheng-devices`（规划中） | — | 未来设备能力 Profile，与场景能力需求做离线匹配。 |
| [`.github`](https://github.com/JCHENG-Robotics/.github) | L0 | 治理、文档标准与仓库分类。 |

## 许可证

在组织许可证评审结束前，本仓库不提供 `LICENSE` 文件；见
[LICENSE-REVIEW.md](LICENSE-REVIEW.md)。

## 相关文档

- [架构](docs/ARCHITECTURE.md)
- [SCEN 层](docs/SCEN_LAYER.md)
- [场景模型](docs/SCENARIO_MODEL.md)
- [能力匹配](docs/CAPABILITY_MATCHING.md)
- [评测模型](docs/EVALUATION_MODEL.md)
- [编写指南](docs/AUTHORING.md)
- [资产审计](docs/ASSET_AUDIT_20261127.md)
- [依赖审查](docs/DEPENDENCY_REVIEW.md)
- [路线图](ROADMAP.md)
- [验收](ACCEPTANCE.md)
- [变更记录](CHANGELOG.md)
