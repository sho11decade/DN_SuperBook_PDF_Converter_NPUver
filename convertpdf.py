#!/usr/bin/env python3
import argparse
import importlib.util
import json
import logging
import shutil
import sys
from pathlib import Path

LOG = logging.getLogger("convertpdf")


def detect_backend() -> str:
    try:
        if importlib.util.find_spec("openvino") or importlib.util.find_spec("openvino.runtime"):
            return "NPU"
    except ModuleNotFoundError:
        return "CPU"
    return "CPU"


def load_config(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".yaml", ".yml"}:
        try:
            import yaml
        except ImportError as exc:
            raise RuntimeError("PyYAML is not installed; cannot read YAML config.") from exc
        return yaml.safe_load(text) or {}
    return json.loads(text) or {}


def collect_pdfs(inputs: list[str], recursive: bool) -> list[tuple[Path, Path]]:
    collected: list[tuple[Path, Path]] = []
    for raw in inputs:
        path = Path(raw)
        if not path.exists():
            LOG.error("Input not found: %s", path)
            continue
        if path.is_dir():
            pattern = "**/*" if recursive else "*"
            found = False
            for candidate in path.glob(pattern):
                if candidate.is_file() and candidate.suffix.lower() == ".pdf":
                    collected.append((candidate, path))
                    found = True
            if not found:
                LOG.warning("No PDF files found in %s", path)
        else:
            if path.suffix.lower() != ".pdf":
                LOG.warning("Skipping non-PDF input: %s", path)
                continue
            collected.append((path, path.parent))
    return collected


def write_ocr_placeholders(output_pdf: Path, source_pdf: Path) -> None:
    ocr_pdf = output_pdf.with_name(f"{output_pdf.stem}.ocr.pdf")
    shutil.copy2(output_pdf, ocr_pdf)

    html_path = output_pdf.with_suffix(".html")
    md_path = output_pdf.with_suffix(".md")
    json_path = output_pdf.with_suffix(".json")

    html_path.write_text(
        f"<html><body><h1>OCR placeholder</h1><p>Source: {source_pdf}</p></body></html>\n",
        encoding="utf-8",
    )
    md_path.write_text(
        f"# OCR placeholder\n\nSource: {source_pdf}\n",
        encoding="utf-8",
    )
    json_path.write_text(
        json.dumps({"source": str(source_pdf), "status": "placeholder"}, ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
    )


def merge_setting(cli_value, config, key, default):
    if cli_value is not None:
        return cli_value
    return config.get(key, default)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="convertpdf",
        description="Minimal PDF converter skeleton (NPU/CPU placeholder)",
    )
    parser.add_argument("inputs", nargs="+", help="PDF files or directories")
    parser.add_argument("-o", "--output-dir", default=None, help="Output directory")
    parser.add_argument("-r", "--recursive", action="store_true", default=None, help="Recurse into directories")
    parser.add_argument("--ocr", action="store_true", default=None, help="Emit OCR placeholder outputs")
    parser.add_argument("--config", help="Config file (JSON/YAML)")
    return parser.parse_args()


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    args = parse_args()

    config: dict = {}
    if args.config:
        try:
            config = load_config(Path(args.config))
        except Exception as exc:
            LOG.error("Failed to load config: %s", exc)
            return 1

    output_dir = Path(merge_setting(args.output_dir, config, "output_dir", "output"))
    recursive = bool(merge_setting(args.recursive, config, "recursive", False))
    ocr = bool(merge_setting(args.ocr, config, "ocr", False))

    backend = detect_backend()
    if backend == "NPU":
        LOG.info("OpenVINO detected; using NPU backend (placeholder).")
    else:
        LOG.warning("OpenVINO not detected; using CPU fallback.")

    pdfs = collect_pdfs(args.inputs, recursive)
    if not pdfs:
        LOG.error("No PDF inputs to process.")
        return 1

    for pdf_path, base_dir in pdfs:
        relative = pdf_path.relative_to(base_dir)
        output_path = output_dir / relative
        output_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(pdf_path, output_path)
        LOG.info("Wrote PDF: %s", output_path)

        if ocr:
            write_ocr_placeholders(output_path, pdf_path)
            LOG.info("Wrote OCR placeholders for: %s", output_path)

    return 0


if __name__ == "__main__":
    sys.exit(main())
