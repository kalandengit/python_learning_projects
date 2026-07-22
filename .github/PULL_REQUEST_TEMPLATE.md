<!--
  Definition of Done checklist. For AI School Assistant changes this mirrors
  AISchoolAssistant/docs/adr/0003-definition-of-done.md. Delete sections that do
  not apply to your change and explain any unchecked box.
-->

## Summary

<!-- What does this change do, and why? Link the issue / work package. -->

## Type of change

- [ ] Feature
- [ ] Bug fix
- [ ] Refactor / chore
- [ ] Documentation
- [ ] Infrastructure / CI

## Universal Definition of Done

- [ ] Code compiles and typechecks.
- [ ] Lint passes with zero warnings.
- [ ] Formatting clean (`prettier --check`).
- [ ] Tests pass; coverage ≥ 90% on changed packages (unit + integration; e2e where applicable).
- [ ] Public APIs documented (OpenAPI) + README/docs updated.
- [ ] Security reviewed (authz, input validation, secrets, output encoding); dependency + secret scan clean.
- [ ] DB changes ship with migrations, audit fields, UUID keys (no `synchronize` in prod).
- [ ] Observability present: structured logs, metrics, health `live`/`ready`, traces.
- [ ] Backward compatibility preserved (or a documented, versioned migration path).

## AI capability gates (only if the change touches AI)

- [ ] AI accessed only through the AI SDK via a registered capability (no direct provider calls).
- [ ] The capability has an evaluation suite (accuracy + safety + regression) that passes threshold.
- [ ] Governance metadata complete (owner, data classification, PII policy, model allow-list).
- [ ] Capability invocations are traced and emit Event-Catalog events.

## Notes for reviewers

<!-- Anything reviewers should focus on, trade-offs, follow-ups. -->
