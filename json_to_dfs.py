import json
import pandas as pd

DISCHARGE_QUANTITIES = ['Discharge', 'DischargeInStructure', 'OverlandFlow', 
                        'InterFlow', 'BaseFlow', 'LowerBaseFlow', 
                        'InfiltrationToGroundWater', 'TotalInflow', 
                        'TotalOutflow', 'TotalRunOff']

def load_json_data(json_path):
    """
    Load JSON and split into:
    1. dfs (dict of DataFrames)
    2. output_files (dict)
    3. res1d_files_df (DataFrame)
    4. combined (list of structured items)
    """

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    dfs = {}
    output_files = {}
    res1d_files_df = pd.DataFrame()
    combined = []

    for key, value in data.items():

        # ✅ OUTPUT FILES (config)
        if key == "output_files":
            output_files = value

        # ✅ RES1D FILES (table)
        elif key == "res1d_files":
            res1d_files_df = pd.DataFrame(value)
            res1d_files_df = clean_dataframe(res1d_files_df)

        # ✅ COMBINED ITEMS (NEW)
        elif key == "combined":
            combined = normalize_combined(value)

        # ✅ STANDARD TABLES → dfs
        else:
            if isinstance(value, list):
                df = pd.DataFrame(value)
                dfs[key] = clean_dataframe(df)
            else:
                dfs[key] = pd.DataFrame()

    return dfs, output_files, res1d_files_df, combined


# ✅ ✅ ✅ CLEAN DATAFRAME
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


# ✅ ✅ ✅ NORMALIZE COMBINED STRUCTURE
def normalize_combined(combined_list):
    """
    Ensure combined items follow expected structure
    """

    normalized = []

    for item in combined_list:

        new_item = {
            "alias": item.get("alias", ""),
            "quantity": "Discharge",  # enforce rule
            "terms": []
        }

        terms = item.get("terms", [])

        for t in terms:
            new_item["terms"].append({
                "op": t.get("op", "+"),
                "source": t.get("source", "node"),
                "alias": t.get("alias", "")
            })

        normalized.append(new_item)

    return normalized


# ✅ ✅ ✅ SAVE BACK TO JSON
def save_to_json(dfs, output_files, res1d_files_df, combined, json_path):
    data = {}

    # dfs tables
    for name, df in dfs.items():
        data[name] = df.where(pd.notnull(df), None).to_dict(orient="records")

    # config
    data["output_files"] = output_files

    # res1d files
    data["res1d_files"] = res1d_files_df.where(
        pd.notnull(res1d_files_df), None
    ).to_dict(orient="records")

    # combined items
    data["combined"] = combined

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


# ✅ ✅ ✅ OPTIONAL VALIDATION
def validate_combined(dfs, combined):
    """
    Validate:
    - referenced alias exists
    - quantity must be Discharge
    """

    errors = []

    # build lookup of aliases
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


# ✅ ✅ ✅ EXAMPLE USAGE
if __name__ == "__main__":

    dfs, output_files, res1d_files_df, combined = load_json_data("res1d2excel_template.json")

    print("\n--- Combined Items ---")
    for c in combined:
        print(c)

    # ✅ validate
    errors = validate_combined(dfs, combined)

    if errors:
        print("\nValidation Errors:")
        for e in errors:
            print(" -", e)
