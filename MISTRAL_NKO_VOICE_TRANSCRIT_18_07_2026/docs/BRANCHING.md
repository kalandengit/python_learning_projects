# Branching & workflow

## Long-lived branches

- `main` — docs, CI, governance. Protected; PRs only.
- `backend` — the FastAPI service (`backend/`).
- `android` — the native Android app (`android-app/`).
- `ios` — the native iOS app (`ios-app/`).

Day-to-day work happens on short-lived feature branches cut from the
component branch (`feature/…`, `hotfix/…`), merged back by PR.
Component branches merge into `main` at release points.

## Recommended branch protection (GitHub → Settings → Branches)

For `main` and each component branch:
- Require a pull request before merging (1 approval).
- Require status checks: the component's CI workflow.
- Block force pushes; require linear history.

## CI

Workflows in `.github/workflows/` are path-filtered:

| Workflow | Trigger paths | Jobs |
|---|---|---|
| `backend-ci.yml` | `backend/**` | ruff, pytest, bandit, pip-audit, Docker build |
| `android-ci.yml` | `android-app/**` | Gradle assemble + unit tests |
| `ios-ci.yml` | `ios-app/**` | XcodeGen + xcodebuild (macOS runner) |

## Releases

Tag from `main` as `vMAJOR.MINOR.PATCH`. The rebuild starts at `v2.0.0`
(v1.x is the original N'Ko Voice Transcriptor line).
