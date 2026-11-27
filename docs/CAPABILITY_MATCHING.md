# Capability matching: scenarios and devices

> Status: **Proposed** as of 2026-11-27. No matcher exists in v0.1.0 and no
> device is declared compatible with `ore_sorting`.

## 1. Problem

A scenario says what a task needs; a device profile says what a device can do.
The two must be comparable without either repository importing the other and
without inventing a compatibility claim.

`jcheng-scenarios` owns the requirement side. `jcheng-devices` (planned) owns the
device-declaration side. Both use a shared, versioned capability vocabulary. A
future offline matcher reads both and emits a report; it does not become a
runtime dependency.

## 2. Vocabulary

Capability names are dotted lower-case identifiers, for example:

| Namespace | Examples | Owner of meaning |
|---|---|---|
| `manipulation.arm.*` | `reach_m`, `payload_kg`, `dof` | `jcheng-devices` (planned) |
| `manipulation.gripper.*` | `aperture_m`, `force_n` | `jcheng-devices` (planned) |
| `sensing.camera.*` | `resolution_px`, `mount` | `jcheng-devices` (planned) |
| `perception.*` | `instance_segmentation`, `scene_state`, `reachability` | `jcheng-perception` / `jcheng-devices` |
| `system.*` | `execute_motion`, `lease`, `stop_latch` | `jcheng-system` |

The vocabulary is `local_draft` in v0.1.0. It becomes `proposed` when a
`jcheng-interfaces` proposal is opened, and `contracted` only after acceptance.
A contracted vocabulary is versioned; a scenario requirement names the version
it was authored against.

## 3. Requirement form

v0.1.0 records a human-readable requirement string plus a basis:

```yaml
- id: arm_reach
  capability: manipulation.arm.reach_m
  requirement: ">= 0.45 m from the robot base to every station centre"
  basis: design_target
  rationale: Covers the pick surface and both bins in the declared cell.
  verification: Unverified
```

The validator checks shape and uniqueness, not the expression. A future matcher
needs a small, explicit grammar (for example a comparator and a unit). Until
that grammar is specified, a requirement string is documentation, not an
executable constraint.

## 4. Device profile (planned)

A device profile should declare, at minimum:

- device ID, class and profile version;
- the capability names it supports, with value, unit, tolerance and evidence;
- limits and exclusions (workspace, payload, environmental rating);
- calibration and evidence references;
- a compatibility statement: `verified`, `partially verified`, `unverified` or
  `inconclusive`, with a link to evidence;
- no scenario ID as authority and no runtime control path.

The exact schema belongs to `jcheng-devices`; this document only fixes the
matching contract.

## 5. Match outcomes

A future matcher reports one outcome per requirement:

| Outcome | Meaning |
|---|---|
| `satisfied` | Device value meets the requirement and the evidence level is declared |
| `unsatisfied` | Device value is below the requirement or explicitly excluded |
| `unknown` | Device value, unit or evidence is missing; never treated as satisfied |

A report must not collapse `unknown` into `satisfied`. A scenario is
"compatible" only when every mandatory requirement is `satisfied` at the
required evidence level. A `design_target` requirement is not evidence that the
device meets it.

## 6. Cycle prevention

- `jcheng-scenarios` never imports `jcheng-devices` and never contains a device ID.
- `jcheng-devices` never imports a scenario or treats a scenario version as a
  safety authority.
- The matcher is an offline tool in the repository that owns the matching
  policy; it reads pinned files from both sides.
- A shared vocabulary is a contract, not a code dependency. It must be proposed
  to `jcheng-interfaces` before either side treats it as stable.

## 7. Roadmap hook

| Version | Scope |
|---|---|
| v0.1.x | Abstract requirements with `local_draft` vocabulary (current) |
| v0.3.x | Shared vocabulary proposal, device-profile schema and offline matcher |
| v0.4.x | Matcher report consumed by applications or operations as an admission gate |
| v1.0.0 | Contracted vocabulary and a compatibility matrix with evidence levels |

## Related

- [Scenario model](SCENARIO_MODEL.md)
- [SCEN layer](SCEN_LAYER.md)
- [Reference requirements](../scenarios/ore_sorting/capability-requirements.yaml)
- [`jcheng-interfaces`](https://github.com/JCHENG-Robotics/jcheng-interfaces)
- [`jcheng-perception` scene representation](https://github.com/JCHENG-Robotics/jcheng-perception/blob/main/docs/SCENE_REPRESENTATION.md)
