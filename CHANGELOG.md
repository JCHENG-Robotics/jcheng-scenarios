# Changelog

All notable changes to this project are documented here. Format based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); this project follows
[Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- MIG-02 scenario source of truth: `hashing.py` computes a canonical
  `sha256:` content hash over the scenario profile and its referenced
  declaration documents, with sorted mappings, preserved list order and
  generation timestamps excluded.
- `requirements.py` generates the `jcheng.scenario_requirements.v1` document
  (`scenario_id`, `scenario_version`, artifact `content_hash`, versioned
  `task_id`/`evaluation_id`, capabilities, task constraints and provenance).
  The artifact self-hash matches the offline consumer contract; the canonical
  scenario content hash is recorded in `provenance.scenario_content_hash`.
  Missing, duplicate or inconsistent source documents abort generation.
- `compatibility.py` provides an offline, read-only capability check with
  explicit `UNKNOWN_CAPABILITY`, `MISSING_REQUIRED_CAPABILITY`,
  `INCOMPATIBLE_PARAMETER`, `INCOMPATIBLE_VERSION`, `INCOMPATIBLE_CONTENT_HASH`
  and `INCOMPATIBLE_SCENARIO` errors, optional-capability warnings and no
  deployment claim (`deployable: false`).
- CLI subcommands `requirements` (with `--json` and `--output PATH`) and
  `compatibility` (with `--device-capabilities PATH` and `--json`).
- `docs/SOURCE_OF_TRUTH.md` records the scenario/task/evaluation identifiers,
  versions, hash, consumer contracts and the system/perception safety boundary.
- Tests for hash stability and semantic scope, requirements fields and
  inconsistency rejection, compatibility pass/unknown/missing/parameter/version
  outcomes and malformed-input rejection.
- `SCHEMA_OWNERSHIP.md`: every repository-local Schema now declares its owner,
  version, status (`repo-local`), consumers and promotion trigger. The contract
  test fails when a Schema file is not declared.
- CI now runs on the organization merge queue (`merge_group`) and pins
  `actions/setup-python` to a full commit SHA.

### Changed

- README, README.zh-CN and the repository gate describe and exercise the
  requirements/compatibility commands and link the source-of-truth document.
- `capability.yaml` now uses the canonical `capability-manifest.v1` shape
  (`schema_version`, `contract`, `safety`, `hardware_access`, `runtime`) instead
  of a custom offline profile. Because the repository is offline, `class` is
  `offline`, `scopes` and `runtime` are empty, and `requires_lease: true` is a
  schema-required vacuous value, not a lease request. The contract test pins the
  exact shape, interfaces range and contract hash.
- README, README.zh-CN and `docs/ARCHITECTURE.md` describe the canonical manifest
  and link the ecosystem boundary specification.

## [0.1.0] — 2026-11-27

Tag `v0.1.0`. No `jcheng-interfaces` contract is pinned; the SCEN schemas are
repository-local v1 documents.

### Added

- SCEN-layer repository admission: `capability.yaml`, four-document set,
  repository gate, CODEOWNERS and CI. The catalog is outside the runtime
  dependency graph and has no hardware, DDS or motion path.
- Scenario registry with unique IDs, version agreement and a root-containment
  check (`registry.yaml`).
- Repository-local JSON Schemas v1 for the registry, scenario profile,
  environment, semantics, task, capability requirements, operational
  constraints and evaluation specification (`schemas/`).
- Strict YAML loader that rejects duplicate mapping keys, plus an offline
  validator that checks file references, cross-profile references, duplicate
  IDs, finite numbers and threshold consistency (`src/jcheng_scenarios/`).
- `jcheng-scenarios` CLI with `validate`, `list` and `show`, including a
  deterministic `--json` report.
- `ore_sorting` reference scenario: environment, semantic vocabulary, task
  conditions, abstract capability requirements, operational risks and
  evaluation metrics. All parameters are design declarations and all
  verification fields are `Unverified`.
- Asset audit of the existing ore-scene material in `jcheng-perception`, with
  ownership and migration recommendations. No file was moved.
- Dependency, license and SCEN-layer design documents (`docs/`).
