#!/usr/bin/env python3
"""
Apulu Suite Quality Metrics Collector

Collects quality metrics from various tools and generates a unified JSON report.
Used by the Quality Team Coordinator Agent for tracking metrics over time.

Usage:
    python scripts/collect-quality-metrics.py [--output FILE] [--format json|md]
"""

import argparse
import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class QualityMetricsCollector:
    """Collects and aggregates quality metrics from various sources."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.reports_dir = project_root / "quality-reports"
        self.metrics: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "run_id": f"local-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            "git_ref": self._get_git_ref(),
            "metrics": {
                "quality_score": 0,
                "quality_grade": "F",
                "testing": {},
                "code_quality": {"backend": {}, "frontend": {}},
                "security": {},
                "documentation": {},
            },
            "agents": {},
            "findings": [],
            "action_items": [],
        }

    def _get_git_ref(self) -> dict[str, Any]:
        """Get current git reference information."""
        try:
            branch = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True,
                text=True,
                cwd=self.project_root,
            ).stdout.strip()

            commit = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                cwd=self.project_root,
            ).stdout.strip()

            return {"branch": branch, "commit": commit[:8], "tag": None}
        except Exception:
            return {"branch": "unknown", "commit": "unknown", "tag": None}

    def collect_coverage_metrics(self) -> None:
        """Collect test coverage metrics from coverage.xml."""
        coverage_file = self.reports_dir / "backend-coverage.xml"

        if coverage_file.exists():
            try:
                tree = ET.parse(coverage_file)
                root = tree.getroot()

                # Get overall coverage
                coverage_attr = root.get("line-rate")
                if coverage_attr:
                    coverage = float(coverage_attr) * 100

                    self.metrics["metrics"]["testing"]["backend_coverage"] = round(
                        coverage, 2
                    )

                    # Get lines
                    lines_valid = int(root.get("lines-valid", 0))
                    lines_covered = int(root.get("lines-covered", 0))

                    self.metrics["metrics"]["testing"]["backend_lines_total"] = (
                        lines_valid
                    )
                    self.metrics["metrics"]["testing"]["backend_lines_covered"] = (
                        lines_covered
                    )
            except Exception as e:
                print(f"Warning: Could not parse coverage.xml: {e}", file=sys.stderr)

    def collect_pytest_results(self) -> None:
        """Collect pytest results from JUnit XML."""
        pytest_file = self.reports_dir / "backend-pytest-results.xml"

        if pytest_file.exists():
            try:
                tree = ET.parse(pytest_file)
                root = tree.getroot()

                # Get test suite summary
                testsuite = root.find("testsuite")
                if testsuite is not None:
                    self.metrics["metrics"]["testing"]["total_tests"] = int(
                        testsuite.get("tests", 0)
                    )
                    self.metrics["metrics"]["testing"]["failed_tests"] = int(
                        testsuite.get("failures", 0)
                    ) + int(testsuite.get("errors", 0))
                    self.metrics["metrics"]["testing"]["skipped_tests"] = int(
                        testsuite.get("skipped", 0)
                    )
                    self.metrics["metrics"]["testing"]["passed_tests"] = (
                        self.metrics["metrics"]["testing"]["total_tests"]
                        - self.metrics["metrics"]["testing"]["failed_tests"]
                        - self.metrics["metrics"]["testing"]["skipped_tests"]
                    )
            except Exception as e:
                print(
                    f"Warning: Could not parse pytest results: {e}", file=sys.stderr
                )

    def collect_bandit_results(self) -> None:
        """Collect security scan results from Bandit."""
        bandit_file = self.reports_dir / "backend-bandit.txt"

        if bandit_file.exists():
            try:
                content = bandit_file.read_text()

                # Parse severity counts from the summary
                self.metrics["metrics"]["security"]["critical"] = content.count(
                    "Severity: High"
                )
                self.metrics["metrics"]["security"]["high"] = content.count(
                    "Severity: Medium"
                )
                self.metrics["metrics"]["security"]["medium"] = content.count(
                    "Severity: Low"
                )
                self.metrics["metrics"]["security"]["low"] = 0
            except Exception as e:
                print(f"Warning: Could not parse bandit results: {e}", file=sys.stderr)

    def collect_npm_audit_results(self) -> None:
        """Collect npm audit results."""
        npm_audit_file = self.reports_dir / "frontend-npm-audit.json"

        if npm_audit_file.exists():
            try:
                data = json.loads(npm_audit_file.read_text())
                vulnerabilities = data.get("metadata", {}).get("vulnerabilities", {})

                if "dependency_vulnerabilities" not in self.metrics["metrics"]["security"]:
                    self.metrics["metrics"]["security"]["dependency_vulnerabilities"] = {}

                self.metrics["metrics"]["security"]["dependency_vulnerabilities"][
                    "frontend"
                ] = (
                    vulnerabilities.get("critical", 0)
                    + vulnerabilities.get("high", 0)
                    + vulnerabilities.get("moderate", 0)
                    + vulnerabilities.get("low", 0)
                )
            except Exception as e:
                print(f"Warning: Could not parse npm audit: {e}", file=sys.stderr)

    def collect_pip_audit_results(self) -> None:
        """Collect pip-audit results."""
        pip_audit_file = self.reports_dir / "backend-pip-audit.json"

        if pip_audit_file.exists():
            try:
                data = json.loads(pip_audit_file.read_text())

                if "dependency_vulnerabilities" not in self.metrics["metrics"]["security"]:
                    self.metrics["metrics"]["security"]["dependency_vulnerabilities"] = {}

                self.metrics["metrics"]["security"]["dependency_vulnerabilities"][
                    "backend"
                ] = len(data) if isinstance(data, list) else 0
            except Exception as e:
                print(f"Warning: Could not parse pip-audit: {e}", file=sys.stderr)

    def calculate_quality_score(self) -> None:
        """Calculate overall quality score based on collected metrics."""
        testing = self.metrics["metrics"]["testing"]
        security = self.metrics["metrics"]["security"]

        # Testing score (25%)
        coverage = testing.get("backend_coverage", 0)
        test_pass_rate = (
            (
                testing.get("passed_tests", 0)
                / testing.get("total_tests", 1)
                * 100
            )
            if testing.get("total_tests", 0) > 0
            else 0
        )
        testing_score = (coverage * 0.6 + test_pass_rate * 0.4) * 0.25

        # Security score (30%)
        security_issues = (
            security.get("critical", 0) * 10
            + security.get("high", 0) * 5
            + security.get("medium", 0) * 2
            + security.get("low", 0) * 0.5
        )
        security_score = max(0, (100 - security_issues)) * 0.30

        # Code quality score (25%) - placeholder
        code_quality_score = 75 * 0.25  # Default to 75% if not measured

        # Documentation score (20%) - placeholder
        doc_score = 60 * 0.20  # Default to 60% if not measured

        total_score = testing_score + security_score + code_quality_score + doc_score
        self.metrics["metrics"]["quality_score"] = round(total_score, 1)

        # Determine grade
        score = self.metrics["metrics"]["quality_score"]
        if score >= 90:
            self.metrics["metrics"]["quality_grade"] = "A"
        elif score >= 85:
            self.metrics["metrics"]["quality_grade"] = "B+"
        elif score >= 80:
            self.metrics["metrics"]["quality_grade"] = "B"
        elif score >= 75:
            self.metrics["metrics"]["quality_grade"] = "C+"
        elif score >= 70:
            self.metrics["metrics"]["quality_grade"] = "C"
        elif score >= 60:
            self.metrics["metrics"]["quality_grade"] = "D"
        else:
            self.metrics["metrics"]["quality_grade"] = "F"

    def collect_all(self) -> dict[str, Any]:
        """Collect all available metrics."""
        print("Collecting quality metrics...")

        self.collect_coverage_metrics()
        self.collect_pytest_results()
        self.collect_bandit_results()
        self.collect_npm_audit_results()
        self.collect_pip_audit_results()
        self.calculate_quality_score()

        return self.metrics

    def save_metrics(self, output_path: Path) -> None:
        """Save metrics to JSON file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(self.metrics, indent=2))
        print(f"Metrics saved to: {output_path}")

    def generate_markdown_summary(self) -> str:
        """Generate a markdown summary of the metrics."""
        m = self.metrics["metrics"]

        summary = f"""# Quality Metrics Summary

**Generated**: {self.metrics['timestamp']}
**Run ID**: {self.metrics['run_id']}
**Git Branch**: {self.metrics['git_ref']['branch']}
**Commit**: {self.metrics['git_ref']['commit']}

## Overall Score

| Metric | Value |
|--------|-------|
| Quality Score | **{m['quality_score']}/100** |
| Quality Grade | **{m['quality_grade']}** |

## Testing

| Metric | Value |
|--------|-------|
| Backend Coverage | {m['testing'].get('backend_coverage', 'N/A')}% |
| Total Tests | {m['testing'].get('total_tests', 'N/A')} |
| Passed | {m['testing'].get('passed_tests', 'N/A')} |
| Failed | {m['testing'].get('failed_tests', 'N/A')} |
| Skipped | {m['testing'].get('skipped_tests', 'N/A')} |

## Security

| Severity | Count |
|----------|-------|
| Critical | {m['security'].get('critical', 0)} |
| High | {m['security'].get('high', 0)} |
| Medium | {m['security'].get('medium', 0)} |
| Low | {m['security'].get('low', 0)} |

### Dependency Vulnerabilities

| Source | Count |
|--------|-------|
| Backend (pip) | {m['security'].get('dependency_vulnerabilities', {}).get('backend', 'N/A')} |
| Frontend (npm) | {m['security'].get('dependency_vulnerabilities', {}).get('frontend', 'N/A')} |
"""
        return summary


def main():
    parser = argparse.ArgumentParser(
        description="Collect quality metrics for Apulu Suite"
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        help="Output file path (default: quality-reports/metrics-<timestamp>.json)",
    )
    parser.add_argument(
        "--format",
        "-f",
        choices=["json", "md", "both"],
        default="json",
        help="Output format (default: json)",
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path(__file__).parent.parent,
        help="Project root directory",
    )

    args = parser.parse_args()

    collector = QualityMetricsCollector(args.project_root)
    metrics = collector.collect_all()

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    reports_dir = args.project_root / "quality-reports"

    if args.format in ("json", "both"):
        output_path = args.output or reports_dir / f"metrics-{timestamp}.json"
        collector.save_metrics(output_path)

    if args.format in ("md", "both"):
        md_output = reports_dir / f"metrics-{timestamp}.md"
        md_output.write_text(collector.generate_markdown_summary())
        print(f"Markdown summary saved to: {md_output}")

    # Print summary
    print("\n" + "=" * 60)
    print(f"Quality Score: {metrics['metrics']['quality_score']}/100")
    print(f"Quality Grade: {metrics['metrics']['quality_grade']}")
    print("=" * 60)


if __name__ == "__main__":
    main()
