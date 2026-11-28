# Capability matching: scenarios and devices

> Status: **Proposed** as of 2026-11-27; structured requirement fields and the
> role-composed matcher were added on 2026-11-28. No device is declared
> *verified* compatible with `ore_sorting`.

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

A device requirement now carries a small, explicit grammar:

```yaml
- id: arm_reach
  capability: manipulation.arm.reach_m
  role: arm
  interface: arm.position_control
  threshold: {op: ">=", value: 0.45, unit: m}
  requirement: ">= 0.45 m from the robot base to every station centre"
  basis: design_target
  rationale: Covers the pick surface and both bins in the declared cell.
  verification: Unverified
```

- `role` selects the cell role (`arm`, `gripper`, `camera`, `base`, `sensor`,
  `teleop`); several devices can fill different roles in one cell.
- `interface` is the concrete device capability that must be declared, for
  example `arm.position_control`, `end_effector.position_control` or
  `sensor.rgb_stream`.
- `threshold` is optional. A requirement whose fact is not declared by the
  device is `unverified`, never `satisfied`. A camera resolution stated as two
  dimensions is documented prose today and carries no threshold.

Algorithm requirements use the same `id`/`capability` shape but name an
`owner`; they are deferred to that owner and are never matched against a device.
Interface requirements remain documentation for the owning repository.

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
| `deferred` | The requirement is owned by an algorithm repository, not a device |

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
| v0.3.x | Shared vocabulary proposal and offline matcher (structured fields + role composition implemented locally) |
| v0.4.x | Matcher report consumed by applications or operations as an admission gate |
| v1.0.0 | Contracted vocabulary and a compatibility matrix with evidence levels |

## Related

- [Scenario model](SCENARIO_MODEL.md)
- [SCEN layer](SCEN_LAYER.md)
- [Reference requirements](../scenarios/ore_sorting/capability-requirements.yaml)
- [`jcheng-interfaces`](https://github.com/JCHENG-Robotics/jcheng-interfaces)
- [`jcheng-perception` scene representation](https://github.com/JCHENG-Robotics/jcheng-perception/blob/main/docs/SCENE_REPRESENTATION.md)
