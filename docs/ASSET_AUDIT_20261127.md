# Ore scenario asset audit — 2026-11-27

> Status: **Complete** as of 2026-11-27. Read-only audit of the existing ore
> scenario material in the JCHENG Robotics workspace. **No file was moved**, no
> file was copied into this repository and no file in `jcheng-perception` was
> edited.

## 1. Scope and method

The audit answers three questions:

1. What ore-related scenario material already exists?
2. Which repository should own each kind of material after the SCEN layer is
   introduced?
3. What must happen before any file is moved?

Method: read-only inventory (`find`, `wc`, `grep`) of the workspace on
2026-11-27, followed by reading the design documents and package layout. No
dataset was opened or re-run. No evidence was regenerated.

## 2. Inventory

### 2.1 Design and protocol documents

All under `jcheng-perception/docs/`; 14 `ORE_SCENE_*` documents plus
`SCENE_REPRESENTATION.md`, about 3,585 lines in total.

| Asset | Content | Current role |
|---|---|---|
| `ORE_SCENE_RESEARCH.md` | S0 public-data, paper and licence research | Perception research record |
| `ORE_SCENE_UNDERSTANDING.md` | S0 architecture, module boundaries and non-goals | Perception design baseline |
| `ORE_SCENE_ROADMAP.md` | S0–S8 stages, states and evidence links | Perception ore roadmap |
| `SCENE_REPRESENTATION.md` | Scene State v1 fields and v2 draft | Perception output design |
| `ORE_SCENE_EVALUATION.md` | S1–S8 experiment design and evaluation rules | Perception evaluation protocol |
| `ORE_SCENE_S1.md`, `S1_5`, `S2`, `S3`, `S4`, `S4_1`, `S4_2`, `S4_3`, `S4_4`, `S4_4B` | Stage designs and results | Perception stage record |

### 2.2 Offline package

`jcheng-perception/ros2_ws/src/jcheng_perception_scene/` — 32 files:

- 22 Python modules (pipeline, backends, synthetic generator, geometry, mask
  operations, relations, association, metrics, evaluation, CLI, visualisation);
- `package.xml`, `setup.py`, `setup.cfg` and the ament resource marker;
- 6 JSON Schemas: `jcheng.ore_dataset.v1`, `jcheng.ore_dual_view_dataset.v1`,
  `jcheng.ore_evaluation.v1`, `jcheng.scene_association.v1`,
  `jcheng.scene_state.v1`, `jcheng.scene_state.v2`.

A thin entry point lives at `jcheng-perception/scripts/ore_scene.py`.

### 2.3 Evidence

Ten directories under `jcheng-perception/evidence/`:

`ore_scene_s1_20261126`, `ore_scene_s2_20261126`, `ore_scene_s3_20261126`,
`ore_scene_s3_relations_20261126`, `ore_scene_s4_1_20261127`,
`ore_scene_s4_2_20261127`, `ore_scene_s4_3_20261127`,
`ore_scene_s4_4_20261127`, `ore_scene_s4_4b_20261127`,
`ore_scene_sam2_20261126`.

These are perception's own experiment records. They are not scenario
declarations and are not copied here.

### 2.4 Datasets and external material

| Path | Size | Location |
|---|---|---|
| `perception_datasets/ore_public` | ~781 MB | Workspace, outside every git repository |
| `perception_datasets/ore_s1_20261126` | ~710 MB | Workspace, outside every git repository |

Both stay outside version control. Their licences and provenance are recorded
in `ORE_SCENE_RESEARCH.md` and `ORE_SCENE_EVALUATION.md`; this audit does not
grant redistribution rights.

### 2.5 Status claims found

`ORE_SCENE_ROADMAP.md` records S0 and S1 as Complete, S1.5/S2/S3/S4 as In
progress, and S5–S8 as Planned or Not started. S1 verification is
**Partially verified**: synthetic closed loop verified, a public-data baseline
measured, and real-ore acceptance **Unverified**. The audit does not upgrade any
of these states.

## 3. Ownership proposal

