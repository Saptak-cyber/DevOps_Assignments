#!/usr/bin/env python3
"""Security gate for the ClinicDesk pipeline (adapted from my Session 17 gate).

Every scanner job runs in report mode and uploads a JSON report. This script reads
them all, counts findings per severity, compares the counts with the thresholds in
security/gate-policy.toml and exits non-zero if any threshold is exceeded. The
"Push images" job `needs:` this job, so a failing gate means nothing reaches GHCR,
the cluster, or the GitOps repo.

Fail-closed: a missing or unreadable report is itself a gate failure.

Reports expected in --reports:
  bandit.json, semgrep.json, pip-audit.json, npm-audit.json, trivy-fs.json,
  trivy-config.json, gitleaks.json, trivy-image-backend.json, trivy-image-frontend.json

Usage: python3 security/security_gate.py --reports reports --policy security/gate-policy.toml
"""

import argparse
import json
import os
import sys
import tomllib
from collections import Counter
from pathlib import Path


def load_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


# ── one parser per tool: return (Counter of severities, list of short descriptions) ──

def parse_bandit(data, _cfg):
    counts, items = Counter(), []
    for r in data.get("results", []):
        sev = r["issue_severity"].upper()
        counts[sev] += 1
        items.append(f"{sev} {r['test_id']} {r['filename']}:{r['line_number']} {r['issue_text']}")
    return counts, items


SEMGREP_MAP = {"ERROR": "HIGH", "CRITICAL": "HIGH", "HIGH": "HIGH",
               "WARNING": "MEDIUM", "MEDIUM": "MEDIUM", "INFO": "LOW", "LOW": "LOW"}


def parse_semgrep(data, _cfg):
    counts, items = Counter(), []
    for r in data.get("results", []):
        sev = SEMGREP_MAP.get(r["extra"]["severity"].upper(), "LOW")
        counts[sev] += 1
        items.append(f"{sev} {r['check_id']} {r['path']}:{r['start']['line']}")
    return counts, items


def parse_pip_audit(data, cfg):
    ignore = set(cfg.get("ignore_ids", []))
    counts, items, seen = Counter(), [], set()
    for dep in data.get("dependencies", []):
        for v in dep.get("vulns", []):
            key = (dep["name"], v["id"])
            if key in seen or v["id"] in ignore or set(v.get("aliases", [])) & ignore:
                continue
            seen.add(key)
            counts["VULN"] += 1
            fix = ", ".join(v.get("fix_versions", [])) or "none"
            items.append(f"{dep['name']}=={dep['version']} {v['id']} (fix: {fix})")
    return counts, items


def parse_npm_audit(data, _cfg):
    """npm audit --json (v7+ format): one entry per vulnerable package."""
    counts, items = Counter(), []
    for name, v in (data.get("vulnerabilities") or {}).items():
        sev = v["severity"].upper()          # info / low / moderate / high / critical
        counts[sev] += 1
        items.append(f"{sev} {name} {v.get('range', '')} fixAvailable={bool(v.get('fixAvailable'))}")
    return counts, items


def parse_trivy_vulns(data, _cfg):
    """Counts as SEVERITY (fix available) and SEVERITY_UNFIXED (no fix yet)."""
    counts, items = Counter(), []
    for res in data.get("Results", []) or []:
        for v in res.get("Vulnerabilities", []) or []:
            sev = v["Severity"].upper()
            fixed = v.get("FixedVersion")
            counts[sev if fixed else f"{sev}_UNFIXED"] += 1
            if sev in ("CRITICAL", "HIGH"):
                items.append(f"{sev} {v['VulnerabilityID']} {v['PkgName']} {v.get('InstalledVersion', '')}"
                             f" -> {fixed or 'no fix'}")
    return counts, items


def parse_trivy_misconfig(data, _cfg):
    counts, items = Counter(), []
    for res in data.get("Results", []) or []:
        for m in res.get("Misconfigurations", []) or []:
            if m.get("Status") != "FAIL":
                continue
            sev = m["Severity"].upper()
            counts[sev] += 1
            items.append(f"{sev} {m['ID']} {res['Target']} - {m['Title']}")
    return counts, items


