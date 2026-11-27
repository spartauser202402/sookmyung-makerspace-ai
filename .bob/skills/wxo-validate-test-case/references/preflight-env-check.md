<!-- SHARED FILE: keep in sync with skills/wxo-test-case-generation/references/preflight-env-check.md -->
# Preflight environment check

Run this check before starting test generation or validation.

1. Choose Python for the user's target project, not the skill's installation directory. Follow explicit user or project instructions first. Otherwise inspect the active environment, an existing project environment such as `.venv`, and relevant project configuration. For Poetry or Pipenv, query the existing environment's interpreter if needed. For uv, use the existing project environment without syncing. A `pyproject.toml` or `.python-version` alone does not identify an installed interpreter. Do not create environments, install packages, or sync dependencies during discovery.
2. If several environments are plausible and project instructions do not resolve the choice, ask which to use. If no project environment is identified, use `python` on PATH, falling back to `python3` only when `python` is unavailable.
3. Run the shared script with the selected Python executable:

   ```bash
   bash "<skills-directory>/verify-eval-framework.sh" "<python-executable>"
   ```

   Resolve `<skills-directory>` from this skill's actual location, following symlinks: the script and this reference are beside the skill folders. Pass one executable path or command name, not a launcher string such as `poetry run python`.
4. Continue only on exit code `0`. The check prints the interpreter's full path and verifies `import agentops`. Use that interpreter for all subsequent local Python commands, including commands shown as `python` in references. Do not switch environments merely to find one where the import succeeds.
5. If the script is missing or the check fails, stop and report the error and suggested fix. Rerun after the environment is fixed. A successful check can be reused for follow-ups within the same request unless the environment changes.
