from __future__ import annotations

from extract_eval import EvalExtractionResult
from extract_fs import FSExtractionResult
from mapper import MappingResult, map_and_fill
from parse_blank_vs_final import ManualInputCell


def fill_template(
    template_blank_path: str,
    output_path: str,
    manual_inputs: list[ManualInputCell],
    fs_result: FSExtractionResult,
    eval_result: EvalExtractionResult,
    deal_id: str,
    timestamp: str,
) -> MappingResult:
    return map_and_fill(
        template_blank_path=template_blank_path,
        output_path=output_path,
        manual_inputs=manual_inputs,
        fs=fs_result,
        ev=eval_result,
        deal_id=deal_id,
        timestamp=timestamp,
    )
