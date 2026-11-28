# Scenario source of truth (MIG-02)

> Status: **Implemented offline** as of 2026-11-28, v0.1.0. One reference
> scenario (`ore_sorting`) has stable identifiers, source and artifact content
> hashes, a generated consumer document and a read-only compatibility checker.
> No consumer repository has been changed and no device, ROS, DDS or hardware
> path was added.

## 1. Identity

| Field | Current value | Owner |
|---|---|---|
| `scenario_id` | `ore_sorting` | `jcheng-scenarios` |
| `scenario_version` | `0.1.0` | `jcheng-scenarios` |
| `task_id` | `ore_sorting.task@0.1.0` | `jcheng-scenarios` |
| `evaluation_id` | `ore_sorting.evaluation@0.1.0` | `jcheng-scenarios` |
| scenario content hash | `sha256:7cca43d18456f0bc33469ca7b83374160cc3fc3bb1ee3d394c1dfdf834d7a4f6` | `jcheng-scenarios` (derived) |
| requirements artifact `content_hash` | generated self-hash, printed by the command below | `jcheng-scenarios` (derived) |

`capability_requirements` uses the profile id `ore_sorting.capability_requirements`.
Task, evaluation and capability profiles carry the same semantic version as the
scenario profile; the generator rejects a mismatch instead of choosing one.

The scenario content hash is recomputed, never hand-edited:

```bash
jcheng-scenarios requirements ore_sorting --root .
```

A change to any declaration changes the hash; a regenerated copy with only a new
generation timestamp does not. The value above is a snapshot for review, not a
constant pinned in code.

### 1.1 Scenario content hash

The hash covers the seven declaration documents of the scenario directory:

1. `scenario.yaml`
2. the six profiles referenced by `scenario.yaml` (`environment`, `semantics`,
   `task`, `capability_requirements`, `operational_constraints`, `evaluation`)

Canonicalisation rules (`src/jcheng_scenarios/hashing.py`):

- documents are ordered by their scenario-relative POSIX path;
- each document is framed with its relative path, so moving content between
  files changes the digest;
- mapping keys are sorted; list order is preserved because list order is
  semantic (for example metric order and condition order);
- generation-only keys (`generated_at`, `generated_on`, `generated_timestamp`,
  `timestamp`, `exported_at`, `snapshot_at`, and similar) are removed at every
  nesting level;
- the canonical JSON is UTF-8 encoded and hashed with SHA-256; the result is
  prefixed with `sha256:`.

The hash is an identity aid, not a signature, not a safety certificate and not
a deployment approval.

### 1.2 Requirements artifact self-hash

A pinned requirements file has a second hash. Its `content_hash` field is the
SHA-256 of the canonical JSON encoding of the whole requirements document with
`content_hash` removed (sorted keys, no whitespace, ASCII escaping, JSON-safe
values). This is the same convention the offline consumer harness uses for the
device snapshot and the scenario requirements artifact; it detects a stale or
hand-edited pinned copy.

The scenario content hash is preserved in
`provenance.scenario_content_hash`, so a consumer can tell which scenario
declaration set the artifact was generated from. Because that source hash is
part of the provenance, a change to any declaration changes both hashes, even
when the changed document (environment, semantics, operational constraints) is
not otherwise projected into the requirements document.

## 2. Generated requirements document

`jcheng.scenario_requirements.v1` is generated from four declaration files:

| Field | Source |
|---|---|
| `scenario_id`, `scenario_version` | `registry.yaml` + `scenario.yaml` |
| `content_hash` | artifact self-hash (section 1.2) |
| `task_id` | `task.yaml` `id` + `@` + scenario version |
| `evaluation_id` | `evaluation.yaml` `id` + `@` + scenario version |
| `capabilities` | `capability-requirements.yaml` device and algorithm requirements |
| `constraints` | `task.yaml` `constraints` (`id`, `statement`) |
| `provenance` | `source_path`, `generated_by` and `scenario_content_hash` |

Shape:

```json
{
  "schema": "jcheng.scenario_requirements.v1",
  "scenario_id": "ore_sorting",
  "scenario_version": "0.1.0",
  "content_hash": "sha256:...",
  "task_id": "ore_sorting.task@0.1.0",
  "evaluation_id": "ore_sorting.evaluation@0.1.0",
  "capabilities": [
    {"id": "manipulation.arm.reach_m", "required": true}
  ],
  "constraints": [
    {"id": "motion_via_system_only", "statement": "..."}
  ],
  "provenance": {
    "source_path": "scenarios/ore_sorting",
    "generated_by": "jcheng-scenarios.requirements 0.1.0",
    "scenario_content_hash": "sha256:..."
  }
}
```

Rules:

- `task_id` and `evaluation_id` always carry an `@MAJOR.MINOR.PATCH` suffix; the
  suffix must equal `scenario_version`.
- `capabilities[].id` is the capability identifier, not the local requirement
  slug. Every current requirement is mandatory (`required: true`).
- `parameters` is emitted only when the source requirement declares a
  machine-readable `parameters` mapping. The v0.1.0 prose requirement strings
  are **not parsed**: `docs/CAPABILITY_MATCHING.md` states that the grammar is
  not specified, so inventing numeric bounds from prose would fabricate a
  constraint. When present, a value is a scalar, a flat list, or the
  `{op, value}` comparison form.
- `constraints` entries contain exactly `id` and `statement`; the task's
  `verification` field remains in the source profile and is not copied.
- A missing document, an identifier mismatch, a version mismatch, a duplicate
  requirement/capability or a schema failure aborts generation. There is no
  partial or best-effort output.
