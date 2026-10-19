# Roadmap

## Completed

- [x] Runnable standard-library CLI foundation
- [x] Behavioral tests and documented local examples
- [x] Input handling, explicit limitations and setup guide

## Next

- [x] Add top-level inline JSON request/response type and required-property checks
- [ ] Extend body checks to nested property types and constraints
- [x] Resolve same-document parameter references with cycle detection
- [ ] Extend reference resolution to path items and schemas
- [ ] Add readable HTML diff and CI integration

## Continuity

Initial foundation implemented and checked on 2026-10-17. Inspect current code and commits before continuing. Prioritize the first unchecked item and keep improvements small enough to verify. No visual dashboard has been implemented.


2026-10-18: Added bounded same-document parameter reference resolution, escape handling and inheritance tests. Ten tests pass. Request/response schema checks remain the next domain feature.


2026-10-19: Added directional top-level JSON body checks with coverage warnings for unsupported schemas. Nested properties, removed statuses/media and schema references remain outside checked scope. Next: nested body coverage or local reference extension.
