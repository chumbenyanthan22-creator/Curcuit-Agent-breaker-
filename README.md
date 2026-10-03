# AgentBreaker

**Loop detection and cost tracking for LangChain agents.** AgentBreaker provides a deterministic pre-dispatch guard, Supabase telemetry logging, Slack loop alerts, and estimate-based spend tracking.

## Install

```bash
pip install agentbreaker
```

The package requires Python 3.11+ and includes the public exports `LoopDetector` and `LoopBreakerHandler`:

```python
from agentbreaker import LoopBreakerHandler, LoopDetector
```

`Detector` remains available as a compatibility alias for `LoopDetector`. The optional Slack webhook endpoint requires the web extra:

```bash
pip install "agentbreaker[web]"
```

## Repository layout

- `agentbreaker/` — distributable Python package
- `examples/` — runnable integration examples kept at the repository root
- `tests/` — detector, pipeline, cost, and Slack tests
- `supabase/` — database migrations and Supabase integration documentation
- `client/` — React/Vite dashboard

Top-level Python modules retained from earlier prototypes are compatibility shims that re-export the package modules. New code should import from `agentbreaker`.

## Local development

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e ".[test,web]"
pytest -q
```

Configure integrations with environment variables; do not commit secrets. See `.env.example`, `SUPABASE.md`, and `SLACK.md`. The published PyPI distribution is named `supabase`; it provides the Supabase Python client commonly referred to as `supabase-py`.

## Build and verify locally

Install the build tools and create both an sdist and wheel:

```bash
python -m pip install --upgrade build
rm -rf dist build *.egg-info
python -m build
python -m venv /tmp/agentbreaker-wheel-check
/tmp/agentbreaker-wheel-check/bin/python -m pip install dist/agentbreaker-0.1.0-py3-none-any.whl
/tmp/agentbreaker-wheel-check/bin/python -c "from agentbreaker import LoopBreakerHandler, LoopDetector; print(LoopDetector, LoopBreakerHandler)"
```

`dist/` is intentionally ignored by Git and is not published automatically.

## Prepare a future PyPI upload

1. Create a PyPI or TestPyPI account and generate a project-scoped API token.
2. Copy `.pypirc.example` to `~/.pypirc` and replace the placeholder token locally, or use Twine's environment-based credentials. Never commit the configured file.
3. Build a clean distribution and optionally validate it on TestPyPI:

   ```bash
   rm -rf dist build *.egg-info
   python -m build
   python -m twine check dist/*
   python -m twine upload --repository testpypi dist/*
   ```

4. When ready for the real release, upload the same version to PyPI:

   ```bash
   python -m twine upload dist/*
   ```

This repository is **not uploaded to PyPI yet**. Increment the version in `pyproject.toml` before publishing a subsequent release.

## Existing dashboard

The AgentBreaker dashboard remains a separate React application and continues to use the existing Supabase schema and telemetry pipeline. The Python package restructure does not change the database tables or Slack workflow.
