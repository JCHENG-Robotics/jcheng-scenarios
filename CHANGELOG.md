# Changelog

All notable changes to this project are documented here. Format based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); this project follows
[Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- Nothing yet.

### Changed

- Nothing yet.

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
