# Evidence

> Status: **offline scaffold evidence only** as of 2026-11-27.

## Policy

- Evidence is the captured output of a command that was actually run, stored
  under `evidence/<kind>_<YYYYMMDD>_<slug>/`.
- A result file is never hand-written, edited or back-filled. A rerun creates a
  new directory; it does not overwrite an old result.
- Dates are ISO 8601. Every directory has a `README.md` stating scope, commands,
  environment and limitations.
- No dataset, recording, model weight or robot asset is stored here.
- Scenario declarations are not evidence. A passing schema check is L0/L1
  evidence, not a scenario result or a hardware validation.
- Synthetic, public, mock, simulation and replay results are labelled by source
  and are never reported as hardware validation.

## Current evidence

| Directory | Scope | Levels |
|---|---|---|
| [`20261127_scaffold/`](20261127_scaffold/README.md) | Repository gate and test suite for v0.1.0 | L0, L1 |

There is no L2–L5 evidence. No consumer integration, evaluation run or hardware
session exists.

## Naming

```text
evidence/
└── <kind>_<YYYYMMDD>_<slug>/
    ├── README.md
    ├── gate.txt
    └── pytest.txt
```

Supported kinds: `scaffold`, `validation`, `integration`, `evaluation`,
`hardware`. A future kind must be documented in the directory README.

## Related

- [Acceptance](../ACCEPTANCE.md)
- [Roadmap](../ROADMAP.md)
- [`.github` documentation standard](https://github.com/JCHENG-Robotics/.github/blob/main/docs/documentation-standard.md)
