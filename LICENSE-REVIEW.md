# License review — pending

This repository does **not** ship a `LICENSE` file. Copyright is reserved; the
JCHENG-Robotics license review is in progress, consistent with `.github`,
`jcheng-interfaces`, `jcheng-system`, `jcheng-perception`, `jcheng-ops`,
`jcheng-studio`, `jcheng-applications`, `jcheng-learning`, `jcheng-teleop` and
`jcheng-simulation`.

## What is in this repository

- Original YAML scenario declarations, JSON Schemas, Python validation code,
  shell and Markdown written for this repository.
- No recorded dataset, model weight, vendor source or copied third-party code.
- No robot asset, URDF, mesh or world file.
- The `ore_sorting` scenario is a design declaration dated 2026-11-27. It is not
  derived from a customer workcell and contains no measured production data.

## Third-party runtime dependencies

| Dependency | Use | License note |
|---|---|---|
| Python standard library (`argparse`, `json`, `math`, `pathlib`, `dataclasses`) | catalog and CLI | PSF-2.0 |
| PyYAML 6.x | YAML parsing | MIT |
| jsonschema 4.x | JSON Schema validation | MIT |
| pytest 7.4+ | tests only | MIT |

None of these are vendored. A future `THIRD_PARTY_NOTICES.md` is required if
any code or notice is incorporated.

## Data policy

Datasets, recordings and robot assets stay outside the repository. A scenario
references a data source by kind and a provenance note; it never embeds a
recording. The 2026-11-26/27 ore datasets and evidence remain the property of
`jcheng-perception` and are not copied here.

## Secrets and weights

The repository contains no credentials. `scripts/check_repo_gate.sh` fails if a
token-like value, a `*.env` file or a model weight / recorded bag appears in the
tree.
