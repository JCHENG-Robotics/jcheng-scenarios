# Evaluation model

> Status: **v1** as of 2026-11-27. Metrics are declared; no threshold is set
> and no result exists.

## 1. Separation of responsibilities

| Repository | Responsibility |
|---|---|
| `jcheng-scenarios` | Declare metrics, definitions, units, directions, threshold status and the test protocol |
| `jcheng-benchmark` | Execute the declared evaluation over a recorded or synthetic dataset and emit a provenance-labelled report |
| `jcheng-perception` | Produce advisory scene observations and, when applicable, instance-level ground truth for its own offline evaluation |
| `jcheng-system` | Provide runtime telemetry and the authoritative stop/latch state; never accepts a metric as safety evidence |

A scenario file never contains a result. A benchmark report never edits a
scenario threshold.

## 2. Levels

| Level | Name | Environment | Hardware |
|---|---|---|---|
| L0 | Contract / static | CI runner | No |
| L1 | Unit | CI runner | No |
| L2 | Mock integration | In-process / mock bus | No |
| L3 | Mock end-to-end | Mock gateway / topics | No |
| L4 | Replay | Recorded data | No |
| L5 | Hardware | Robot | Yes |

`ore_sorting` declares all six levels because a future evaluation may use them.
v0.1.0 executes only L0/L1 structural checks; the other levels are not claimed.

## 3. Data-source classes

| Class | Meaning | Reporting rule |
|---|---|---|
| `synthetic` | Generated with procedural ground truth | Label synthetic; never hardware |
| `public` | Third-party public dataset with a licence | Record dataset, version, licence and DOI |
| `recorded` | Captured from the robot, replayed offline | Record session, hashes and calibration |
| `mock` | Mock gateway or mock plant | Label mock; never hardware |
| `simulation` | Domain-43 plant | Label simulated; never hardware |
| `hardware` | Supervised run on the robot | Requires per-session authorization and a linked evidence path |

Classes are reported separately and never aggregated into one "accuracy"
number. A public or synthetic result does not become a hardware result by being
rerun.

## 4. Metrics

Each metric declares:

- `id`: stable identifier;
- `definition`: one precise sentence, including what counts as failure;
- `unit`: `ratio`, `percent`, `s`, `m` or `count`;
- `direction`: `higher_is_better`, `lower_is_better` or `target`;
- `threshold`: a number or `null`;
- `threshold_status`: `not_set`, `proposed` or `fixed`;
- `verification`: standard verification vocabulary.

`ore_sorting` declares pick success rate, misclassification rate, cycle time,
placement error and scene-freshness violations. All are `not_set` and
`Unverified`.

## 5. Threshold policy

1. The metric definition is written before data collection.
2. A baseline is measured on a declared data source.
3. The task owner proposes a threshold and records the rationale.
4. A `fixed` threshold requires a number and a new evaluation version.
5. A failed bound stays failed. A rerun creates a new report; it never
   overwrites or reinterprets the old one.
6. A threshold change is a scenario change: bump the version, update the
   changelog and link the new evidence.

`not_set` is the honest default. An unset threshold is not "zero" and is not a
pass.

## 6. Failure accounting

- A missing prediction, a dropped instance, a stale scene or a stopped run is a
  failure, not a skipped row.
- A malformed dataset row aborts the evaluation; it is never silently dropped.
- A run with human intervention is reported as intervened and is not counted as
  an autonomous success.
- A covered or invisible instance is an explicit unknown, not a success.

## 7. Reporting

A future `jcheng-benchmark` report must record:

- scenario ID and version;
- evaluation schema version;
- dataset identifier and SHA-256;
- data-source class;
- operator, host and ISO 8601 date;
- metric values, thresholds and result per metric;
- explicit limitations and unverified items.

No report is produced by this repository. The `--json` output of
`jcheng-scenarios validate` is a catalog validation report, not an evaluation
or acceptance report.

## Related

- [Scenario model](SCENARIO_MODEL.md)
- [Capability matching](CAPABILITY_MATCHING.md)
- [Reference evaluation](../scenarios/ore_sorting/evaluation.yaml)
- [`jcheng-benchmark` protocol](https://github.com/JCHENG-Robotics/jcheng-benchmark/blob/main/docs/BENCHMARK_PROTOCOL.md)
- [`jcheng-perception` ore evaluation](https://github.com/JCHENG-Robotics/jcheng-perception/blob/main/docs/ORE_SCENE_EVALUATION.md)
- [`.github` documentation standard](https://github.com/JCHENG-Robotics/.github/blob/main/docs/documentation-standard.md)
