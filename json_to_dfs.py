# -*- coding: utf-8 -*-
# Author: Yi Wang
# Compatibility wrapper for JSON input helpers.

from input_json import (
    DISCHARGE_QUANTITIES,
    clean_dataframe,
    load_json_data,
    normalize_combined,
    save_to_json,
    validate_combined,
)


if __name__ == "__main__":
    res1d_files_df, dfs, output_files, combined = load_json_data("res1d2excel_template.json")

    print("\n--- Combined Items ---")
    for c in combined:
        print(c)

    errors = validate_combined(dfs, combined)

    if errors:
        print("\nValidation Errors:")
        for e in errors:
            print(" -", e)
