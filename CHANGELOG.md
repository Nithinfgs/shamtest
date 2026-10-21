# Changelog

All notable changes to `shamtest` will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-10-21

### Added
- Core AST static inspection engine with sub-50ms execution speed.
- Zero runtime dependencies (pure Python standard library).
- 10 detection rules targeting common AI-generated test smells:
  - `SHAM001`: Tautological assertions (`assert True`, `assert x == x`, `assert 1 == 1`).
  - `SHAM002`: Trivially true checks (`len(...) >= 0`, `status_code != 500`).
  - `SHAM003`: Truthiness assertion on `Mock` instances (`bool(Mock()) == True`).
  - `SHAM004`: Uncalled mock assertions missing parentheses (`mock.assert_called_once`).
  - `SHAM005`: Misspelled mock assertion method names (`mock.asser_called()`).
  - `SHAM006`: Test functions executing code with zero assertions.
  - `SHAM007`: Swallowed exceptions via `try ... except: pass` in tests.
  - `SHAM008`: Overly broad exception captures (`pytest.raises(Exception)`).
  - `SHAM009`: Self-validating mock loops (mock return value asserted against itself).
  - `SHAM010`: Standalone mock condition expressions (`mock.called` without assert).
- Interactive colored CLI with source code pointers, line locations, and remediation suggestions.
- Git diff integration: `--diff`, `--staged`, and `--base <ref>`.
- Machine-readable `--json` output format.
- GitHub Code Scanning SARIF v2.1.0 output format (`--sarif`).
- Inline suppression support (`# shamtest: disable=SHAM001` or `# noqa: shamtest`).
- Config file loading via `.shamtest.toml` or `pyproject.toml` `[tool.shamtest]`.
- Hollow Test Index calculation (% of tests with sham patterns).
