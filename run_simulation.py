"""Interactive, terminal-only runner for the Metro Manila AADT model."""

from pathlib import Path
import re
import sys
import textwrap

import pandas as pd

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
        ("6", "Compare scenarios", "See the sensitivity range at 2025, 2030, and 2035."),
        ("0", "Exit", "Close the simulation."),
    ]
    for number, label, goal in rows:
        print(f"{number:<5} {label:<31} {goal}")
    print("-" * 100)
    choice = ask_choice("Enter a scenario number (0-6): ", set("0123456"))
    scenarios = {
        "1": ("Baseline 4.5%", {"growth_rate": 0.045}),
        "2": ("Accelerated 7%", {"growth_rate": 0.07}),
        "3": ("Transit shift 20%", {"growth_rate": 0.045, "transfer_share": 0.20}),
        "4": ("EDSA/C-5 expansion 20%", {"growth_rate": 0.045, "capacity_increase": 0.20}),
    }
    if choice == "5":
        growth = ask_growth()
        return f"Custom growth {growth * 100:g}%", {"growth_rate": growth}
    if choice == "6":
        return "__compare__", {}
    return scenarios.get(choice)


def show_comparison(comparison):
    width = 92
    border = "+" + "=" * (width - 2) + "+"
    print("\n" + border)
    print("| SCENARIO SENSITIVITY | planning comparison across stated assumptions".ljust(width - 1) + "|")
    print("| Changes in risk counts when assumptions change; this is not a probability forecast.".ljust(width - 1) + "|")
    print("|" + "-" * (width - 2) + "|")
    print("| " + f"{'Scenario':<25} {'Year':>4} {'Low':>5} {'Medium':>7} {'High':>6} {'Max V/C':>9}".ljust(width - 4) + " |")
    for _, row in comparison.iterrows():
        line = f"{row.Scenario:<25} {int(row.Year):>4} {int(row.Low_Roads):>5} {int(row.Medium_Roads):>7} {int(row.High_Roads):>6} {row.Max_VC:>8.1%}"
        print("| " + line.ljust(width - 4) + " |")
    print("|" + "-" * (width - 2) + "|")
    print("| Low <70%, Medium 70%-<95%, High >=95% of assumed capacity.".ljust(width - 1) + "|")
    print("| Max V/C = busiest road traffic divided by assumed capacity.".ljust(width - 1) + "|")
    print(border)


def show_results(result, year):
    frame = result.loc[result.Year.eq(year)].copy()
    baseline = result.loc[result.Year.eq(2025), ["Road_ID_Name", "Total_Raw_Volume_Reported", "Road_PCU_Volume"]].set_index("Road_ID_Name")
    counts = frame.Risk_Level.value_counts().reindex(["Low", "Medium", "High"], fill_value=0)
    year_alert = "High" if counts["High"] else "Medium" if counts["Medium"] else "Low"
    high_roads = frame.loc[frame.Risk_Level.eq("High"), "Road_ID_Name"].tolist()
    width = 108

    def border(char="-"):
        return "+" + char * (width - 2) + "+"

    def line(message=""):
        for part in textwrap.wrap(str(message), width - 4, break_long_words=False) or [""]:
            print("| " + part.ljust(width - 4) + " |")

    def table_line(message):
        if len(message) > width - 4:
            raise ValueError("Result row exceeds terminal box width")
        print("| " + message.ljust(width - 4) + " |")

    print("\n" + border("="))
    line(f"TRAFFIC RISK RESULT | {result.Scenario.iat[0]} | YEAR {year}")
    print(border())
    line(f"AT A GLANCE: {year} is {year_alert.upper()} ALERT for this 20-road group.")
    line(f"In {year}: {counts['High']} roads are High, {counts['Medium']} are Medium, and {counts['Low']} are Low.")
    line("The group alert uses the highest road risk; it does not mean every road has that risk.")
    line("High-risk roads this year: " + (", ".join(high_roads) if high_roads else "none"))
    print(border())
    line(f"ROAD-BY-ROAD RISK IN {year}")
    header = f"{'Road':<20} {'2025 vehicles':>13} {'2025 PCU':>10} {str(year) + ' PCU':>10} {'Cap. used':>9} {str(year) + ' risk':>9} {'AI risk':>8} {'High from':>9}"
    table_line(header)
    print(border())
    for _, road in frame.sort_values("VC_Ratio", ascending=False).iterrows():
        first_high = "-" if pd.isna(road.First_High_Year) else str(int(road.First_High_Year))
        row = (f"{road.Road_ID_Name:<20} {baseline.loc[road.Road_ID_Name, 'Total_Raw_Volume_Reported']:>13,.0f} "
               f"{baseline.loc[road.Road_ID_Name, 'Road_PCU_Volume']:>10,.0f} "
               f"{road.Road_PCU_Volume:>10,.0f} {road.VC_Ratio:>8.1%} "
               f"{road.Risk_Level:>9} {road.RF_Risk_Level:>8} {first_high:>9}")
        table_line(row)
    print(border())
    line("WHAT THE COLUMNS MEAN")
    line("2025 vehicles/day = reported vehicle count in the supplied dataset (source unverified).")
    line("2025 PCU/day = that vehicle mix converted to passenger-car units; this is calculated, not measured.")
    line(f"{year} PCU/day = projected daily traffic under the selected scenario. For 2025, this is the baseline, not a forecast.")
    line("Capacity used = projected traffic divided by assumed road capacity; the capacity is not measured.")
    line("Risk assessment = Low below 70%, Medium from 70% to below 95%, High at 95% or more.")
    line("AI assessment = Random Forest label. It can disagree with the threshold-based risk assessment.")
    line(f"The AI assessment differs from the threshold assessment for {int(frame.RF_Disagreement.sum())} roads in {year}.")
    line("High from = first modeled year at 95% capacity or more; '-' means no crossing by 2035.")
    line("These are scenario results for planning, not measured capacity or a prediction of physical road failure.")
    print(border("="))


def main():
    print("\nMETRO MANILA ROAD TRAFFIC SIMULATION | 2025-2035")
    print("Goal: explore when projected daily traffic may approach or exceed road capacity on 20 roads.")
    print("How to use: choose a scenario number, choose a year, then decide whether to save the full forecast.")
    print("After each result, the menu returns so you can compare another scenario. Enter 0 to exit.")
    print("The results are planning examples because the supplied road capacities are synthetic estimates.\n")
    if sys.version_info >= (3, 14):
        print("This CLI requires a supported scientific-Python runtime. Please recreate the environment with Python 3.12:")
        print("  py -3.12 -m venv .venv")
        print("  .\\.venv\\Scripts\\python -m pip install -r requirements-cli.txt")
        print("Then run this command again. Python 3.14 may block the SciPy DLL used by scikit-learn on Windows.\n")
        return
    print("Checking data and preparing the Random Forest risk model...")
    try:
        from aadt_model import add_pcu_and_risk, compare_predefined_scenarios, fit_and_evaluate, save_outputs, simulate, validate_data
    except (ImportError, OSError) as exc:
        print("\nThe scientific Python packages could not be loaded.")
        print("On Windows, recreate the environment with Python 3.12 and run the installation commands in README.md.")
        print(f"Technical detail: {exc}")
        return
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
        if name == "__compare__":
            comparison = compare_predefined_scenarios(history, model)
            show_comparison(comparison)
            if ask_choice("Save this sensitivity table as CSV? (y/n): ", {"y", "n"}) == "y":
                destination = ROOT / "outputs" / "terminal" / "scenario_comparison.csv"
                comparison.to_csv(destination, index=False)
                print(f"Saved {destination}")
            continue
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
