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
        print(f"Please enter: {', '.join(sorted(choices))}")


def ask_year():
    while True:
        answer = input("Which year would you like to see? 2025-2035 [Enter = 2035]: ").strip()
        if not answer:
            return 2035
        if answer.isdigit() and 2025 <= int(answer) <= 2035:
            return int(answer)
        print("Enter a year from 2025 through 2035.")


def ask_growth():
    while True:
        answer = input("Yearly traffic growth percentage, 0-30 [Enter = 4.5]: ").strip()
        try:
            value = 4.5 if not answer else float(answer)
        except ValueError:
            value = -1
        if 0 <= value <= 30:
            return value / 100
        print("Enter a number from 0 to 30.")


def choose_scenario():
    print("\nCHOOSE A SCENARIO")
    print("-" * 100)
    print(f"{'No.':<5} {'Scenario':<31} {'What question does it answer?'}")
    print("-" * 100)
    rows = [
        ("1", "Baseline: 4.5% yearly growth", "What happens if traffic grows at the assumed rate?"),
        ("2", "Faster growth: 7% yearly", "What if traffic grows faster than expected?"),
        ("3", "Transit shift: 20% of cars", "What if some car users move to buses?"),
        ("4", "EDSA/C-5: 20% more capacity", "What if these roads gain capacity in 2028?"),
        ("5", "Your own growth rate", "What if traffic grows at a rate you choose?"),
        ("0", "Exit", "Close the simulation."),
    ]
    for number, label, goal in rows:
        print(f"{number:<5} {label:<31} {goal}")
    print("-" * 100)
    choice = ask_choice("Enter a scenario number (0-5): ", set("012345"))
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
    print(f"\nRESULTS: {result.Scenario.iat[0]} in {year}")
    print("Road capacity is an illustrative estimate, not a measured limit.")
    counts = frame.Risk_Level.value_counts().reindex(["Low", "Medium", "High"], fill_value=0)
    print("Roads by risk:", ", ".join(f"{level}: {count}" for level, count in counts.items()))
    print("Risk guide: Low = below 70% capacity; Medium = 70-<95%; High = 95% or more.")
    print("Capacity used means projected traffic divided by the illustrative road capacity.")
    print("AI risk is the Random Forest's estimate; Risk follows the stated capacity thresholds.")
    print("AI/rule differences for this year:", int(frame.RF_Disagreement.sum()))
    columns = ["Road_ID_Name", "Road_Type", "Road_PCU_Volume", "Capacity_Limit", "VC_Ratio", "Risk_Level", "RF_Risk_Level", "First_High_Year"]
    shown = frame[columns].sort_values("VC_Ratio", ascending=False).copy()
    shown["Road_PCU_Volume"] = shown.Road_PCU_Volume.round(0).astype(int)
    shown["Capacity_Limit"] = shown.Capacity_Limit.round(0).astype(int)
    shown["VC_Ratio"] = (shown.VC_Ratio * 100).map(lambda value: f"{value:.1f}%")
    shown["First_High_Year"] = shown.First_High_Year.astype("string").fillna("Not by 2035")
    shown.columns = ["Road", "Type", "Traffic PCU/day", "Capacity PCU/day", "Capacity used", "Risk", "AI risk", "First High year"]
    print(shown.to_string(index=False))
    print("First High year is the first modeled year at 95% capacity or more, not a measured failure year.")


def main():
    print("\nMETRO MANILA ROAD TRAFFIC SIMULATION | 2025-2035")
    print("Goal: explore when projected daily traffic may approach or exceed road capacity on 20 roads.")
    print("How to use: choose a scenario number, choose a year, then decide whether to save the full forecast.")
    print("After each result, the menu returns so you can compare another scenario. Enter 0 to exit.")
    print("The results are planning examples because the supplied road capacities are synthetic estimates.\n")
    print("Checking data and preparing the Random Forest risk model...")
    history = add_pcu_and_risk(validate_data(pd.read_csv(DATA)))
    model, metrics, _, comparison = fit_and_evaluate(history)
    print(f"Model check: the Random Forest matched {metrics.loc['accuracy', 'support']:.1%} of 2024-2025 risk labels.")
    print("This measures risk-label matching, not accuracy of future traffic forecasts.")
    while True:
        scenario = choose_scenario()
        if scenario is None:
            print("Goodbye.")
            return
        name, parameters = scenario
        result = simulate(history, model, name, **parameters)
        year = ask_year()
        show_results(result, year)
        if ask_choice("Save every year of this scenario as CSV files? (y/n): ", {"y", "n"}) == "y":
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