| Material | Current owner | Proposed owner | v0.1.0 action |
|---|---|---|---|
| Scenario identity, environment, semantic vocabulary, task goal and conditions, capability requirements, operational constraints, evaluation declarations | Embedded in perception design documents | `jcheng-scenarios` | Author new declarations here; reference the perception documents as sources |
| Segmentation pipeline, backends, synthetic generator, geometry, mask operations, relations, association, metrics implementation | `jcheng-perception` | `jcheng-perception` | Keep; do not copy |
| Scene State v1/v2 schema and association schema | `jcheng-perception` | `jcheng-perception` | Keep; a cross-repository contract needs a `jcheng-interfaces` proposal first |
| Ore evaluation protocol and stage results | `jcheng-perception` | `jcheng-perception` (protocol detail); `jcheng-scenarios` (declared metrics) | Keep; scenario declares only metric definitions and threshold status |
| Evidence directories | `jcheng-perception` | `jcheng-perception` | Keep; link only |
| Datasets and public-data caches | `jcheng-perception` / workspace | Outside git | Keep; never copy |
| `ORE_SCENE_ROADMAP.md` S7 integration plan | `jcheng-perception` | `jcheng-perception` roadmap; `jcheng-scenarios` roadmap for SCEN milestones | Keep; cross-reference, no duplicate roadmap |
| `scripts/ore_scene.py` entry point | `jcheng-perception` | `jcheng-perception` | Keep |

The boundary in one sentence: **scenarios own the scenario knowledge,
perception owns the perception implementation and its evidence, benchmark owns
evaluation execution, and the system layer owns motion and safety.**

## 4. Known design conflict

`ORE_SCENE_UNDERSTANDING.md` §1.2 lists "不新建独立仓库" (do not create a new
repository) as an S0 non-goal. The statement was written for the
perception-local ore-scene module on 2026-11-26, before the SCEN layer existed.
It is not a prohibition on a separate catalog: this repository does not absorb
`jcheng_perception_scene`, does not move its code and does not own its evidence.

Recommended follow-up (not done in this milestone): the perception owner adds a
short pointer to the SCEN layer in `ORE_SCENE_UNDERSTANDING.md` so the old
non-goal is read in context. Editing that document is a perception-repository
change and needs its own branch and review.

## 5. Migration recommendations

| Version | Recommendation | Gate |
|---|---|---|
| v0.1.x (now) | No move, no copy. New scenario declarations reference the perception documents by path. | This audit, repository gate |
| v0.2.x | Reconcile terminology (ore/gangue, visible geometry, forbidden fields). If a task-level section is moved, leave a pointer stub in the perception document. | Vocabulary review; no broken links |
| v0.3.x | Propose the shared capability vocabulary with `jcheng-devices`; do not move algorithm schemas. | `jcheng-interfaces` proposal accepted |
| v0.4.x | Controlled integration: applications reads the task specification, simulation reads the environment profile, benchmark reads the evaluation specification. | Consumer pin, contract or documented adapter |
| v0.5.x | Cross-device reuse and supervised hardware evidence; evidence remains with the producer. | Per-session operator authorization |

A file move is allowed only when all of the following hold:

- [ ] The destination owner accepts the responsibility in writing.
- [ ] The source document is replaced by a pointer, not deleted silently.
- [ ] Relative links in both repositories resolve.
- [ ] Provenance and evidence references survive the move.
- [ ] No dataset, model weight or recording enters git.
- [ ] A changelog entry and a review exist on both sides.

## 6. Risks

| Risk | Consequence | Mitigation |
|---|---|---|
| Two definitions of the ore task diverge | Applications and benchmark disagree | Scenarios is the single owner of task/evaluation declarations; perception documents are referenced, not copied |
| Broken links after a future move | Reviewers cannot trace evidence | Pointer stubs and link checks in both repositories |
| Metric definitions drift | Results are not comparable | Scenario version pins the metric definition; benchmark records the version |
| The old "no new repository" non-goal is read as current policy | Ownership confusion | Explicit conflict note and a follow-up pointer in perception |
| Scene State is treated as a contract prematurely | Cross-repository breakage | Keep it perception-local until an interfaces proposal is accepted |
| Synthetic results are read as hardware evidence | False acceptance | Data-source labels, no-result rule in scenario files, acceptance report states L5 Not applicable |

## 7. Conclusion

The ecosystem already has substantial ore-scene knowledge, but it is
perception-owned research and implementation, not a scenario registry. The new
SCEN repository should **declare** the scenario and **reference** the existing
material. No file was moved in this milestone, and none should move until the
version gates in §5 are met.

## Related

- [SCEN layer](SCEN_LAYER.md)
- [Scenario model](SCENARIO_MODEL.md)
- [Evaluation model](EVALUATION_MODEL.md)
- [Reference scenario](../scenarios/ore_sorting/scenario.yaml)
- [`jcheng-perception` ore roadmap](https://github.com/JCHENG-Robotics/jcheng-perception/blob/main/docs/ORE_SCENE_ROADMAP.md)
- [`jcheng-perception` scene representation](https://github.com/JCHENG-Robotics/jcheng-perception/blob/main/docs/SCENE_REPRESENTATION.md)
- [`jcheng-perception` ore evaluation](https://github.com/JCHENG-Robotics/jcheng-perception/blob/main/docs/ORE_SCENE_EVALUATION.md)
