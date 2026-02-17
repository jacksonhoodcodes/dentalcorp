# Dentalcorp Template Autofill Automation

Python CLI to populate a locked Excel template from deal package PDFs and validate against a final reference workbook.

## Files

- `parse_blank_vs_final.py`: identifies manual input cells by diffing blank vs final workbooks.
- `extract_fs.py`: parses financial statement PDF into canonical income statement categories.
- `extract_eval.py`: parses evaluation report PDF for production, provider split, and payroll details.
- `mapper.py`: maps extracted canonical values into manual input cells in the template.
- `fill_template.py`: orchestration wrapper around mapping and write operations.
- `validate.py`: validates generated output against final workbook on manual input cells only.
- `main.py`: CLI entrypoint to run end-to-end.

## Run

```bash
python main.py \
  --template_blank template_blank.xlsx \
  --template_final template_final.xlsx \
  --fs_pdf fs.pdf \
  --eval_pdf eval_report.pdf \
  --out output_filled.xlsx \
  --audit run_audit.csv \
  --validation validation_report.csv \
  --manual_input_map manual_input_map.csv \
  --deal_id kamloops_sample
```

## Notes

- Template structure is preserved; only detected manual input cells are considered for writes.
- Missing/ambiguous values remain blank and are logged in audit output.
- EN/FR normalization is supported through text normalization and synonym dictionaries.