def parse_gitleaks(data, _cfg):
    counts, items = Counter(), []
    for f in data or []:
        counts["FINDING"] += 1
        items.append(f"{f['RuleID']} {f['File']}:{f['StartLine']}")   # never print the secret itself
    return counts, items


TRIVY_VULN_LIMITS = {"max_critical": "CRITICAL", "max_high": "HIGH",
                     "max_critical_unfixed": "CRITICAL_UNFIXED", "max_high_unfixed": "HIGH_UNFIXED"}

# (stage label, report file, policy section, parser, {policy key: counter key})
CHECKS = [
    ("SAST - Bandit", "bandit.json", "bandit", parse_bandit,
     {"max_high": "HIGH", "max_medium": "MEDIUM", "max_low": "LOW"}),
    ("SAST - Semgrep", "semgrep.json", "semgrep", parse_semgrep,
     {"max_high": "HIGH", "max_medium": "MEDIUM", "max_low": "LOW"}),
    ("SCA - pip-audit", "pip-audit.json", "pip_audit", parse_pip_audit,
     {"max_vulns": "VULN"}),
    ("SCA - npm audit", "npm-audit.json", "npm_audit", parse_npm_audit,
     {"max_critical": "CRITICAL", "max_high": "HIGH", "max_moderate": "MODERATE"}),
    ("SCA - Trivy fs", "trivy-fs.json", "trivy_fs", parse_trivy_vulns, TRIVY_VULN_LIMITS),
    ("IaC - Trivy config", "trivy-config.json", "trivy_config", parse_trivy_misconfig,
     {"max_critical": "CRITICAL", "max_high": "HIGH", "max_medium": "MEDIUM"}),
    ("Secrets - gitleaks", "gitleaks.json", "gitleaks", parse_gitleaks,
     {"max_findings": "FINDING"}),
    ("Image - backend", "trivy-image-backend.json", "trivy_image", parse_trivy_vulns, TRIVY_VULN_LIMITS),
    ("Image - frontend", "trivy-image-frontend.json", "trivy_image", parse_trivy_vulns, TRIVY_VULN_LIMITS),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reports", default="reports")
    ap.add_argument("--policy", default="security/gate-policy.toml")
    args = ap.parse_args()

    policy = tomllib.loads(Path(args.policy).read_text())
    reports = Path(args.reports)
    rows, details, failed = [], [], False

    for label, fname, section, parser, limits in CHECKS:
        cfg = policy.get(section, {})
        path = reports / fname
        if not path.exists():
            rows.append((label, "report missing", "-", "FAIL"))
            failed = True
            continue
        try:
            counts, items = parser(load_json(path), cfg)
        except (ValueError, KeyError, TypeError, AttributeError) as exc:
            rows.append((label, f"unreadable report: {exc}", "-", "FAIL"))
            failed = True
            continue

        verdict, found, allowed = "PASS", [], []
        for key, counter_key in limits.items():
            limit = cfg.get(key, 0)
            n = counts.get(counter_key, 0)
            found.append(f"{counter_key}={n}")
            allowed.append(f"{counter_key}<={'any' if limit < 0 else limit}")
            if limit >= 0 and n > limit:
                verdict = "FAIL"
        failed |= verdict == "FAIL"
        rows.append((label, " ".join(found), " ".join(allowed), verdict))
        if items:
            details.append((label, items))

    w = max(len(r[0]) for r in rows)
    print(f"{'Check'.ljust(w)}  Verdict  Findings  (policy)")
    for label, found, allowed, verdict in rows:
        print(f"{label.ljust(w)}  {verdict:<7}  {found}  ({allowed})")
    for label, items in details:
        print(f"\n{label} findings ({len(items)}):")
        for it in items[:25]:
            print(f"  - {it}")
        if len(items) > 25:
            print(f"  ... {len(items) - 25} more")
    print(f"\nSECURITY GATE: {'FAILED - images will NOT be pushed or deployed' if failed else 'PASSED'}")

    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as fh:
            fh.write(f"## Security gate: {'FAILED' if failed else 'PASSED'}\n\n")
            fh.write("| Check | Verdict | Findings | Policy |\n|---|---|---|---|\n")
            for label, found, allowed, verdict in rows:
                fh.write(f"| {label} | {verdict} | `{found}` | `{allowed}` |\n")

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
