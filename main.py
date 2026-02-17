from __future__ import annotations

import argparse
import os

import pandas as pd

from extract_eval import EvalExtractionResult, extract_evaluation
from extract_fs import FSExtractionResult, extract_financial_statement
from fill_template import fill_template
from parse_blank_vs_final import identify_manual_input_cells, manual_inputs_to_df
from utils import now_iso
from validate import validate_output


def _empty_fs() -> FSExtractionResult:
    return FSExtractionResult(
        income_statement=pd.DataFrame(
            columns=["line_item", "canonical_line_item", "amount_year_1", "amount_year_2"]
        ),
        metadata={"status": "missing_input"},
    )


def _empty_eval() -> EvalExtractionResult:
    return EvalExtractionResult(
        production=pd.DataFrame(columns=["month", "gross_revenue"]),
        provider_split=pd.DataFrame(columns=["provider_type", "percent"]),
        payroll=pd.DataFrame(columns=["role", "hourly_rate", "days_per_week", "inferred_hours_per_week"]),
        metadata={"status": "missing_input"},
    )


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Fill locked Excel template from deal package docs.")
    p.add_argument("--template_blank", required=True)
    p.add_argument("--template_final", required=True)
    p.add_argument("--fs_pdf", default="")
    p.add_argument("--eval_pdf", default="")
    p.add_argument("--out", required=True)
    p.add_argument("--audit", required=True)
    p.add_argument("--validation", required=True)
    p.add_argument("--manual_input_map", default="manual_input_map.csv")
    p.add_argument("--deal_id", default="unknown_deal")
    return p


def main() -> int:
    args = build_arg_parser().parse_args()
    ts = now_iso()

    manual_inputs = identify_manual_input_cells(args.template_blank, args.template_final)
    manual_df = manual_inputs_to_df(manual_inputs)
    manual_df.to_csv(args.manual_input_map, index=False)

    has_fs = bool(args.fs_pdf) and os.path.exists(args.fs_pdf)
    has_eval = bool(args.eval_pdf) and os.path.exists(args.eval_pdf)

    fs_result = extract_financial_statement(args.fs_pdf) if has_fs else _empty_fs()
    eval_result = extract_evaluation(args.eval_pdf) if has_eval else _empty_eval()

    mapping_result = fill_template(
        template_blank_path=args.template_blank,
        output_path=args.out,
        manual_inputs=manual_inputs,
        fs_result=fs_result,
        eval_result=eval_result,
        deal_id=args.deal_id,
        timestamp=ts,
    )

    audit_df = pd.DataFrame([r.__dict__ for r in mapping_result.audit_rows])
    audit_df.to_csv(args.audit, index=False)

    validation_df, summary = validate_output(args.out, args.template_final, manual_inputs)
    validation_df.to_csv(args.validation, index=False)

    fs_received = "yes" if has_fs else "no"
    production_received = "yes" if has_eval else "no"
    payroll_received = "yes" if has_eval else "no"

    print("=== Deal package status ===")
    print(f"Deal ID: {args.deal_id}")
    print(f"FS received: {fs_received}")
    print(f"Production received: {production_received}")
    print(f"Payroll received: {payroll_received}")
    print(f"Fields filled: {len(mapping_result.writes)}/{len(manual_inputs)}")
    print(f"Fields missing: {len(mapping_result.missing)}")

    print("\n=== Validation summary ===")
    print(f"Manual input cells: {summary.total}")
    print(f"Matched: {summary.matched}")
    print(f"Mismatched: {summary.mismatched}")
    print(f"Match %: {summary.matched_pct:.2f}")

    if not validation_df.empty:
        top = validation_df[~validation_df["match"]].head(20)
        if not top.empty:
            print("\nTop mismatches (up to 20):")
            print(top.to_string(index=False))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
