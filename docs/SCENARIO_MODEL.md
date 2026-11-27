# Scenario model v1

> Status: **v1** as of 2026-11-27. Repository-local; not a `jcheng-interfaces`
> contract. Eight documents define one scenario: one registry entry, one
> scenario profile and six sub-profiles.

## 1. Registry and identity

`registry.yaml` is the only entry point. It uses
`schema_version: jcheng.scenario.registry.v1` and lists every admitted
scenario.

| Field | Rule |
|---|---|
| `id` | `^[a-z][a-z0-9_]*$`, at most 64 characters, unique, stable for the life of the scenario |
| `version` | SemVer `MAJOR.MINOR.PATCH`; matches every profile version |
| `path` | `scenarios/<id>`; must resolve inside the catalog root |
| `profile` | `scenario.yaml` |
| `domain` | Short domain label, for example `mining` |
| `delivery` | `Complete`, `In progress`, `Planned` or `Not started` |
| `verification` | `Verified`, `Partially verified`, `Unverified` or `Inconclusive` |
| `summary` | One short, factual description |
| `tags` | Lower-case kebab-case tags, unique |

An ID is never reused for a different scenario. A retired scenario keeps its ID
and gains a retirement note; it is not silently replaced.

## 2. Directory layout

```text
scenarios/<id>/
├── scenario.yaml                  # profile: identity, provenance, consumers
├── environment.yaml               # frames, stations, zones, lighting, constraints
├── semantics.yaml                 # classes, attributes, relations, forbidden inferences
├── task.yaml                      # goal, pre/post/failure conditions
├── capability-requirements.yaml   # abstract device/algorithm/interface needs
├── operational-constraints.yaml   # business, environment, risks, safety boundary
└── evaluation.yaml                # metrics, protocol, reporting owner
```

A scenario directory contains only these seven YAML files in v1. Assets such as
URDFs, meshes, images or recordings do not belong here; a future asset policy
must be designed separately.

## 3. Scenario profile

`scenario.yaml` (`jcheng.scenario.profile.v1`) carries:

- `title`, `domain`, `summary`, `delivery`, `verification`;
- `provenance`: author, created/updated ISO dates, `source_kind`
  (`design`, `literature`, `synthetic`, `recorded`, `hardware`) and at least one
  source record;
- `profiles`: the six relative filenames;
- `consumers`: repository, role and integration state, all starting at
  `Not started` in v0.1.0;
- `boundaries`: explicit statements about what the scenario is not.

## 4. Environment profile

`environment.yaml` (`jcheng.scenario.environment.v1`) declares the workcell.

| Section | Content |
|---|---|
| `basis` | `design_target`, `measured`, `derived` or `assumed` for the whole document |
| `frames` | Named frames with parent and note; names are unique |
| `stations` | `pick`, `drop`, `staging`, `inspection` or `operator`; pose and footprint |
| `zones` | `restricted`, `human`, `exclusion` or `approach`; frame and description |
| `lighting` | Declared light classes and a note |
| `surfaces` | Material declarations |
| `constraints` | Physical constraints with a verification state |

A pose is declarative. It is not a calibration and it never overrides a measured
TF tree.

## 5. Semantic profile

`semantics.yaml` (`jcheng.scenario.semantics.v1`) defines the vocabulary:

- `ontology`: class ID, English label, optional Chinese label, category
  (`target`, `distractor`, `receptacle`, `structure`, `human`) and description;
- `attributes`: observable fields and the classes they apply to;
- `relations`: subject/object class lists and a description;
- `forbidden_inferences`: fields the scenario refuses to assert.

`ore_sorting` forbids `true_centroid`, `true_center`, `full_extent`, `volume`,
`mass`, `material_composition`, `ore_grade` and `economic_value`. A scenario
that needs one of these must first define an evidence source and a measurement
method.

## 6. Task specification

`task.yaml` (`jcheng.scenario.task.v1`) is declarative, not an execution plan.

