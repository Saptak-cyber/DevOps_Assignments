# Screenshots — CI/CD & GitHub Actions

The README references these filenames, and every one of them is in this folder.

| File | What it shows |
| --- | --- |
| `01-actions-run-graph.png` | Actions → run [37547563915](https://github.com/Saptak-cyber/DevOps_Assignments/actions/runs/37547563915): the workflow graph with all 9 jobs green (4 matrix legs → report / security / build → docker → deploy) |
| `02-matrix-test-jobs.png` | Same run, left sidebar expanded on the `test` matrix plus the "Show runner details" step of the macOS leg (Runner OS: macOS ARM64) |
| `03-job-summary.png` | Same run, Summary page scrolled to the job summaries: the test-report table, the image/digest block, "SMOKE TEST PASSED" |
| `04-secret-masked.png` | Job "CD / Docker build & push to GHCR" → step "Secrets demo: GITHUB_TOKEN is masked in logs" showing `Echoing the token anyway -> ***` |
| `05-artifacts.png` | Same run, Artifacts section at the bottom of the Summary page (calculator-build + 4 test-report-* + .dockerbuild) |
| `06-ghcr-package.png` | https://github.com/users/Saptak-cyber/packages/container/package/s16-calculator — package page with the commit-SHA tags and `latest`, and the linked repository |
| `07-deploy-smoke-test.png` | Job "CD / Deploy to Kubernetes (kind) + smoke test": the rollout status + `kubectl get deploy,rs,pods,svc` + "SMOKE TEST PASSED" steps expanded |
| `08-failed-run.png` | Run [37547931810](https://github.com/Saptak-cyber/DevOps_Assignments/actions/runs/37547931810): graph with the 4 red test legs and every downstream job skipped, plus the `assert 16 == 15` failure |
| `09-local-tests.png` | Terminal: `python3 -m pytest -v --cov=app --cov-report=term-missing` in this folder (12 passed, 98%) |
| `10-local-docker.png` | Terminal: `docker build` + `docker run` + the `curl` calls and `docker ps` showing `(healthy)` |

Every command needed is in the README, in the section that references the screenshot.

## How these screenshots were produced

Terminal screenshots are renderings of the real command output already captured in the README (same commands, same output; very long outputs are trimmed with a marked `[… lines trimmed …]` line). GitHub Actions and GHCR screenshots are live browser captures of the actual runs and packages (Playwright, signed in as Saptak-cyber).
