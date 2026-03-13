# Python Style Guide — NEOS Scripts

## General
- Python 3.14, stdlib only, no external dependencies
- Scripts must be runnable standalone: `python script_name.py [args]`
- Use `argparse` for CLI interfaces
- Use `pathlib` for all file operations

## Formatting
- 4-space indentation
- Max line length: 100 characters
- Use f-strings for string formatting
- Type hints on all function signatures

## Structure
- One script per file, clear single responsibility
- `if __name__ == "__main__":` guard on all scripts
- Docstring on every public function
- Exit codes: 0 = success, 1 = validation failure, 2 = error

## Naming
- `snake_case` for files, functions, variables
- `UPPER_CASE` for constants
- Descriptive names — `validate_skill_structure()` not `check()`
