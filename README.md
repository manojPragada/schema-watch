# Schema Watch

Find removed HTTP operations and newly required inline or same-document referenced parameters between OpenAPI 3.x JSON documents.

**Status:** runnable CLI plus standalone HTML findings report. No hosted demo is available. Examples use synthetic offline data. Python 3.10+; standard library only. Validated with Python 3.12.

## Quick start

```bash
git clone https://github.com/manojPragada/schema-watch.git
cd schema-watch
python --version
python app.py examples/before.json examples/before.json
# Expected exit code 1: the second specification removes GET /pets.
python app.py examples/before.json examples/after.json
```

Use `python3` if your system does not provide `python`. No package installation or API key is needed.

## Usage and behavior

Numeric `minimum`, `maximum`, `exclusiveMinimum`, and `exclusiveMaximum` transitions are directional: tighter request bounds and weaker response guarantees are breaking changes.

Exit codes: `0` means no changes detected within the supported scope, `1` means breaking changes found, `2` means invalid input or a read error. Path-level parameters are inherited; operation-level declarations override parameters with the same location and name.

Run `python app.py --help` for available options.

Same-document JSON Pointer references are resolved for parameters, schemas and path items with bounded chains and cycle detection. External references never trigger network access. Path-item `$ref` siblings are rejected because their merge semantics are not analyzed.

Nested enum/const checks are directional: removing an accepted request value or adding a possible response value is reported as breaking. Both sides must expose 1–100 literal values; partial transitions remain coverage warnings rather than guesses.

## CI annotations and warning policy

In GitHub Actions, emit escaped workflow annotations for every supported breaking change and coverage warning:

```bash
python app.py before.json after.json --github-annotations
python app.py before.json after.json --github-annotations --fail-on-warnings
```

Breaking changes always return exit code 1. Coverage warnings normally preserve exit code 0, because they mean “not checked,” not “known break”; `--fail-on-warnings` opts into exit 1 for stricter repositories. Invalid inputs still return 2. The annotation output escapes workflow-command control characters and names the compared `after` file, but does not invent source line numbers.

## Local HTML comparison report

```bash
python app.py examples/before.json examples/after.json --html schema-report.html
```

The command writes a standalone responsive report with finding totals and interactive breaking-change/coverage-warning filters. It intentionally preserves the normal exit code (`1` when supported checks detect a break), does not overwrite an existing report and contains no external assets, analytics or network requests.

## Reusable parameter references

Parameter lists now support references such as `{"$ref":"#/components/parameters/id"}`. Same-document chains are resolved with cycle detection and a 100-link bound. URI-fragment percent encoding and JSON Pointer `~1`/`~0` escapes are supported. Missing targets, non-object parameters, external references and cycles fail with exit code 2 instead of being silently skipped. No reference triggers a network request.

Resolution applies to path-level and operation-level parameter lists. Operation-level parameters still override matching inherited parameters. `$ref` siblings do not change the referenced parameter's requiredness. This is deliberately narrower than full OpenAPI reference support; see the [OpenAPI reference rules](https://spec.openapis.org/oas/v3.1.0.html#reference-object).

## Directional body-contract checks

For inline `application/json` request and matching-status response schemas, the checker now detects narrowed accepted request types, widened response types, newly required request properties and removed response required-property guarantees. It also detects a newly required request body. Integer is treated as a subset of number; single type names and OpenAPI 3.0 `nullable` are supported.

These are **bounded, partial checks**, not complete schema compatibility analysis. Inline nested properties and homogeneous array items are traversed up to 32 levels. Bounded same-document schema references are expanded; missing targets and cycles become coverage warnings and external references never cause network access. Constraints are not compared. Composition, boolean schemas, type arrays and readOnly/writeOnly property contracts produce `coverage_warnings` and are skipped. Exit 0 means no detected changes within checked scope, even when warnings exist; CI users must inspect warnings too. A required-property result follows the [JSON Schema object contract](https://json-schema.org/understanding-json-schema/reference/object); response/request direction is the tool's compatibility rule.

## Development and verification

```bash
python -m unittest discover -s tests -v
python -m compileall -q annotations.py app.py contracts.py report.py tests
```

Tests cover operation/parameter comparisons, same-document references, pointer escaping, inheritance and rejected reference inputs. There is no build step or configured linter; compilation is a syntax check, not linting.

## Configuration

Configuration is provided through CLI arguments. No environment variables, `.env` file, credentials or external services are required. `.env.example` documents this intentionally empty configuration contract.

## Structure

```text
app.py          CLI and operation/parameter checks
annotations.py  escaped GitHub Actions findings output
contracts.py    partial directional JSON body checks
report.py       standalone interactive HTML findings renderer
examples/       synthetic example inputs
tests/          behavioral unit tests
ROADMAP.md      completed work and prioritized next steps
.env.example    configuration notes
```



## Architecture

Body type and required-property checks recurse through common object properties and homogeneous array `items`, including bounded same-document `$ref` targets, with paths such as `$["profile"]["id"]` and `$[*]`. Request narrowing and response widening are checked directionally. Nesting beyond 32 levels, unresolved/external references, composition, boolean schemas, property additions/removals and unsupported constraints produce coverage warnings. Numeric/string limits, enums, formats and additional-property policies are not compatibility-checked. No findings is **not** proof of compatibility; inspect `coverage_warnings`, which do not change the existing exit code. This remains a partial checker, not a full schema validator.

Semantics references: [JSON Schema object properties](https://json-schema.org/understanding-json-schema/reference/object) and [OpenAPI Schema Object](https://spec.openapis.org/oas/v3.0.4.html#schema-object). `readOnly`/`writeOnly` contracts remain explicitly unsupported rather than guessed across dialects.

The dependency-free CLI in app.py handles operation/parameter checks; contracts.py handles bounded inline body comparison. No network requests or external reference resolution occur. A package and UI remain future work; see the roadmap.

## Limitations

This is a partial checker, not an OpenAPI validator or compatibility guarantee. Body checks cover bounded inline or same-document-referenced application/json types and required-property sets, including common nested properties and homogeneous array items. Enum/range constraints, removed media types/status codes, security requirements and YAML are not checked. Path-item `$ref` references are rejected. Parameter and schema references support same-document object-key JSON Pointers only; array-index pointers, external files and network references are not supported. No dashboard yet.

## Running and deployment

Run locally from the repository using the commands above. No hosted deployment has been configured. Do not expose a development process publicly. A web deployment guide will be added when a web application actually exists.

## Troubleshooting

- **Python not found:** install Python 3.10+ or try `python3`.
- **File not found:** run from the repository root or provide an absolute input path.
- **Invalid input:** inspect the error printed to standard error and compare with the examples.
- **Permission denied:** choose a folder you own; avoid running as administrator.

## Contributing and credits

Open an issue describing the observed behavior, expected result and a minimal synthetic example. Keep changes focused, include behavioral tests, run the checks above, and update this README when commands or capabilities change. Do not submit credentials or private input files.

Implementation and synthetic examples are original to this repository. There are no third-party runtime dependencies or media assets. A redistribution license has not yet been selected; public visibility alone does not grant an open-source license.



