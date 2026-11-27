# SCEN layer: classification, responsibility and consumers

> Status: **Proposed** as of 2026-11-27. This document defines the layer for the
> repository taxonomy; the organization-level taxonomy change is tracked in
> `.github` and the ecosystem design record.

## 1. Classification

`jcheng-scenarios` is a **SCEN** repository. SCEN is a declarative knowledge
layer outside the runtime dependency graph, alongside BENCH and RESEARCH:

| Property | SCEN |
|---|---|
| Runtime node | None |
| DDS domain | None |
| Hardware access | `none` |
| Motion authority | `none` |
| Control path | `none` |
| Input / output | YAML/JSON files in; validated declarations and reports out |
| Blocking dependency | None in the runtime graph |
| Admission owner | Organization owner plus the consumer repositories |

SCEN is not L4: it is not an operator application and it never calls the system
gateway. It is not BENCH: it declares metrics, but the benchmark repository
executes them. It is not a capability repository: it has no algorithm and no
device.

## 2. Responsibilities

| Repository | Owns | Must not own |
|---|---|---|
| `jcheng-scenarios` | Scenario identity and versions; environment, semantic, task, capability, operational and evaluation declarations; offline structural validation | Runtime execution, motion, device control, safety enforcement, simulation plants, benchmark reports, perception algorithms |
| `jcheng-devices` (planned) | Device capability, limits and compatibility profiles | Scenario task goals, runtime motion, safety authority |
| `jcheng-applications` | Parsing a task specification, deterministic planning and fail-closed intent sequencing through the system gateway | Scenario authoring, motion execution, safety policy |
| `jcheng-perception` | General perception and scene-understanding algorithms; advisory scene state | Scenario acceptance, motion authority, ore grade or economic claims |
| `jcheng-simulation` | Loading environment assets into a domain-43 plant; simulated truth | Reading real scenario data as measurements, joining domains 0/41/42 |
| `jcheng-benchmark` | Executing an evaluation specification over declared data and emitting provenance-labelled reports | Editing scenario thresholds, fabricating measurements, accepting safety |
| `jcheng-system` | Runtime safety, lease, arbiter, limits, stop latch, hardware control and the only `ExecuteMotion` | Reading scenario files as authority, delegating safety to a scenario |
| `jcheng-interfaces` | Cross-repository contracts, schemas and contract hashes | Owning repository-local v1 SCEN documents before a proposal is accepted |

A scenario is a **declaration of intent and context**, never an authority. The
system layer remains the only origin of motion.

## 3. Dependency direction

```text
                 reads (future, pinned version)
 jcheng-applications ─────────────┐
 jcheng-simulation ───────────────┼──▶ jcheng-scenarios
 jcheng-benchmark ────────────────┘         │
                                            │ capability vocabulary
                                            ▼
                                    jcheng-devices (planned)
                                            │
                                  no import either way
                                            │
 jcheng-perception ── advisory scene state ─┘  (contract review first)

 jcheng-system ◀── motion intent only ── applications/system clients
       ▲
       └── safety authority; never delegated to SCEN
```

Rules:

- SCEN does not import any repository. Consumers read files at a pinned version.
- `jcheng-devices` and `jcheng-scenarios` share a **versioned vocabulary**, not
  code. Neither imports the other; a future offline matcher reads both.
- A scene-state message shared with `jcheng-perception` is a contract change and
  must go through `jcheng-interfaces`.
- No runtime repository depends on SCEN to start, stop or move.

## 4. Consumers

| Consumer | Consumes | Integration state | Prerequisite |
|---|---|---|---|
| `jcheng-devices` (planned) | `capability-requirements.yaml` | Not started | Shared vocabulary proposal and device-profile schema |
| `jcheng-applications` | `task.yaml`, `semantics.yaml` | Not started | Task-specification contract or accepted local adapter; gateway-only execution |
| `jcheng-simulation` | `environment.yaml` | Not started | Environment-to-sim asset mapping; domain 43 only |
| `jcheng-benchmark` | `evaluation.yaml` | Not started | Metric and report mapping; no threshold edits |
| `jcheng-perception` | May consume `semantics.yaml` for class names | Not started | Scene-state contract proposal; perception remains advisory |
| `jcheng-system` | Nothing | Not applicable | Safety authority, not a scenario consumer |
| `jcheng-interfaces` | Nothing in v1 | Not applicable | Owns cross-repository contracts; SCEN schemas are local until proposed |

## 5. Cycle prevention

- No repository imports SCEN code; consumers parse files with their own reader.
- SCEN requirements use abstract capability names, never device IDs.
- Device profiles declare capabilities with the same vocabulary; they do not
  reference scenario IDs as authority.
- A future matcher is an offline tool, not a runtime dependency, and it lives in
  the repository that owns the matching policy (currently planned `jcheng-devices`).
- A cross-repository consumer must pin a scenario version. A floating `main`
  read is not admissible for acceptance evidence.

## 6. Admission and change rules

A new scenario or schema version is admitted only when:

- [ ] The responsibility does not overlap an existing repository.
- [ ] Every parameter has a provenance basis (`design_target`, `measured`,
  `derived` or `assumed`); measured values link to evidence.
- [ ] Every metric has a threshold status; `not_set` is allowed and honest.
- [ ] No forbidden inference (grade, composition, mass, value) is asserted.
- [ ] The repository gate and tests pass.
- [ ] A cross-repository consumer change has an accepted contract proposal or a
  documented local adapter.
- [ ] Any hardware claim is separately authorized per session and linked to
  evidence; no scenario file itself claims hardware validation.

## Related

- [Architecture](ARCHITECTURE.md)
- [Scenario model](SCENARIO_MODEL.md)
- [Capability matching](CAPABILITY_MATCHING.md)
- [Evaluation model](EVALUATION_MODEL.md)
- [`.github` repository taxonomy](https://github.com/JCHENG-Robotics/.github/blob/main/docs/repo-taxonomy.md)
- [`.github` documentation standard](https://github.com/JCHENG-Robotics/.github/blob/main/docs/documentation-standard.md)
- [`jcheng-system` safety](https://github.com/JCHENG-Robotics/jcheng-system/blob/main/docs/SAFETY.md)