- Output is deterministic JSON and can be consumed as a file:

```bash
jcheng-scenarios requirements ore_sorting --root . \
  --output build/ore_sorting.requirements.json
```

An applications reference harness reads that file with its own JSON/YAML reader;
it does not import this repository. `--json` prints the same document to stdout.

## 3. Consumer contracts

| Consumer | Consumes | Does not own |
|---|---|---|
| `jcheng-applications` | `task_id@version`, task constraints, capability ids, `scenario_id@version` and `content_hash` | Success thresholds, safety limits, evaluation results |
| `jcheng-simulation` | `environment.yaml`, `scenario_id@version` | Task success, evaluation results, real scenario data as measurement |
| `jcheng-benchmark` | `evaluation_id@version`, metric definitions, data-source classes | Task semantics, thresholds, scenario edits |
| `jcheng-devices` | Capability identifiers and parameters to match | Scenario acceptance, task success, safety authority |
| `jcheng-perception` | `semantics.yaml` class names and observable attributes (advisory) | Task phase, task success, motion authority |
| `jcheng-system` | Nothing from this catalog as runtime authority | Business task, evaluation, safety delegation |

A consumer must pin `scenario_id@scenario_version`, the requirements artifact
`content_hash` and the `provenance.scenario_content_hash`. Reading a floating
`main` is not admissible evidence. A recipe references `scenario_id@version` and
`task_id@version`; a benchmark suite references `evaluation_id@version`.

## 4. Compatibility check

`src/jcheng_scenarios/compatibility.py` compares one requirements document with
one device-capability document. It is read-only and offline: it does not read a
device repository, start a process, join DDS or touch a device.

```bash
jcheng-scenarios compatibility ore_sorting --root . \
  --device-capabilities device-capabilities.json --json
```

Accepted device documents:

- a list of entries, for example
  `[{"id": "manipulation.arm.reach_m", "parameters": {"reach_m": 0.50}}]`;
- a mapping keyed by capability id, for example
  `{"manipulation.arm.reach_m": {"reach_m": 0.50}}`;
- a wrapper with optional `scenario_id`, `scenario_version`, `content_hash`,
  `device_id`/`source_device`, `device_version` or a nested `scenario_ref`, plus
  `capabilities` (a list or a mapping).

A standalone device snapshot has its own artifact `content_hash`; it is not a
scenario pin. The checker compares `content_hash` only when the document also
declares `scenario_id` or `scenario_version`.

Outcomes:

| Code | Severity | Meaning |
|---|---|---|
| `UNKNOWN_CAPABILITY` | error | Device declares a capability that the scenario requirements do not contain |
| `MISSING_REQUIRED_CAPABILITY` | error | A required capability is absent, unsupported or unavailable |
| `INCOMPATIBLE_PARAMETER` | error | A declared parameter is missing or does not meet the required value/range |
| `INCOMPATIBLE_SCENARIO` | error | The device document refers to a different scenario |
| `INCOMPATIBLE_VERSION` | error | `scenario_version` differs |
| `INCOMPATIBLE_CONTENT_HASH` | error | The pinned requirements artifact `content_hash` differs (stale or changed declaration) |
| `OPTIONAL_CAPABILITY_MISSING` | warning | An optional capability is absent or unavailable |

Parameter rules: a requirement key must exist on the device. A requirement
value is a scalar or list (exact match), `{"min": ...}`/`{"max": ...}` numeric
bounds, or `{"op": ">=", "value": ...}` with one of `>=`, `<=`, `>`, `<`, `==`,
`!=`. Floats use a small tolerance; booleans do not compare equal to numbers.

A malformed requirements or device document raises an input error and exits
non-zero. A mismatched capability is reported as structured findings, not
silently downgraded.

**A compatible result is not deployment approval.** The result always reports
`"deployable": false`: the check proves only that declared capabilities satisfy
declared requirements. It does not prove measurements, safety, calibration or a
hardware session.

## 5. Safety boundary

- **System safety stays in `jcheng-system`.** Lease, deadman, limits, the stop
  latch, the arbiter and `ExecuteMotion` are system-owned. A scenario
  constraint is never a safety mechanism, and no system safety criterion may be
  migrated into this catalog.
- **System conformance cases stay system-owned.** The system S1–S17 cases are
  consistency tests, not scenario task states; they must not be renamed or
  reinterpreted as scenario acceptance evidence.
- **Perception `scene_state`/`Phase` is not a task state.** It is an advisory
  observation with validity, freshness and explicit unknowns. Task-phase
  decisions and task success stay in applications/scenarios. A perception phase
  value must not be promoted to a task state, success condition or safety
  signal.
- **No execution path.** This repository has no ROS node, DDS participant,
  device access, intent publication or motion command.
- **No measured claim.** Capability values, metrics and compatibility results
  remain declarations. Any hardware claim requires a separate, per-session
  authorization and linked evidence.

## 6. Non-goals

- No second scenario, second arm or real-ore grasp.
- No consumer repository change and no `jcheng-interfaces` contract change; the
  document is a repository-local v1 format until a second real consumer parses
  it and a proposal is accepted.
- No deletion of existing schemas, profiles or fields.
- No threshold, measurement or compatibility claim that the source data does
  not contain.

## Related

- [Capability matching](CAPABILITY_MATCHING.md)
- [Scenario model](SCENARIO_MODEL.md)
- [SCEN layer](SCEN_LAYER.md)
- [Architecture](ARCHITECTURE.md)
- [Evaluation model](EVALUATION_MODEL.md)
- [Reference capability requirements](../scenarios/ore_sorting/capability-requirements.yaml)
- [Registry](../registry.yaml)
