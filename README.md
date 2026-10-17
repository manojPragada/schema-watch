# Schema Watch

Find removed HTTP operations and newly required inline parameters between OpenAPI 3.x JSON documents.

**Status:** runnable CLI foundation. No hosted demo or dashboard is available yet. Examples use synthetic offline data. Python 3.10+; standard library only. Validated with Python 3.12.

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

Exit codes: `0` means no changes detected within the supported scope, `1` means breaking changes found, `2` means invalid input or a read error. Path-level parameters are inherited; operation-level declarations override parameters with the same location and name.

Run `python app.py --help` for available options.

## Development and verification

```bash
python -m unittest discover -s tests -v
python -m compileall -q app.py tests
```

Tests exercise behavior with temporary/local data. PufferFish's recording test uses only a loopback HTTP server. There is no build step or configured linter; compilation is a syntax check, not linting.

## Configuration

Configuration is provided through CLI arguments. No environment variables, `.env` file, credentials or external services are required. `.env.example` documents this intentionally empty configuration contract.

## Structure

```text
app.py          CLI and core domain functions
examples/       synthetic example inputs (queue-lab uses commands above)
tests/          behavioral unit tests
ROADMAP.md      completed work and prioritized next steps
.env.example    configuration notes
```



## Architecture

A single dependency-free module exposes importable core functions and a CLI entry point. Filesystem and network access occur only when the corresponding commands run. This small foundation will be split into a package, integrations and UI as those features arrive; see the roadmap.

## Limitations

This is a partial checker, not an OpenAPI validator or compatibility guarantee. It does not check request/response schemas, status codes, content types, security requirements or YAML. Path-item and parameter `$ref` references are rejected; nested schema references are not analyzed. No dashboard yet.

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
