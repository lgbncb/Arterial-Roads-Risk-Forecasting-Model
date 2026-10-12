"""Annual PCU-demand scenarios for the supplied Metro Manila road dataset."""

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

CLASSES = ("Car", "PUJ", "UV", "Taxi", "PUB", "Truck", "Trailer", "MC", "Tricycle")
FEATURES = ["Road_PCU_Volume", "Capacity_Limit", "Year", "Road_Type"] + [f"Share_{c}" for c in CLASSES]
RISK_ORDER = ["Low", "Medium", "High"]
RING_ROADS = ("C-4_EDSA", "C-5_CP_Garcia")


def risk_from_ratio(ratio):
    values = np.asarray(ratio, dtype=float)
    labels = np.select([values >= 0.95, values >= 0.70], ["High", "Medium"], default="Low")
    return str(labels.item()) if labels.ndim == 0 else labels


def validate_data(df):
    required = {"Year", "Road_ID_Name", "Road_Type", "Capacity_Limit_PCU_Per_Day", "Road_PCU_Volume_Per_Day"}
    required |= set(CLASSES) | {f"PCEF_{c}" for c in CLASSES}
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f"Missing columns: {missing}")
    data = df.copy()
    numeric = list(CLASSES) + [f"PCEF_{c}" for c in CLASSES] + ["Year", "Capacity_Limit_PCU_Per_Day", "Road_PCU_Volume_Per_Day"]
    for col in numeric:
        data[col] = pd.to_numeric(data[col], errors="raise")
    if data[numeric].isna().any().any():
        raise ValueError("Missing numeric values")
    if data.duplicated(["Road_ID_Name", "Year"]).any():
        raise ValueError("Duplicate road-year rows")
    if len(data) != 120 or data.Road_ID_Name.nunique() != 20 or set(data.Year) != set(range(2020, 2026)):
        raise ValueError("Expected 20 roads for every year 2020–2025")
    if data.groupby("Road_ID_Name").Year.nunique().ne(6).any():
        raise ValueError("A road is missing a historical year")
    if (data["Capacity_Limit_PCU_Per_Day"] <= 0).any() or (data[list(CLASSES)] < 0).any().any():
        raise ValueError("Capacity must be positive and counts nonnegative")
    return data.sort_values(["Road_ID_Name", "Year"]).reset_index(drop=True)


def add_pcu_and_risk(df):
    data = df.copy()
    data["Road_PCU_Volume"] = sum(data[c] * data[f"PCEF_{c}"] for c in CLASSES)
    data["Capacity_Limit"] = data["Capacity_Limit_PCU_Per_Day"]
    data["PCU_Difference"] = data["Road_PCU_Volume"] - data["Road_PCU_Volume_Per_Day"]
    raw_total = data[list(CLASSES)].sum(axis=1)
    for c in CLASSES:
        data[f"Share_{c}"] = np.where(raw_total > 0, data[c] / raw_total, 0.0)
    data["VC_Ratio"] = data["Road_PCU_Volume"] / data["Capacity_Limit"]
    data["Rule_Risk_Level"] = risk_from_ratio(data["VC_Ratio"])
    return data


def make_features(df):
    return df[FEATURES]


def fit_and_evaluate(history):
    train = history[history.Year <= 2023]
    test = history[history.Year >= 2024]
    prep = ColumnTransformer([
        ("road_type", OneHotEncoder(handle_unknown="ignore"), ["Road_Type"]),
        ("numeric", "passthrough", [c for c in FEATURES if c != "Road_Type"]),
    ])
    model = Pipeline([("features", prep), ("forest", RandomForestClassifier(n_estimators=300, max_depth=8, min_samples_leaf=2, random_state=42, class_weight="balanced"))])
    model.fit(make_features(train), train.Rule_Risk_Level)
    pred = model.predict(make_features(test))
    report = classification_report(test.Rule_Risk_Level, pred, labels=RISK_ORDER, output_dict=True, zero_division=0)
    metrics = pd.DataFrame(report).T
    matrix = pd.DataFrame(confusion_matrix(test.Rule_Risk_Level, pred, labels=RISK_ORDER), index=RISK_ORDER, columns=RISK_ORDER)
    comparison = test[["Year", "Road_ID_Name", "Road_Type", "VC_Ratio", "Rule_Risk_Level"]].copy()
    comparison["RF_Risk_Level"] = pred
    comparison["Disagreement"] = comparison.Rule_Risk_Level.ne(comparison.RF_Risk_Level)
    return model, metrics, matrix, comparison


def simulate(history, model, name, growth_rate=0.045, transfer_share=0.0, capacity_increase=0.0, expansion_year=2028):
    """Transfer share moves car *people* to buses: one new bus per 40 shifted cars."""
    if not 0 <= transfer_share <= 1 or growth_rate < -1 or capacity_increase < 0:
        raise ValueError("Invalid scenario parameters")
    baseline = history.loc[history.Year == 2025].copy()
    output = []
    for year in range(2025, 2036):
        state = baseline.copy()
        state["Year"] = year
        factor = (1 + growth_rate) ** (year - 2025)
        for c in CLASSES:
            state[c] = baseline[c].to_numpy(dtype=float) * factor
        if year > 2025 and transfer_share:
            shifted_cars = state.Car * transfer_share
            state["Car"] -= shifted_cars
            state["PUB"] += shifted_cars / 40.0
        state["Capacity_Limit_PCU_Per_Day"] = baseline.Capacity_Limit.to_numpy(dtype=float)
        if year >= expansion_year and capacity_increase:
            mask = state.Road_ID_Name.isin(RING_ROADS)
            state.loc[mask, "Capacity_Limit_PCU_Per_Day"] *= 1 + capacity_increase
        state = add_pcu_and_risk(state)
        state["RF_Risk_Level"] = model.predict(make_features(state))
        state["Risk_Level"] = state["Rule_Risk_Level"]
        state["RF_Disagreement"] = state.RF_Risk_Level.ne(state.Risk_Level)
        state["Scenario"] = name
        state["Capacity_Basis"] = "Synthetic scenario, not measured"
        output.append(state)
    result = pd.concat(output, ignore_index=True)
    first_high = result.loc[result.Risk_Level.eq("High")].groupby("Road_ID_Name").Year.min()
    result["First_High_Year"] = result.Road_ID_Name.map(first_high).astype("Int64")
    return result


def save_outputs(results, directory):
    folder = Path(directory)
    folder.mkdir(parents=True, exist_ok=True)
    cols = ["Scenario", "Year", "Road_ID_Name", "Road_Type", "Road_PCU_Volume", "Capacity_Limit", "VC_Ratio", "Risk_Level", "RF_Risk_Level", "RF_Disagreement", "First_High_Year", "Capacity_Basis"]
    results[cols].to_csv(folder / "road_year_forecast.csv", index=False)
    results.loc[results.Year.eq(2035), ["Scenario", "Road_ID_Name", "Road_Type", "VC_Ratio", "Risk_Level", "First_High_Year"]].to_csv(folder / "scenario_2035_summary.csv", index=False)
