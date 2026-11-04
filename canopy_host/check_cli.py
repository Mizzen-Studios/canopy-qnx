"""Explicit host budget CLI; never infers missing evidence."""
import argparse
from pathlib import Path
from .check import (load_budgets, load_evidence, check, render_rustc,
                    render_github_annotations, render_github_summary)

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("evidence", help="explicit HOST SIM/HOST VCAN evidence JSON")
    parser.add_argument("--budgets", default="budgets.yaml")
    parser.add_argument("--github", action="store_true", help="emit failure annotations")
    parser.add_argument("--summary", help="append host-only Markdown summary to this file")
    args = parser.parse_args(argv)
    try:
        report = check(load_budgets(args.budgets), load_evidence(args.evidence))
        print(render_rustc(report), end="")
        if args.github:
            annotations = render_github_annotations(report)
            if annotations:
                print(annotations)
        if args.summary:
            with Path(args.summary).open("a", encoding="utf-8") as stream:
                stream.write(render_github_summary(report))
    except (OSError, ValueError) as error:
        parser.error(str(error))
    return report.exit_code
