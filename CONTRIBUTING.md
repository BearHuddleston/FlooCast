# Contributing to FlooCast

## Development Setup

1. Clone the repository:
   ```bash
   git clone git@github.com:BearHuddleston/FlooCast.git
   cd FlooCast
   ```

2. Install system dependencies:
   ```bash
   sudo apt install python3-dev python3-wxgtk4.0 libsndfile1 gir1.2-appindicator3-0.1
   ```

3. Install uv and sync dependencies with dev tools:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   uv sync --extra dev
   ```

4. Install pre-commit hooks:
   ```bash
   uv run pre-commit install
   uv run pre-commit install --hook-type commit-msg
   ```

## Development Workflow

1. Create a feature branch:
   ```bash
   git checkout -b feat/your-feature
   ```

2. Make changes and run linting:
   ```bash
   uv run ruff check .
   uv run ruff format .
   ```

3. Run tests:
   ```bash
   uv run pytest
   ```

4. Commit with semantic commit messages:
   ```
   feat: add new feature
   fix: resolve bug
   refactor: improve code structure
   test: add tests
   docs: update documentation
   chore: maintenance tasks
   ```

5. Push and create a pull request.

## Code Style

- Follow PEP 8 (enforced by ruff)
- Line length: 100 characters
- Use type hints where practical

## Testing

- Add tests for new functionality in `tests/`
- Ensure all tests pass before submitting PR
