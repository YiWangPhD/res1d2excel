"""Canonical specification helpers for the GUI editor."""

from __future__ import annotations

import copy
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from . import input_dataframes
from . import input_json
from . import input_xlsx


ELEMENT_TYPES = [
    "catchment",
    "node",
    "link",
    "orifice",
    "pump",
    "regulation",
    "weir",
    "valve",
    "bridge",
    "direct_discharge",
    "gate",
]

COMBINED_SOURCES = ELEMENT_TYPES

ELEMENT_SCHEMAS = {
    "catchment": ["alias", "quantity", "muid"],
    "node": ["alias", "quantity", "muid"],
    "link": ["alias", "quantity", "muid", "chainage"],
    "orifice": ["alias", "quantity", "muid"],
    "pump": ["alias", "quantity", "muid"],
    "regulation": ["alias", "quantity", "muid", "chainage"],
    "weir": ["alias", "quantity", "muid"],
    "valve": ["alias", "quantity", "muid"],
    "bridge": ["alias", "quantity", "muid"],
    "direct_discharge": ["alias", "quantity", "muid"],
    "gate": ["alias", "quantity", "muid"],
    "res1d_files": ["result_type", "short_name", "res1d_file_path"],
}

OUTPUT_DEFAULTS = {
    "output_folder": os.getcwd(),
    "resample_interval": None,
    "skip_time": None,
    "trunc_time": None,
    "to_html": False,
    "export_by_element": False,
    "export_by_result_file": False,
    "export_statistics": False,
}


def empty_spec() -> dict[str, Any]:
    spec: dict[str, Any] = {name: [] for name in ELEMENT_TYPES}
    spec["combined"] = []
    spec["output_files"] = copy.deepcopy(OUTPUT_DEFAULTS)
    spec["res1d_files"] = []
    return spec


def normalize_spec(spec: dict[str, Any] | None) -> dict[str, Any]:
    normalized = empty_spec()
    if not spec:
        return normalized

    for name in ELEMENT_TYPES:
        rows = spec.get(name, [])
        normalized[name] = _normalize_records(rows, ELEMENT_SCHEMAS[name])

    normalized["res1d_files"] = _normalize_records(
        spec.get("res1d_files", []),
        ELEMENT_SCHEMAS["res1d_files"],
    )

    output = copy.deepcopy(OUTPUT_DEFAULTS)
    if isinstance(spec.get("output_files"), dict):
        output.update(spec["output_files"])
    output["to_html"] = input_dataframes.parse_bool(output.get("to_html", False))
    output["export_by_element"] = input_dataframes.parse_bool(
        output.get("export_by_element", output.get("by_elements", False))
    )
    output["export_by_result_file"] = input_dataframes.parse_bool(
        output.get("export_by_result_file", output.get("by_file", False))
    )
    output["export_statistics"] = input_dataframes.parse_bool(
        output.get("export_statistics", output.get("stats", False))
    )
    normalized["output_files"] = output

    combined = spec.get("combined", [])
    normalized["combined"] = input_json.normalize_combined(combined) if isinstance(combined, list) else []
    return normalized


def load_spec(path: str | Path) -> dict[str, Any]:
    source = Path(path)
    suffix = source.suffix.lower()
    if suffix == ".json":
        with source.open("r", encoding="utf-8") as handle:
            return normalize_spec(json.load(handle))
    if suffix == ".xlsx":
        return normalize_spec(load_spec_from_xlsx(source))
    raise ValueError(f"Unsupported specification file: {source}")


def load_spec_from_xlsx(path: str | Path) -> dict[str, Any]:
    dfs_list = input_xlsx.read_dataframes_from_xlsx(path)
    res1d_file_dfs, element_dfs, output_dfs, combined = dfs_list

    spec: dict[str, Any] = {}
    for name in ELEMENT_TYPES:
        df = element_dfs.get(name, pd.DataFrame(columns=ELEMENT_SCHEMAS[name]))
        spec[name] = _dataframe_to_records(df)

    res1d_df = res1d_file_dfs.get("res1d_files", pd.DataFrame(columns=ELEMENT_SCHEMAS["res1d_files"]))
    spec["res1d_files"] = _dataframe_to_records(res1d_df)

    output_df = output_dfs.get("output_files", pd.DataFrame(columns=["type", "value"]))
    spec["output_files"] = input_json._output_files_dataframe_to_json(output_df)
    spec["combined"] = combined
    return spec


