# Metro Manila AADT simulation, 2025–2035

Run the simulation directly in a terminal. It prompts for a scenario, a year to inspect, and whether to save CSV results. The included CSV is in `data/`.

On Windows, from the repository folder:

```powershell
py -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements-cli.txt
.\.venv\Scripts\python run_simulation.py
```

The terminal runner uses Pandas, NumPy, and scikit-learn. Select baseline, accelerated growth, transit shift, ring-road expansion, or enter a custom annual growth rate. It prints all 20 roads for the selected year and can save full 2025–2035 results to a scenario-specific folder under `outputs/terminal/`. The menu repeats within one session. The optional notebook remains available for plots and detailed evaluation, using `requirements.txt`.

**Interpretation:** The dataset labels capacity as a synthetic scenario, and source AADT rows and PCU factors as unverified. Risk thresholds are Low (<0.70 V/C), Medium (0.70–<0.95), and High (≥0.95). The Random Forest classifies that derived risk; annual growth supplies the traffic forecast. Treat the first High year as a threshold crossing under stated assumptions, not a measured road failure year.
