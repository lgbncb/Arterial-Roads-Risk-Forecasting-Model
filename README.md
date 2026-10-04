# Metro Manila AADT simulation, 2025–2035

## What this simulation does

It projects how much traffic the 20 included Metro Manila roads might carry each year from 2025 to 2035, then compares that traffic with an illustrative road capacity. The result is a Low, Medium, or High risk level. The goal is to see **which roads may reach high usage first under different assumptions**. The capacity figures in the supplied dataset are synthetic estimates, so these are planning scenarios rather than measured predictions.

## Run it in PowerShell

On Windows, from the repository folder:

```powershell
py -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements-cli.txt
.\.venv\Scripts\python run_simulation.py
```

The terminal runner uses Pandas, NumPy, and scikit-learn. After it starts, enter a **scenario number from 1 to 5**. Enter a year from **2025 to 2035**, or press Enter to see 2035. One result box shows the supplied 2025 vehicle count, calculated 2025 PCU, scenario traffic, capacity use, threshold risk, AI risk, and first High year, with explanations inside the same box. Answer **y** to save all years of that scenario as CSV files under `outputs/terminal/`, or **n** to return to the menu. Enter **0** at the scenario menu to quit. The optional notebook remains available for plots and detailed evaluation, using `requirements.txt`.

## What each scenario asks

- **1. Baseline:** If traffic grows 4.5% each year and capacity stays fixed, when might roads reach high usage?
- **2. Faster growth:** If traffic grows 7% each year, how much sooner might that happen?
- **3. Transit shift:** If 20% of projected cars move to buses (assuming 40 shifted cars per new bus), how might road usage change? This is an illustrative assumption.
- **4. EDSA/C-5 capacity increase:** If these two roads gain 20% capacity in 2028, how might their risk change? This is an illustrative intervention.
- **5. Your own growth rate:** Enter a yearly growth percentage to explore a different assumption.

**Interpretation:** The dataset labels capacity as a synthetic scenario, and source AADT rows and PCU factors as unverified. Risk thresholds are Low (<0.70 V/C), Medium (0.70–<0.95), and High (≥0.95). The Random Forest classifies that derived risk; annual growth supplies the traffic forecast. Treat the first High year as a threshold crossing under stated assumptions, not a measured road failure year.