- `goal`: statement, target class and destination;
- `preconditions`: conditions that must hold before a run;
- `success_conditions`: conditions that define success at the final check;
- `failure_conditions`: conditions that classify the run as failed;
- `constraints`: task-level rules;
- `out_of_scope`: explicitly delegated responsibilities.

Each condition has an ID, description, optional predicate string, `measurable`
flag and verification state. A predicate is a human-readable declaration; the
validator does not execute it. Sequencing, retries, trajectories and idempotent
submission belong to `jcheng-applications` and `jcheng-system`.

## 7. Capability requirements

`capability-requirements.yaml`
(`jcheng.scenario.capability_requirements.v1`) separates:

- `device_requirements`: arm reach, payload, gripper aperture, degrees of
  freedom, camera resolution;
- `algorithm_requirements`: instance segmentation, scene state, reachability;
- `interface_requirements`: the owning repository and the required boundary,
  for example `jcheng-system` and `ExecuteMotion`.

Every requirement has a dotted capability name, a human-readable requirement
string, a `basis` and a verification state. There is no device ID and no model
name in v0.1.0; see [CAPABILITY_MATCHING.md](CAPABILITY_MATCHING.md).

## 8. Operational constraints

`operational-constraints.yaml`
(`jcheng.scenario.operational_constraints.v1`) records:

- `business`: throughput, traceability, batch definition;
- `environment`: light, dust, vibration, human access;
- `risks`: severity, description and mitigation;
- `safety_boundary`: a statement and `owner`, which is always `jcheng-system`.

The safety boundary is a pointer to the authority, not a substitute for it.

## 9. Evaluation specification

`evaluation.yaml` (`jcheng.scenario.evaluation.v1`) declares:

- `metrics`: ID, definition, unit, direction, threshold, threshold status and
  verification state;
- `test_protocol`: levels, data-source classes and reporting rules;
- `reporting`: the owner (currently `jcheng-benchmark`) and its note.

A threshold is `not_set` until a baseline and an operator-accepted requirement
exist. A `fixed` threshold must be a number. See
[EVALUATION_MODEL.md](EVALUATION_MODEL.md).

## 10. Schema mapping

| Document | Schema | Const `schema_version` |
|---|---|---|
| Registry | `schemas/scenario-registry.v1.schema.json` | `jcheng.scenario.registry.v1` |
| Scenario profile | `schemas/scenario-profile.v1.schema.json` | `jcheng.scenario.profile.v1` |
| Environment | `schemas/environment-profile.v1.schema.json` | `jcheng.scenario.environment.v1` |
| Semantics | `schemas/semantic-profile.v1.schema.json` | `jcheng.scenario.semantics.v1` |
| Task | `schemas/task-specification.v1.schema.json` | `jcheng.scenario.task.v1` |
| Capability | `schemas/capability-requirements.v1.schema.json` | `jcheng.scenario.capability_requirements.v1` |
| Operational | `schemas/operational-constraints.v1.schema.json` | `jcheng.scenario.operational_constraints.v1` |
| Evaluation | `schemas/evaluation-specification.v1.schema.json` | `jcheng.scenario.evaluation.v1` |

Every schema is self-contained: `$ref` values point only to `#/$defs/...` in the
same file. The loader resolves file references explicitly, so a schema cannot
silently fetch a remote document.

## 11. Versioning and change policy

- A schema version is frozen once a release ships it. Additive fields require a
  new schema version and a scenario version bump.
- A breaking schema change requires a new major version and a migration note.
- A scenario version bump is required when a field changes meaning, a condition
  changes, a metric changes or a capability requirement changes.
- A typo-only edit may keep the version but must update `provenance.updated`.
- Consumers pin a scenario version; a floating read is not evidence.

## Related

- [Registry and authoring](AUTHORING.md)
- [SCEN layer](SCEN_LAYER.md)
- [Capability matching](CAPABILITY_MATCHING.md)
- [Evaluation model](EVALUATION_MODEL.md)
- [Reference scenario](../scenarios/ore_sorting/scenario.yaml)
- [`jcheng-interfaces` schema process](https://github.com/JCHENG-Robotics/jcheng-interfaces)
