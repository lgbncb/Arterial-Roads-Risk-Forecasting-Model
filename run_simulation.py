"""Interactive, terminal-only runner for the Metro Manila AADT model."""

from pathlib import Path
import re

import pandas as pd

from aadt_model import add_pcu_and_risk, fit_and_evaluate, save_outputs, simulate, validate_data

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data" / "metro_manila_aadt_simulation_input_2020_2025.csv"


def ask_choice(prompt, choices):
    while True:
        answer = input(prompt).strip().lower()
        if answer in choices:
            return answer
        print(f"Enter one of: {', '.join(choices)}")


def ask_year():
    while True:
        answer = input("Year to inspect (2025–2035, default 2035): ").strip()
        if not answer:
            return 2035
        if answer.isdigit() and 2025 <= int(answer) <= 2035:
            return int(answer)
        print("Enter a year from 2025 through 2035.")


def ask_growth():
    while True:
        answer = input("Annual growth percent (0–30, default 4.5): ").strip()
        try:
            value = 4.5 if not answer else float(answer)
        except ValueError:
            value = -1
        if 0 <= value <= 30:
            return value / 100
        print("Enter a number from 0 to 30.")


def choose_scenario():
    print("\nScenario: 1) baseline 4.5%  2) accelerated 7%  3) transit shift 20%")
    print("          4) EDSA/C-5 capacity +20% in 2028  5) custom annual growth  0) quit")
    choice = ask_choice("Choose 0–5: ", set("012345"))
    scenarios = {
        "1": ("Baseline 4.5%", {"growth_rate": 0.045}),
        "2": ("Accelerated 7%", {"growth_rate": 0.07}),
        "3": ("Transit shift 20%", {"growth_rate": 0.045, "transfer_share": 0.20}),
        "4": ("EDSA/C-5 expansion 20%", {"growth_rate": 0.045, "capacity_increase": 0.20}),
    }
    if choice == "5":
        growth = ask_growth()
        return f"Custom growth {growth * 100:g}%", {"growth_rate": growth}
    return scenarios.get(choice)


def show_results(result, year):
    frame = result.loc[result.Year.eq(year)].copy()
    print(f"\n{result.Scenario.iat[0]} | {year} | synthetic capacity, not measured")
    counts = frame.Risk_Level.value_counts().reindex(["Low", "Medium", "High"], fill_value=0)
    print("Roads by direct V/C risk:", ", ".join(f"{level} {count}" for level, count in counts.items()))
    print("Random Forest disagreements:", int(frame.RF_Disagreement.sum()))
    columns = ["Road_ID_Name", "Road_Type", "Road_PCU_Volume", "Capacity_Limit", "VC_Ratio", "Risk_Level", "RF_Risk_Level", "First_High_Year"]
    shown = frame[columns].sort_values("VC_Ratio", ascending=False).copy()
    shown["Road_PCU_Volume"] = shown.Road_PCU_Volume.round(0).astype(int)
    shown["Capacity_Limit"] = shown.Capacity_Limit.round(0).astype(int)
    shown["VC_Ratio"] = shown.VC_Ratio.round(3)
    shown["First_High_Year"] = shown.First_High_Year.astype("string").fillna("—")
    print(shown.to_string(index=False))
    print("First High year means first V/C >= 0.95 during 2025-2035; it is not a measured failure year.")


def main():
    print("Metro Manila AADT simulation | 20 roads | 2025–2035")
    print("Loading data and training the Random Forest...")
    history = add_pcu_and_risk(validate_data(pd.read_csv(DATA)))
    model, metrics, _, comparison = fit_and_evaluate(history)
    print(f"2024–2025 Random Forest holdout accuracy: {metrics.loc['accuracy', 'support']:.1%}")
    print(f"Forest/direct-rule disagreements: {int(comparison.Disagreement.sum())} of {len(comparison)}")
    print("Risk labels are derived from V/C; classifier accuracy is not independent traffic forecast accuracy.")
    while True:
        scenario = choose_scenario()
        if scenario is None:
            print("Goodbye.")
            return
        name, parameters = scenario
        result = simulate(history, model, name, **parameters)
        year = ask_year()
        show_results(result, year)
        if ask_choice("Save all 2025–2035 results to outputs/? (y/n): ", {"y", "n"}) == "y":
            slug = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
            destination = ROOT / "outputs" / "terminal" / slug
            save_outputs(result, destination)
            print(f"Saved {destination / 'road_year_forecast.csv'}")
            print(f"Saved {destination / 'scenario_2035_summary.csv'}")


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\nStopped.")
