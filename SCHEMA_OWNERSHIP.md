# Schema ownership and consumers

> Status: **repo-local v1.0** as of 2026-11-27. Every JSON Schema in this
> repository is a repository-local document. None is a `jcheng-interfaces`
> contract, and none may be parsed by another repository until an interfaces
> proposal is accepted.

## Ownership table

| Schema file | Schema ID (`$id` suffix) | Version | Status | Owner | Consumers | Promotion trigger |
|---|---|---|---|---|---|---|
| `schemas/scenario-profile.v1.schema.json` | `scen/scenario-profile.v1` | 1.0.0 | `repo-local` | `jcheng-scenarios` | none; planned `jcheng-applications` | applications parses a scenario profile |
| `schemas/scenario-registry.v1.schema.json` | `scen/scenario-registry.v1` | 1.0.0 | `repo-local` | `jcheng-scenarios` | none; planned `jcheng-applications` | any tool outside this repository reads the registry |
| `schemas/task-specification.v1.schema.json` | `scen/task-specification.v1` | 1.0.0 | `repo-local` | `jcheng-scenarios` | none; planned `jcheng-applications`, `jcheng-benchmark` | a recipe or suite references a task ID |
| `schemas/environment-profile.v1.schema.json` | `scen/environment-profile.v1` | 1.0.0 | `repo-local` | `jcheng-scenarios` | none; planned `jcheng-simulation` | simulation loads an environment profile |
| `schemas/semantic-profile.v1.schema.json` | `scen/semantic-profile.v1` | 1.0.0 | `repo-local` | `jcheng-scenarios` | none; planned `jcheng-perception` | perception maps classes by a scenario document |
| `schemas/capability-requirements.v1.schema.json` | `scen/capability-requirements.v1` | 1.0.0 | `repo-local` | `jcheng-scenarios` | none; planned `jcheng-devices` | device matching consumes the requirements |
| `schemas/operational-constraints.v1.schema.json` | `scen/operational-constraints.v1` | 1.0.0 | `repo-local` | `jcheng-scenarios` | none; planned `jcheng-applications` | a recipe reads an operational constraint |
| `schemas/evaluation-specification.v1.schema.json` | `scen/evaluation-specification.v1` | 1.0.0 | `repo-local` | `jcheng-scenarios` | none; planned `jcheng-benchmark` | a benchmark suite references an evaluation ID |

## Rules

1. `Status` is `repo-local` or `contract`. `contract` is reserved for a Schema
   published by `jcheng-interfaces`; this repository has none.
2. A row's `Consumers` lists only repositories that actually parse the file.
   A planned consumer is not a consumer and grants no stability promise.
3. The first external consumer triggers an interfaces proposal. Until that
   proposal is accepted, the external repository must not parse the file.
4. Any new Schema file must be added to this table; the repository gate fails
   when a file under `schemas/` is undeclared.
5. Version bumps that change required fields are breaking; add a new `vN`
   Schema instead of editing a released one.

## Related

- [SCEN layer and consumers](SCEN_LAYER.md)
- [Scenario model](SCENARIO_MODEL.md)
- [Boundary specification](https://github.com/JCHENG-Robotics/.github/blob/main/docs/repo-boundaries.md)
