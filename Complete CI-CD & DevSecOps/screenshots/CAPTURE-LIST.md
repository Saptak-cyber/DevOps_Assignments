# Screenshots — Complete CI/CD & DevSecOps

The README references these filenames, and every one of them is in this folder.

| File | What it shows |
| --- | --- |
| `01-pipeline-graph-green.png` | Actions → run [37547817960](https://github.com/Saptak-cyber/DevOps_Assignments/actions/runs/37547817960): the workflow graph with all 11 stages green, left to right in the Expected-Flow order |
| `02-sast.png` | Same run, job "4. SAST (Bandit + Semgrep)": Bandit "Run metrics" (High 0 / Medium 0 / Low 5) and Semgrep "Findings: 0" |
| `03-sca.png` | Same run, job "5. SCA (pip-audit + Trivy fs)": `trivy_0.75.0_Linux-64bit.tar.gz: OK`, "No known vulnerabilities found" and the Trivy fs report summary |
| `04-secret-scan.png` | Same run, job "6. Secret Scan (gitleaks)": both "no leaks found" lines, "2 commits scanned", "Total gitleaks findings: 0" |
| `05-docker-build.png` | Same run, job "7. Docker Build": the `docker image ls` + `User=10001 Cmd=[gunicorn ...]` lines |
| `06-ghcr-package.png` | https://github.com/users/Saptak-cyber/packages/container/package/s17-devsecops-dashboard — tags (commit SHA + latest) and digest `sha256:1b0b2b29…` |
| `07-deploy-k8s.png` | Same run, job "11. Deploy to Kubernetes (kind)": rollout status, `kubectl get deploy,rs,pods,svc`, "Running pods use the digest that passed the gate.", "SMOKE TEST PASSED" |
| `08-image-scan.png` | Same run, job "8. Container Image Scan (Trivy)": the per-package report table (all 0) and the severity breakdown `HIGH(no fix): 44` |
| `09-gate-blocked.png` | Run [37547452296](https://github.com/Saptak-cyber/DevOps_Assignments/actions/runs/37547452296): graph with stages 1–8 green, "9. Security Gate" red, 10 and 11 skipped, plus the gate log showing the `cryptography 41.0.0` findings and "SECURITY GATE: FAILED" |
| `10-gate-passed.png` | Run 37547817960, job "9. Security Gate": the PASS table and the ✅ job-summary table on the Summary page |
| `11-run-summary.png` | Run 37547817960 Summary page: job summaries (gate table, pushed digest, SMOKE TEST PASSED) and the Artifacts list (report-sast, report-sca, report-secrets, report-image, docker-image, app-build, unit-test-report) |

Every command needed is in the README, in the section that references the screenshot.

## How these screenshots were produced

Terminal screenshots are renderings of the real command output already captured in the README (same commands, same output; very long outputs are trimmed with a marked `[… lines trimmed …]` line). GitHub Actions and GHCR screenshots are live browser captures of the actual runs and packages (Playwright, signed in as Saptak-cyber).
