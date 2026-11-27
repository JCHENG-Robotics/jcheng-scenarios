# Authoring guide

> Status: **v1** as of 2026-11-27. Applies to every scenario added to this
> repository.

## 1. Before authoring

- Confirm the scenario does not overlap an existing repository's responsibility;
  read [SCEN_LAYER.md](SCEN_LAYER.md).
- Confirm the scenario has a real task, a traceable provenance and a reviewer.
- Do not create an empty scenario directory as a placeholder. Candidates stay
  in [ROADMAP.md](../ROADMAP.md) until they can be authored.

## 2. Add a scenario

1. Choose a stable ID: `^[a-z][a-z0-9_]*$`, for example `ore_sorting`. An ID is
   never reused for a different scenario.
2. Create `scenarios/<id>/` and copy the seven-file structure from
   `scenarios/ore_sorting/`. Do not copy its values; author each field from the
   scenario's own provenance.
3. Fill `scenario.yaml` with identity, provenance, consumers and boundaries.
   Every consumer starts at `integration: Not started` until an integration is
   actually accepted.
4. Fill the six sub-profiles:
   - environment: frames, stations, zones, lighting, surfaces, constraints;
   - semantics: classes, observable attributes, relations, forbidden
     inferences;
   - task: goal, preconditions, success and failure conditions, out-of-scope;
   - capability requirements: device, algorithm and interface needs;
   - operational constraints: business, environment, risks, safety boundary;
   - evaluation: metrics, protocol, reporting owner.
5. Add one registry entry in `registry.yaml` with the same ID, version, domain,
   delivery and verification.
6. Run validation and tests:

   ```bash
   jcheng-scenarios validate --root .
   python3 -m pytest -q
   bash scripts/check_repo_gate.sh
   ```

7. Add a changelog entry and update the roadmap if the milestone state changes.

## 3. Authoring rules

- **No fabricated facts.** A parameter is `design_target`, `measured`, `derived`
  or `assumed`. A measured value links to evidence. A value without a basis is
  not admitted.
- **No forbidden inferences.** Do not add grade, composition, mass, volume,
  true centroid, full extent or economic value unless a dedicated evidence
  method and a schema change are accepted first.
- **No execution plan.** Do not add joint trajectories, waypoints, gripper
  command sequences, retries or timing loops. Those belong to applications and
  the system layer.
- **No device claim.** Do not name a device model or assert compatibility in a
  scenario. Capability requirements are abstract; matching is a separate
  offline report.
- **No result.** Do not record success rates, accuracy, latency or a pass/fail
  result in a scenario. Results belong to `jcheng-benchmark`.
- **No runtime code.** Do not add ROS nodes, DDS configuration, device access,
  network clients or a task executor.
- **Status vocabulary is fixed.** Use only `Complete`, `In progress`, `Planned`,
  `Not started` for delivery and `Verified`, `Partially verified`, `Unverified`,
  `Inconclusive` for verification.

## 4. Review checklist

- [ ] ID is unique and stable; directory name matches the ID.
- [ ] Registry and profile agree on ID, version, domain, delivery and verification.
- [ ] Every profile has provenance with at least one source.
- [ ] Every parameter has an explicit basis.
- [ ] Every condition has an ID, description, measurable flag and verification.
- [ ] Every metric has a definition, unit, direction and threshold status.
- [ ] Forbidden inferences are declared and absent from the data.
- [ ] Consumers are honest: `Not started` unless a real integration exists.
- [ ] The safety boundary names `jcheng-system` and does not claim authority.
- [ ] `validate`, `pytest` and the repository gate pass.
- [ ] `CHANGELOG.md` and `ROADMAP.md` are updated when scope changes.

## 5. Candidate policy

`shopping_mall`, `warehouse` and `manufacturing` are candidates in the roadmap,
not directories. A candidate is admitted only after M2/M3 accept the vocabulary
and the task model it depends on. An empty shell is worse than an honest
`Not started`: it looks like coverage without evidence.

## Related

- [Scenario model](SCENARIO_MODEL.md)
- [SCEN layer](SCEN_LAYER.md)
- [Evaluation model](EVALUATION_MODEL.md)
- [Reference scenario](../scenarios/ore_sorting/scenario.yaml)
- [Catalog rules](../scenarios/README.md)
