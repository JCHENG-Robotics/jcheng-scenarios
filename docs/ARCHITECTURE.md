# Architecture

> Status: **v0.1.0** as of 2026-11-27. Offline, file-based and fail-closed.

## 1. Purpose and trust boundary

The catalog answers one question: *is this scenario declaration structurally
valid and internally consistent?* It does not answer whether the scenario is
safe, feasible, accurate or compatible with a device. Those questions belong to
`jcheng-system`, the capability repositories, `jcheng-devices` and
`jcheng-benchmark`.

```text
registry.yaml
scenarios/<id>/*.yaml
schemas/*.schema.json
        │
        ▼
strict loader ── duplicate keys rejected, YAML dates normalised to ISO 8601
        │
        ▼
JSON Schema validation ── Draft 2020-12, local $refs only
        │
        ▼
registry relationships ── unique IDs, path containment, file references,
                          version agreement, cross-profile references,
                          finite numbers, threshold consistency
        │
        ▼
text / JSON report + exit code
```

No arrow leaves the process. There is no network client, no ROS client
library, no DDS initialisation, no device path and no task executor.

## 2. Components

| Component | Module | Responsibility |
|---|---|---|
| Strict loader | `src/jcheng_scenarios/loader.py` | Read YAML/JSON, reject duplicate mapping keys, normalise implicit dates, wrap parse errors |
| Schema layer | `src/jcheng_scenarios/schema.py` | Load the eight v1 schemas, check them, validate a document with path-qualified errors |
| Report model | `src/jcheng_scenarios/model.py` | Immutable `Issue`, `ScenarioSummary`, aggregate `ValidationReport` |
| Registry checks | `src/jcheng_scenarios/registry.py` | Unique IDs, root containment, referenced files, schema versions, cross-profile references, finite numbers |
| CLI | `src/jcheng_scenarios/cli.py` | `validate`, `list`, `show`; text or deterministic JSON; exit codes 0/1 |
| Schemas | `schemas/*.schema.json` | Eight versioned, self-contained Draft 2020-12 schemas |
| Catalog | `registry.yaml`, `scenarios/` | Declarative data only |

## 3. Validation order

1. The root must be a directory and `registry.yaml` must exist.
2. The registry must satisfy the registry schema; otherwise validation stops
   because the scenario list cannot be trusted.
3. For each registry entry, in file order:
   1. the ID must be unique;
   2. the path must resolve inside the catalog root and the directory name must
      match the ID;
   3. `scenario.yaml` must parse and satisfy the profile schema;
   4. registry fields and profile fields must agree on ID, version, domain,
      delivery and verification;
   5. each of the six referenced profiles must exist, resolve inside the
      scenario directory, satisfy its schema, carry the expected schema version,
      ID suffix and version;
   6. duplicate IDs inside top-level lists and duplicate frame names are errors;
   7. cross-references between semantics, environment and task must resolve;
   8. every number must be finite;
   9. evaluation threshold status and value must agree.
4. The report is emitted; the exit code is 0 only when no issue exists.

Schema errors are reported for every document that can be read. Cross-profile
checks run only on documents that passed their schema, so an error never
cascades into misleading secondary messages.

## 4. Fail-closed rules

- A malformed document is an error, never a warning.
- A duplicate YAML key is an error; the last value never wins silently.
- An unknown field is an error (`additionalProperties: false`).
- A path that escapes the catalog root is an error.
- A non-finite number (`NaN`, `Infinity`) is an error.
- A metric marked `fixed` without a number, or `not_set` with a number, is an
  error.
- The validator never rewrites, formats or "repairs" an input document.

## 5. Determinism

Validation output depends only on file content and the fixed schema set. Issues
are sorted by document path order and JSON pointer; the JSON report has stable
keys and no timestamp. Two runs over the same tree produce the same report,
which is why the gate can archive it as evidence.

## 6. Schema versioning

- Schema files are named `<kind>.v1.schema.json` and carry a const
  `schema_version` (for example `jcheng.scenario.task.v1`).
- A v1 schema is frozen once a scenario validates against it in a release.
  Additive fields require a new schema file and a new scenario version; they do
  not mutate v1 in place.
- Breaking changes require a new major schema version and a migration note in
  `CHANGELOG.md`.
- The schemas are repository-local. If another repository consumes them, the
  format must be proposed to `jcheng-interfaces` and accepted before it is
  treated as stable.

## 7. Capability manifest

`capability.yaml` uses the canonical `capability-manifest.v1` shape so the
organization admission check can compare every repository with one schema.
Because this repository is offline, every runtime field is vacuous:

- `safety.class: offline`, empty `scopes`;
- `runtime.ros_domains: []`, empty `publishes` and `subscribes`;
- `hardware_access: none`;
- `requires_lease: true` is required by the schema and is **not** a lease
  request. The catalog never acquires, holds or forwards a lease.

`tests/test_contract.py` pins the exact key set, the interfaces range and the
contract hash. A local format deviation is not allowed; a future runtime
surface would need a reviewed manifest change, not an ad-hoc profile.

## 8. Non-goals

- Executing a scenario, planning a task or generating a trajectory.
- Simulation assets, benchmark runners, perception inference or device drivers.
- A database, service, API server or message broker.
- Storing datasets, recordings, model weights or robot assets.

## Related

- [SCEN layer](SCEN_LAYER.md)
- [Scenario model](SCENARIO_MODEL.md)
- [Capability matching](CAPABILITY_MATCHING.md)
- [Evaluation model](EVALUATION_MODEL.md)
- [Authoring guide](AUTHORING.md)
- [`jcheng-interfaces`](https://github.com/JCHENG-Robotics/jcheng-interfaces)
- [`jcheng-system`](https://github.com/JCHENG-Robotics/jcheng-system)
- [`.github` repository taxonomy](https://github.com/JCHENG-Robotics/.github/blob/main/docs/repo-taxonomy.md)
