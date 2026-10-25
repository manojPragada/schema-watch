# Roadmap

## Completed

- [x] Runnable standard-library CLI foundation
- [x] Behavioral tests and documented local examples
- [x] Input handling, explicit limitations and setup guide

## Next

- [x] Add top-level inline JSON request/response type and required-property checks
- [ ] Extend body checks to nested property types and constraints
- [x] Resolve same-document parameter references with cycle detection
- [x] Resolve bounded same-document schema references
- [x] Extend reference resolution to path items
- [x] Add readable standalone HTML diff
- [x] Add documented CI annotations and opt-in strict warning policy

## Continuity

2026-10-25: Added bounded same-document path-item reference resolution with pointer decoding, missing-target and cycle checks. Reference siblings remain an explicit coverage error rather than being merged ambiguously. Next: expand directional constraint coverage.

2026-10-24: Added bounded same-document schema-reference expansion during nested request/response comparison, including pointer decoding, missing-target errors and cycle detection. External references still never trigger network access. Next: referenced path items.

2026-10-22: Added escaped GitHub Actions error/warning annotations and an opt-in `--fail-on-warnings` policy while preserving the existing 0/1/2 exit contract. Next: bounded local schema-reference expansion.

2026-10-21: Added a responsive standalone HTML report with finding counts and keyboard-accessible breaking/warning filters. Reports contain no external assets or requests and preserve the CLI's compatibility exit code. Next: local schema references and documented CI annotations.

2026-10-20: Added bounded nested-property/array-item type and requiredness comparison, exact schema paths and explicit warnings for unsupported constraints/missing properties/depth limits. Seven new regression tests. Next: local schema references and constraint coverage; nested support remains partial, not complete compatibility analysis.

Initial foundation implemented and checked on 2026-10-17. Inspect current code and commits before continuing. Prioritize the first unchecked item and keep improvements small enough to verify. No visual dashboard has been implemented.


2026-10-18: Added bounded same-document parameter reference resolution, escape handling and inheritance tests. Ten tests pass. Request/response schema checks remain the next domain feature.


2026-10-19: Added directional top-level JSON body checks with coverage warnings for unsupported schemas. Nested properties, removed statuses/media and schema references remain outside checked scope. Next: nested body coverage or local reference extension.

