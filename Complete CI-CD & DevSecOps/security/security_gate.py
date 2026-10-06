#!/usr/bin/env python3
"""Security gate for the Session 17 DevSecOps pipeline.

Every scanner job runs in *report* mode and uploads a JSON report. This script
reads all of them, counts findings per severity, compares the counts with the
thresholds in security/gate-policy.toml and exits non-zero if any threshold is
exceeded. The pipeline's "Push Image" job `needs:` this job, so a failing gate
means the image never reaches the registry or the cluster.

Fail-closed: a missing or unreadable report is itself a gate failure.

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

def parse_bandit(data):
    counts, items = Counter(), []
    for r in data.get("results", []):
        sev = r["issue_severity"].upper()
        counts[sev] += 1
        items.append(f"{sev} {r['test_id']} {r['filename']}:{r['line_number']} {r['issue_text']}")
    return counts, items


SEMGREP_MAP = {"ERROR": "HIGH", "CRITICAL": "HIGH", "HIGH": "HIGH",
               "WARNING": "MEDIUM", "MEDIUM": "MEDIUM", "INFO": "LOW", "LOW": "LOW"}


def parse_semgrep(data):
    counts, items = Counter(), []
    for r in data.get("results", []):
        sev = SEMGREP_MAP.get(r["extra"]["severity"].upper(), "LOW")
        counts[sev] += 1
        items.append(f"{sev} {r['check_id']} {r['path']}:{r['start']['line']}")
    return counts, items


def parse_pip_audit(data, ignore_ids):
    counts, items, seen = Counter(), [], set()
    for dep in data.get("dependencies", []):
        for v in dep.get("vulns", []):
            key = (dep["name"], v["id"])
            if key in seen or v["id"] in ignore_ids or set(v.get("aliases", [])) & ignore_ids:
                continue
            seen.add(key)
            counts["VULN"] += 1
            fix = ", ".join(v.get("fix_versions", [])) or "none"
            items.append(f"{dep['name']}=={dep['version']} {v['id']} (fix: {fix})")
    return counts, items


def parse_trivy(data):
    """Counts as SEVERITY (fix available) and SEVERITY_UNFIXED (no fix yet)."""
    counts, items = Counter(), []
    for res in data.get("Results", []) or []:
        for v in res.get("Vulnerabilities", []) or []:
            sev = v["Severity"].upper()
            fixed = v.get("FixedVersion")
            counts[sev if fixed else f"{sev}_UNFIXED"] += 1
            # list what can block; unfixed HIGH (no upgrade exists yet) is only counted
            if sev == "CRITICAL" or (sev == "HIGH" and fixed):
                items.append(f"{sev} {v['VulnerabilityID']} {v['PkgName']} {v.get('InstalledVersion', '')}"
                             f" -> {fixed or 'no fix'}")
    return counts, items


def parse_gitleaks(data):
    counts, items = Counter(), []
    for f in data or []:
        counts["FINDING"] += 1
        items.append(f"{f['RuleID']} {f['File']}:{f['StartLine']}")   # never print the secret itself
    return counts, items


# (stage label, report file, parser, {policy key: counter key})
CHECKS = [
    ("SAST - Bandit", "bandit.json", "bandit", parse_bandit,
     {"max_high": "HIGH", "max_medium": "MEDIUM", "max_low": "LOW"}),
    ("SAST - Semgrep", "semgrep.json", "semgrep", parse_semgrep,
     {"max_high": "HIGH", "max_medium": "MEDIUM", "max_low": "LOW"}),
    ("SCA - pip-audit", "pip-audit.json", "pip_audit", None,
     {"max_vulns": "VULN"}),
    ("SCA - Trivy fs", "trivy-fs.json", "trivy_fs", parse_trivy,
     {"max_critical": "CRITICAL", "max_high": "HIGH",
      "max_critical_unfixed": "CRITICAL_UNFIXED", "max_high_unfixed": "HIGH_UNFIXED"}),
    ("Secret scan - gitleaks", "gitleaks.json", "gitleaks", parse_gitleaks,
     {"max_findings": "FINDING"}),
    ("Image scan - Trivy", "trivy-image.json", "trivy_image", parse_trivy,
     {"max_critical": "CRITICAL", "max_high": "HIGH",
      "max_critical_unfixed": "CRITICAL_UNFIXED", "max_high_unfixed": "HIGH_UNFIXED"}),
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
            data = load_json(path)
            if section == "pip_audit":
                counts, items = parse_pip_audit(data, set(cfg.get("ignore_ids", [])))
            else:
                counts, items = parser(data)
        except (ValueError, KeyError, TypeError) as exc:
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

    # ── console output ──
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
    print(f"\nSECURITY GATE: {'FAILED - image will NOT be pushed or deployed' if failed else 'PASSED'}")

    # ── GitHub job summary ──
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as fh:
            fh.write(f"## Security gate: {'FAILED' if failed else 'PASSED'}\n\n")
            fh.write("| Check | Verdict | Findings | Policy |\n|---|---|---|---|\n")
            for label, found, allowed, verdict in rows:
                fh.write(f"| {label} | {'❌' if verdict == 'FAIL' else '✅'} {verdict} | `{found}` | `{allowed}` |\n")

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
