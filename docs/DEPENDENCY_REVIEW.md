# Dependency and prior-art review

> Status: **Proposed** as of 2026-11-27. No third-party code is copied into this
> repository. Versions and licences are recorded as observed; a dependency is
> not adopted until it is pinned, tested and reviewed.

## 1. Method

Each candidate is assessed for:

1. **Problem fit** — does it solve a problem this repository actually has?
2. **Architecture fit** — does it keep the repository offline, file-based and
   outside the runtime graph?
3. **Licence** — is reuse compatible with the open ecosystem licence review?
4. **Operational cost** — runtime weight, attack surface, maintenance and
   supply-chain risk.
5. **Evidence** — is the claim from a primary source (official repository,
   specification or licence file)?

The default is to adopt **format ideas** and keep **runtime dependencies** to a
minimum. The catalog must remain importable and testable on a host with no ROS,
no DDS, no GPU and no robot.

## 2. Ecosystem components reused, not rebuilt

| Component | Owner | Reused here | Not duplicated here |
|---|---|---|---|
| Repository taxonomy, documentation standard, status vocabulary | `.github` | Layer rules, document set, delivery/verification terms, evidence levels | Governance documents, organization templates |
| Contract proposal process | `jcheng-interfaces` | The rule that cross-repository formats need a proposal and a hash | IDL, schemas, contract hashing |
| Motion authority and safety boundary | `jcheng-system` | The statement that only `ExecuteMotion` moves the robot | Lease, deadman, limits, stop latch, hardware bridge |
| Scene-understanding terminology and evidence rules | `jcheng-perception` | Ore/gangue classes, visible-versus-true naming, forbidden inferences, data-source separation | Segmentation code, scene-state schema, datasets, evidence |
| Suite/report provenance model | `jcheng-benchmark` | Pre-registration, data-source labels, immutable reports | Benchmark runner, metrics implementation, reports |
| Simulation isolation | `jcheng-simulation` | Domain-43 and simulated-truth boundaries referenced by the layer model | Plants, URDFs, worlds, bridges |
| Task sequencing | `jcheng-applications` | The rule that sequencing and gateway intent belong there | Recipe runner, HTTP/WS client, retry policy |
| Device capability profiles | `jcheng-devices` (planned) | The future matching counterpart; no code exists yet | Device drivers, device profiles |

## 3. Third-party dependencies

### 3.1 Runtime

| Dependency | Version range | Use | Licence |
|---|---|---|---|
| Python standard library | >= 3.10 | `argparse`, `json`, `math`, `pathlib`, `dataclasses` | PSF-2.0 |
| [PyYAML](https://github.com/yaml/pyyaml) | `>=6.0,<7` | Safe YAML parsing with a duplicate-key guard | MIT |
| [jsonschema](https://github.com/python-jsonschema/jsonschema) | `>=4.18,<5` | Draft 2020-12 schema validation | MIT |

The runtime dependency set is two packages. Neither performs I/O beyond reading
files supplied by the caller, and neither has a network, ROS or device path.

### 3.2 Test and CI

| Dependency | Version range | Use | Licence |
|---|---|---|---|
| [pytest](https://github.com/pytest-dev/pytest) | `>=7.4,<9` | Test runner | MIT |

CI pins `PyYAML==6.0.2`, `jsonschema==4.23.0` and `pytest==8.3.4` so a cache or
index change cannot silently alter the gate.

## 4. Prior art and specifications

| Source | Use | Adoption |
|---|---|---|
| [JSON Schema 2020-12](https://json-schema.org/draft/2020-12) | Document validation, `$defs`, `if/then`, `additionalProperties` | Adopt the specification and the `jsonschema` implementation; no remote `$ref` |
| [Semantic Versioning 2.0.0](https://semver.org/) | Repository, schema and scenario versions | Adopt |
| [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/) | `CHANGELOG.md` structure | Adopt |
| [`.github` documentation standard](https://github.com/JCHENG-Robotics/.github/blob/main/docs/documentation-standard.md) | Four-document set, status vocabulary, evidence levels | Adopt |
| [`jcheng-perception` Scene State](https://github.com/JCHENG-Robotics/jcheng-perception/blob/main/docs/SCENE_REPRESENTATION.md) | Visible-versus-true naming and forbidden fields | Adopt as terminology, not as a contract |
| [`jcheng-benchmark` protocol](https://github.com/JCHENG-Robotics/jcheng-benchmark/blob/main/docs/BENCHMARK_PROTOCOL.md) | Pre-registered metrics and provenance labels | Adopt as design rules |

No text, schema or code is copied from these sources. Links are references for
reviewers.

## 5. Rejected dependencies

| Candidate | Why rejected |
|---|---|
| `rclpy`, ROS 2 message packages | The catalog has no node, no DDS graph and no runtime. Adding them would violate the SCEN boundary. |
| NumPy / pandas / pyarrow | No numerical or tabular processing is needed; scenario files are small YAML documents. |
| Pydantic / FastAPI | A schema validator and a CLI are enough; an API server would create a runtime surface. |
| Network clients (`requests`, `urllib`) | The catalog reads local files only. |
| Database drivers / ORMs | The registry is a versioned file, reviewable in git. |
| Benchmark runner / metrics library | Owned by `jcheng-benchmark`; duplicating it would create two result authorities. |
| Simulation engines / URDF parsers | Owned by `jcheng-simulation`; environment profiles are declarations, not assets. |
| Perception libraries / model runtimes | Owned by `jcheng-perception`; a scenario must not perform inference. |
| YAML merge-key frameworks | The strict loader is small and rejects ambiguity; a merge framework would add a second semantic layer. |
| JSON5 / TOML scenario formats | JSON Schema + YAML is already the ecosystem convention and is reviewable as text. |

## 6. Supply chain and failure modes

- Two runtime dependencies with permissive licences and no transitive native
  code.
- CI installs exact versions; local development may use compatible ranges.
- The loader uses `yaml.SafeLoader` only; it never constructs arbitrary Python
  objects.
- Duplicate YAML keys are rejected instead of last-wins.
- A malformed document aborts validation; there is no fallback parser.
- The validator has no network path, so a schema cannot fetch a remote `$ref`.
- A denial-of-service through an enormous input file is possible for any local
  parser; the catalog is reviewed source, not an untrusted upload service.

## 7. Licence position

The organization licence review is open, so this repository ships no `LICENSE`
file. Adopting ideas and specifications is allowed; copying code is not approved
until the review and copyright holder are settled. A future
`THIRD_PARTY_NOTICES.md` is required if any code or notice is incorporated.

## 8. Sources

- PyYAML: <https://github.com/yaml/pyyaml> (MIT).
- jsonschema: <https://github.com/python-jsonschema/jsonschema> (MIT).
- pytest: <https://github.com/pytest-dev/pytest> (MIT).
- JSON Schema 2020-12: <https://json-schema.org/draft/2020-12>.
- Semantic Versioning: <https://semver.org/>.
- Keep a Changelog: <https://keepachangelog.com/en/1.1.0/>.

## Related

- [Architecture](ARCHITECTURE.md)
- [SCEN layer](SCEN_LAYER.md)
- [Asset audit](ASSET_AUDIT_20261127.md)
- [License review](../LICENSE-REVIEW.md)
- [`jcheng-interfaces`](https://github.com/JCHENG-Robotics/jcheng-interfaces)
- [`.github`](https://github.com/JCHENG-Robotics/.github)
