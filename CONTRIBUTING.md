# Contributing to shamtest

Thank you for your interest in improving `shamtest`! We welcome contributions from developers, test engineers, and AI practitioners.

## Development Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Nithinfgs/shamtest.git
   cd shamtest
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install in editable mode:**
   ```bash
   pip install -e .
   ```

4. **Run the test suite:**
   ```bash
   python3 -m unittest discover -s tests -p "test_*.py" -v
   ```

## Adding a New Rule

1. Create a new rule module under `shamtest/rules/` (or extend an existing one).
2. Subclass `shamtest.rules.base.Rule` and assign a unique rule ID (e.g., `SHAM011`).
3. Implement `inspect_node(node, context)` or `inspect_function(func_node, context)`.
4. Register the new rule in `shamtest/rules/__init__.py`.
5. Add comprehensive unit tests in `tests/test_<rule_name>.py` covering positive and negative cases.
6. Document the rule in `README.md` and update `CHANGELOG.md`.

## Coding Guidelines

- `shamtest` maintains zero external runtime dependencies. All core logic must rely only on the Python standard library (`ast`, `argparse`, `dataclasses`, `pathlib`, `typing`, etc.).
- Ensure all test assertions in unit tests are meaningful and pass `shamtest tests/`.
- Maintain clean type annotations and readable docstrings.
