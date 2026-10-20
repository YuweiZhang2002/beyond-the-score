"""Bundle public records for the standalone interactive evidence page."""
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
names = ("report.json", "rbm-cases.json", "robofail-cases.json", "robofail-visibility.json")
records = [json.loads((root / "data" / name).read_text()) for name in names]
(root / "data.js").write_text(
    "// Generated from public JSON by scripts/build_evidence_data.py.\nwindow.REPORT_DATA = "
    + json.dumps(records, ensure_ascii=False, separators=(",", ":")) + ";\n"
)
