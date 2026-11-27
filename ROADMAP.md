# jcheng-scenarios roadmap

> Status: **v0.1.0** as of 2026-11-27. The registry, eight schemas and the
> offline validator are complete for the reference scenario; nothing is
> integrated with another repository and no scenario has been evaluated.

## Current state

| Item | State | Verification | Evidence |
|---|---|---|---|
| Repository admission, four-document set and repository gate | Complete | Verified (L0) | [evidence/20261127_scaffold/](evidence/20261127_scaffold/README.md) |
| Scenario registry with unique IDs and version agreement | Complete | Verified (L0/L1) | `registry.yaml`, `tests/test_registry.py` |
| Eight versioned JSON Schemas | Complete | Verified (L0/L1) | `schemas/`, `tests/test_schemas.py` |
| Offline validation CLI (`validate`, `list`, `show`) | Complete | Verified (L1) | `src/jcheng_scenarios/`, `tests/test_cli.py` |
| `ore_sorting` reference scenario (7 YAML documents) | In progress | Unverified | [scenarios/ore_sorting/](scenarios/ore_sorting/scenario.yaml) |
| Device capability matching | Not started | Unverified | [CAPABILITY_MATCHING.md](docs/CAPABILITY_MATCHING.md) |
| Applications / simulation / benchmark integration | Not started | Unverified | `scenario.yaml` consumer rows |
| Evaluation thresholds or results | Not started | Unverified | `evaluation.yaml` metrics are `not_set` |
| Hardware validation | Not started | Unverified | No device or motion path |

## Milestones

| Milestone | Scope | State | Exit criterion | Evidence |
|---|---|---|---|---|
| M0 | Repository admission, SCEN layer statement, four-document set, gate and CI | Complete | `bash scripts/check_repo_gate.sh` passes locally and in CI | [evidence/20261127_scaffold/](evidence/20261127_scaffold/README.md) |
| M1 (v0.1.x) | Scenario registry, scenario/environment/semantic/task/capability/operational/evaluation schemas, offline validator, `ore_sorting` reference | Complete | One registered scenario validates with zero errors; negative fixtures fail closed | `tests/`, `registry.yaml` |
| M2 (v0.2.x) | Domain semantic modeling: richer ontology, task variables, environment assets as declarations, constraint taxonomy | Planned | A second scenario field review accepts the vocabulary without adding a runtime | — |
| M3 (v0.3.x) | Capability requirements matched offline against versioned device profiles | Planned | Matching report lists satisfied, unsatisfied and unknown requirements; no device is claimed compatible without evidence | — |
| M4 (v0.4.x) | Controlled integration with Applications, Simulation and Benchmark | Planned | Each consumer reads a pinned scenario version through an accepted contract or a documented local adapter; no runtime executor appears here | — |
| M5 (v0.5.x) | Cross-device and cross-scenario task reuse; supervised real-robot experiments | Planned | Reuse is demonstrated across at least two device profiles; hardware evidence is per-session authorized and linked | — |
| v1.0.0 | Stable contracts, repeatable validation and an extensible scenario specification system | Not started | Schema and vocabulary contracts are versioned and accepted; migration policy and compatibility matrix exist | — |

## Candidate scenarios

Candidates are recorded, **not built**. An empty scenario directory is not an
admission: a candidate becomes a real scenario only when its profiles can be
authored with traceable provenance and reviewed.

| Candidate | Domain | State | Rule |
|---|---|---|---|
| `shopping_mall` | Retail / service | Not started | No directory until M2 accepts the semantic vocabulary |
| `warehouse` | Logistics | Not started | No directory until M2 accepts the task and environment model |
| `manufacturing` | Industrial assembly | Not started | No directory until M3 defines device-capability matching |

`ore_sorting` remains the only registered scenario in v0.1.0.

## Next

1. **M2 (v0.2.x) — domain semantic modeling.** Refine the ontology, task
   variables and constraint taxonomy using `ore_sorting` and the
   `jcheng-perception` scene-understanding terminology. Prerequisites: an
   accepted [asset audit](docs/ASSET_AUDIT_20261127.md), no contract change in
   `jcheng-interfaces`, and a reviewer for the vocabulary.
2. **M3 (v0.3.x) — device capability matching.** Define the versioned
   capability vocabulary shared with `jcheng-devices` and implement an offline
   match report. Prerequisites: a device-profile schema proposal and an
   accepted vocabulary version.

## Out of scope

- A standalone runtime task executor. Orchestration belongs to `jcheng-applications`.
- DDS, ROS 2 nodes, device access or control-intent publication.
- Motion commands, leases or safety enforcement. `jcheng-system` is the sole authority.
- Reimplementing simulation plants, benchmark runners or perception algorithms.
- Replacing runtime safety with scenario constraints.
- Cross-repository circular dependencies or repository imports.
- Fabricated parameters, experiment results or device compatibility.
- Cross-repository contract changes without a `jcheng-interfaces` proposal.

## Dependencies

| Dependency | Version / state | Note |
|---|---|---|
| Repository-local SCEN schemas | v1 (2026-11-27) | Not a `jcheng-interfaces` contract; no contract hash |
| `jcheng-interfaces` | Not consumed | A consumer in another repository requires a proposal first |
| `jcheng-system` API | Not consumed | Runtime authority; this repository never calls it |
| `jcheng-devices` | Planned | Capability vocabulary is `local_draft` until jointly contracted |
| Python | >= 3.10 | CI covers 3.10 and 3.12 |
| PyYAML / jsonschema / pytest | 6.x / 4.x / 7.4+ | MIT; test-only pytest |

## Related

- [README](README.md)
- [SCEN layer](docs/SCEN_LAYER.md)
- [Scenario model](docs/SCENARIO_MODEL.md)
- [Acceptance](ACCEPTANCE.md)
- [Changelog](CHANGELOG.md)
- [`.github` roadmap](https://github.com/JCHENG-Robotics/.github/blob/main/ROADMAP.md)
