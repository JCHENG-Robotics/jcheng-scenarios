# jcheng-scenarios

**English** | [简体中文](README.zh-CN.md)

Declarative scenario catalog for the JCHENG Robotics ecosystem. It records
what a robotic application scenario is — environment, semantics, task
conditions, capability requirements, operational constraints and evaluation
metrics — as versioned YAML validated against repository-local JSON Schemas.
It is a SCEN-layer repository outside the runtime dependency graph: it has no
ROS node, no DDS domain, no device access, no task executor and no path to
motion.

> Status: **Experimental** as of 2026-11-27, v0.1.0. One reference scenario
> (`ore_sorting`) exists; every parameter is a design declaration, not a
> measurement, and no scenario has been matched to a device, loaded by another
> repository or evaluated. English canonical; the Chinese README is a
> translation.

## Scope and boundary

| Item | This repository |
|---|---|
| Layer | SCEN — outside the L0–L4 runtime dependency graph (see [`.github` `docs/repo-taxonomy.md`](https://github.com/JCHENG-Robotics/.github/blob/main/docs/repo-taxonomy.md)) |
| Inputs | `registry.yaml`, one `scenario.yaml` per scenario, six referenced sub-profiles, the JSON Schemas under `schemas/` |
| Outputs | A validated catalog, a deterministic text/JSON validation report and a process exit code |
| Hardware access | `none` (`capability.yaml`) |
| Owned devices | None. No `/dev/*`, serial, CAN, GPIO or camera device. |
| Motion authority | `none`; no lease, no control path and no runtime surface |
| Forbidden | DDS or ROS 2 nodes, device access, task execution, control or intent publication, duplicating applications/simulation/benchmark runtime behaviour, fabricated parameters or results |

This repository is **not** a runtime capability. No product repository imports
it, it is not in `ecosystem.lock.yaml`, and it has no path to the robot. It is a
knowledge artifact: files in, validated declarations out.

## What v0.1.0 defines

| Component | Purpose |
|---|---|
| Scenario registry | Stable scenario IDs, versions, paths and delivery/verification state |
| Scenario profile | Top-level metadata, provenance, consumer list and boundary statements |
| Environment profile | Frames, stations, zones, lighting, surfaces and physical constraints |
| Semantic profile | Domain classes, observable attributes, relations and forbidden inferences |
| Task specification | Goal, preconditions, success conditions, failure conditions and out-of-scope items |
| Capability requirements | Abstract device, algorithm and interface requirements; no device claim |
| Operational constraints | Business, environmental and risk constraints plus the safety boundary |
| Evaluation specification | Metrics, test levels, data-source classes and reporting ownership |

The full field model is in [docs/SCENARIO_MODEL.md](docs/SCENARIO_MODEL.md).
The layer boundaries and consumers are in [docs/SCEN_LAYER.md](docs/SCEN_LAYER.md).

## Repository layout

```text
jcheng-scenarios/
├── capability.yaml            # canonical v1 manifest: offline class, no hardware
├── registry.yaml              # scenario registry (one entry: ore_sorting)
├── SCHEMA_OWNERSHIP.md        # schema owner, status, consumers, promotion triggers
├── schemas/                   # eight versioned JSON Schemas
├── scenarios/
│   ├── README.md              # catalog rules and candidate policy
│   └── ore_sorting/           # reference scenario (7 YAML documents)
├── src/jcheng_scenarios/      # loader, schema validation, registry, CLI
├── tests/                     # contract, schema, registry, CLI, boundary, docs
├── docs/                      # architecture, layer, model, audit, dependencies
├── evidence/                  # offline scaffold evidence only
└── scripts/check_repo_gate.sh # required repository gate
```

## Requirements

- Python 3.10 or newer (CI covers 3.10 and 3.12).
- PyYAML 6.x and jsonschema 4.x; pytest for tests.
- No ROS distribution, no DDS middleware, no GPU and no robot.

## Quick start

```bash
python3 -m pip install -e '.[test]'
jcheng-scenarios validate --root .
jcheng-scenarios list --root .
jcheng-scenarios show ore_sorting --root .
python3 -m pytest -q
bash scripts/check_repo_gate.sh
```

`validate` exits non-zero on the first invalid document and prints every issue
with a code, a repository-relative path and a JSON pointer. `--json` prints a
deterministic report for CI or an evidence archive.

## Validation status

| Claim | Level | Status | Evidence |
|---|---|---|---|
| Repository gate, schema validation and link checks | L0 | Verified | [evidence/20261127_scaffold/gate.txt](evidence/20261127_scaffold/gate.txt) |
| Unit, registry, CLI and content tests | L1 | Verified | [evidence/20261127_scaffold/pytest.txt](evidence/20261127_scaffold/pytest.txt) |
| Scenario loaded by applications, simulation or benchmark | L2–L4 | Not applicable | No integration exists in v0.1.0 |
| Hardware execution or measurement | L5 | Not applicable | No device or motion path |

A schema pass is not a safety certification, a device-compatibility statement
or a task acceptance result. Limits are listed in [ACCEPTANCE.md](ACCEPTANCE.md).

## Related repositories

| Repository | Layer | Relationship |
|---|---|---|
| [`jcheng-interfaces`](https://github.com/JCHENG-Robotics/jcheng-interfaces) | L1 | Cross-repository contracts. The SCEN schemas are local v1 and are not contracts; consuming them elsewhere requires a proposal. |
| [`jcheng-system`](https://github.com/JCHENG-Robotics/jcheng-system) | L2 | Sole motion authority. Scenario constraints never replace its lease, deadman, limits or stop latch. |
| [`jcheng-perception`](https://github.com/JCHENG-Robotics/jcheng-perception) | L3 | Source of the ore scene-understanding research, scene-state schema and evidence referenced by the audit. |
| [`jcheng-applications`](https://github.com/JCHENG-Robotics/jcheng-applications) | L4 | Future task-specification consumer and orchestrator. |
| [`jcheng-simulation`](https://github.com/JCHENG-Robotics/jcheng-simulation) | SIM | Future environment-profile consumer; no asset is generated here. |
| [`jcheng-benchmark`](https://github.com/JCHENG-Robotics/jcheng-benchmark) | BENCH | Future evaluation-specification consumer and report owner. |
| `jcheng-devices` | L3 | Future device-capability profiles matched against scenario requirements. |
| [`.github`](https://github.com/JCHENG-Robotics/.github) | L0 | Governance, documentation standard, repository taxonomy and the [boundary specification](https://github.com/JCHENG-Robotics/.github/blob/main/docs/repo-boundaries.md). |

## License

No `LICENSE` file ships until the organization license review closes; see
[LICENSE-REVIEW.md](LICENSE-REVIEW.md).

## Related

- [Architecture](docs/ARCHITECTURE.md)
- [Schema ownership](SCHEMA_OWNERSHIP.md)
- [SCEN layer](docs/SCEN_LAYER.md)
- [Scenario model](docs/SCENARIO_MODEL.md)
- [Capability matching](docs/CAPABILITY_MATCHING.md)
- [Evaluation model](docs/EVALUATION_MODEL.md)
- [Authoring guide](docs/AUTHORING.md)
- [Asset audit](docs/ASSET_AUDIT_20261127.md)
- [Dependency review](docs/DEPENDENCY_REVIEW.md)
- [Roadmap](ROADMAP.md)
- [Acceptance](ACCEPTANCE.md)
- [Changelog](CHANGELOG.md)