def save_spec_to_json(spec: dict[str, Any], path: str | Path) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as handle:
        json.dump(normalize_spec(spec), handle, indent=2, allow_nan=False)
    return target


def timestamped_json_path(source_path: str | Path | None) -> Path:
    stamp = datetime.now().strftime("%Y%m%d%H%M%S")
    if source_path:
        source = Path(source_path)
        folder = source.parent if source.parent != Path("") else Path.cwd()
        stem = source.stem
    else:
        folder = Path.cwd()
        stem = "res1d2excel_spec"
    return folder / f"{stem}_{stamp}.json"


def validate_spec(spec: dict[str, Any]) -> list[str]:
    spec = normalize_spec(spec)
    errors: list[str] = []

    output = spec["output_files"]
    if not output.get("output_folder"):
        errors.append("Output folder is required.")
    elif not Path(str(output["output_folder"])).exists():
        errors.append(f"Output folder does not exist: {output['output_folder']}")

    if not any(
        output.get(key)
        for key in ["export_by_element", "export_by_result_file", "export_statistics", "to_html"]
    ):
        errors.append("Select at least one output option.")

    seen_short_names: set[tuple[str, str]] = set()
    for index, row in enumerate(spec["res1d_files"], start=1):
        result_type = str(row.get("result_type") or "").strip()
        short_name = str(row.get("short_name") or "").strip()
        file_path = str(row.get("res1d_file_path") or "").strip()

        if not result_type or not short_name or not file_path:
            errors.append(f"Result file row {index} must include result_type, short_name, and file path.")
            continue

        key = (result_type, short_name)
        if key in seen_short_names:
            errors.append(f"Duplicate result short name for {result_type}: {short_name}")
        seen_short_names.add(key)

        if not Path(file_path).exists():
            errors.append(f"Result file does not exist: {file_path}")

    alias_lookup = {
        source: {str(row.get("alias")) for row in spec[source] if row.get("alias")}
        for source in COMBINED_SOURCES
    }
    combined_aliases: set[str] = set()
    for index, item in enumerate(spec["combined"], start=1):
        combined_alias = str(item.get("alias") or "").strip()
        if not combined_alias:
            errors.append(f"Combined item {index} must have an alias.")
        elif combined_alias in combined_aliases:
            errors.append(f"Duplicate combined alias: {combined_alias}")
        combined_aliases.add(combined_alias)

        for term in item.get("terms", []):
            source = term.get("source")
            alias = term.get("alias")
            if source not in alias_lookup:
                errors.append(f"Combined term has invalid source: {source}")
            elif alias not in alias_lookup[source]:
                errors.append(f"Combined term references missing alias: {source}.{alias}")

    # Element aliases are optional. They are only required indirectly when a
    # combined item needs to reference a source element by alias.
    for name in ELEMENT_TYPES:
        required = ["quantity", "muid"]
        for index, row in enumerate(spec[name], start=1):
            if any(row.get(col) not in (None, "") for col in ELEMENT_SCHEMAS[name]):
                missing = [col for col in required if row.get(col) in (None, "")]
                if missing:
                    errors.append(f"{name} row {index} missing: {', '.join(missing)}")

    return errors


def _normalize_records(rows: Any, columns: list[str]) -> list[dict[str, Any]]:
    if not isinstance(rows, list):
        return []
    normalized = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        item = {column: _clean_value(row.get(column)) for column in columns}
        if "res1d_file_path" in item and not item["res1d_file_path"]:
            item["res1d_file_path"] = _clean_value(row.get("file_path"))
        if any(value not in (None, "") for value in item.values()):
            normalized.append(item)
    return normalized


def _dataframe_to_records(df: pd.DataFrame) -> list[dict[str, Any]]:
    return [
        {key: _clean_value(value) for key, value in row.items()}
        for row in df.astype(object).where(pd.notnull(df), None).to_dict(orient="records")
    ]


def _clean_value(value: Any) -> Any:
    if pd.isna(value):
        return None
    return value
