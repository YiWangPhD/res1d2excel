# -*- coding: utf-8 -*-
# Author: Yi Wang
# this module build input dataframes using input json files

import json
import os

import pandas as pd

import input_dataframes


DISCHARGE_QUANTITIES = ['Discharge', 'DischargeInStructure', 'OverlandFlow',
                        'InterFlow', 'BaseFlow', 'LowerBaseFlow',
                        'InfiltrationToGroundWater', 'TotalInflow',
                        'TotalOutflow', 'TotalRunOff']


def load_json_data(json_path):
    """
    Load JSON and split into:
    1. res1d_files_df (DataFrame)
    2. dfs (dict of DataFrames)
    3. output_files (dict)
    4. combined (list of structured items)
    """

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    dfs = {}
    output_files = {}
    res1d_files_df = pd.DataFrame()
    combined = []

    for key, value in data.items():
        if key == "output_files":
            output_files = value
        elif key == "res1d_files":
            res1d_files_df = clean_dataframe(pd.DataFrame(value))
        elif key == "combined":
            combined = normalize_combined(value)
        elif isinstance(value, list):
            dfs[key] = clean_dataframe(pd.DataFrame(value))
        else:
            dfs[key] = pd.DataFrame()

    return res1d_files_df, dfs, output_files, combined


def clean_dataframe(df):
    if df.empty:
        return df

    df = df.replace("", pd.NA)

    for col in df.columns:
        try:
            converted = pd.to_numeric(df[col])
            if not converted.isna().all():
                df[col] = converted
        except (ValueError, TypeError):
            pass

    return df


def normalize_combined(combined_list):
    normalized = []

    for item in combined_list:
        new_item = {
            "alias": item.get("alias", ""),
            "quantity": "CalculatedDischarge",
            "terms": []
        }

        terms = item.get("terms", [])

        for term in terms:
            new_item["terms"].append({
                "op": term.get("op", "+"),
                "source": term.get("source", "node"),
                "alias": term.get("alias", "")
            })

        normalized.append(new_item)

    return normalized


def save_to_json(dfs, output_files, res1d_files_df, combined, json_path):
    data = {}

    for name, df in dfs.items():
        data[name] = _dataframe_to_records(df)

    data["output_files"] = output_files
    data["res1d_files"] = _dataframe_to_records(res1d_files_df)
    data["combined"] = combined

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, allow_nan=False)


def validate_combined(dfs, combined):
    errors = []

    lookup = {}
    for name, df in dfs.items():
        if "alias" in df.columns and "quantity" in df.columns:
            lookup[name] = dict(zip(df["alias"], df["quantity"]))

    for item in combined:
        for term in item["terms"]:
            src = term["source"]
            alias = term["alias"]

            if src not in lookup:
                errors.append(f"Invalid source: {src}")
                continue

            if alias not in lookup[src]:
                errors.append(f"Alias not found: {src}.{alias}")
                continue

            if lookup[src][alias] not in DISCHARGE_QUANTITIES:
                errors.append(f"{src}.{alias} is not Discharge")

    return errors


def _dataframe_to_records(df):
    return df.astype(object).where(pd.notnull(df), None).to_dict(orient="records")


def _output_files_dataframe_to_json(output_files_df):
    output_files = dict(zip(output_files_df["type"], output_files_df["value"]))

    return {
        "output_folder": output_files.get("folder_path", os.getcwd()),
        "resample_interval": output_files.get("resample_t"),
        "skip_time": output_files.get("skip_time"),
        "trunc_time": output_files.get("trunc_time"),
        "export_by_element": "by_elements" in output_files,
        "export_by_result_file": "by_file" in output_files,
        "export_statistics": "stats" in output_files,
    }


def _output_files_json_to_dataframe(output_files):
    if isinstance(output_files, pd.DataFrame):
        return {"output_files": output_files}

    if isinstance(output_files, list):
        return {"output_files": pd.DataFrame(output_files)}

    folder_path = output_files.get(
        "folder_path",
        output_files.get("output_folder", os.getcwd())
    )
    rows = [{"type": "folder_path", "value": folder_path}]

    resample_t = output_files.get(
        "resample_t",
        output_files.get("resample_interval")
    )
    if resample_t:
        rows.append({"type": "resample_t", "value": resample_t})

    skip_time = output_files.get("skip_time")
    if skip_time:
        rows.append({"type": "skip_time", "value": skip_time})

    trunc_time = output_files.get("trunc_time")
    if trunc_time:
        rows.append({"type": "trunc_time", "value": trunc_time})

    if output_files.get("by_elements"):
        rows.append({"type": "by_elements", "value": output_files["by_elements"]})
    elif output_files.get("export_by_element"):
        rows.append({"type": "by_elements", "value": "by_element.xlsx"})

    if output_files.get("by_file"):
        rows.append({"type": "by_file", "value": output_files["by_file"]})
    elif output_files.get("export_by_result_file"):
        rows.append({"type": "by_file", "value": "by_file.xlsx"})

    if output_files.get("stats"):
        rows.append({"type": "stats", "value": output_files["stats"]})
    elif output_files.get("export_statistics"):
        rows.append({"type": "stats", "value": "stats.xlsx"})

    return {"output_files": pd.DataFrame(rows)}


def write_dataframes_to_json(json_file_path, dfs, combined=None):
    data = {}
    combined_from_dataframe = None

    for name, df in dfs.items():
        if name == "output_files":
            data[name] = _output_files_dataframe_to_json(df)
        elif name == "combined":
            combined_from_dataframe = input_dataframes.create_combined_from_dataframe(df)
        else:
            data[name] = _dataframe_to_records(df)

    if combined is not None:
        data["combined"] = combined
    elif combined_from_dataframe is not None:
        data["combined"] = combined_from_dataframe
    else:
        data["combined"] = []

    with open(json_file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, allow_nan=False)


def create_template_json(json_file_path):
    dfs = input_dataframes.create_element_collections_dataframes_template()
    dfs = dfs | input_dataframes.create_res1d_files_dataframe_template()
    dfs = dfs | input_dataframes.create_output_files_dataframe_template()
    dfs = dfs | input_dataframes.create_combined_dataframe_template()
    write_dataframes_to_json(json_file_path, dfs)


def read_dataframes_from_json(json_file_path):
    res1d_files_df, element_collections_dfs, output_files, combined = load_json_data(json_file_path)

    if "file_path" in res1d_files_df.columns:
        res1d_files_df = res1d_files_df.rename(columns={"file_path": "res1d_file_path"})

    res1d_file_dfs = {"res1d_files": res1d_files_df}
    output_files_dfs = _output_files_json_to_dataframe(output_files)

    return [res1d_file_dfs, element_collections_dfs, output_files_dfs, combined]


def main():
    json_file_path = os.path.join(os.getcwd(), "res1d2excel_template.json")
    create_template_json(json_file_path)
    dfs_list = read_dataframes_from_json(json_file_path)
    print(dfs_list[0])


if __name__ == "__main__":
    main()
