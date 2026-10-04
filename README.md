# Metro Manila AADT simulation, 2025–2035

Open [aadt_simulation_2025_2035.ipynb](aadt_simulation_2025_2035.ipynb) in JupyterLab and run all cells. The included CSV is in `data/`. Outputs are written to `outputs/`.

On Windows, from the repository folder:

```powershell
py -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m jupyter lab
```

The notebook uses Pandas, NumPy, scikit-learn, Matplotlib, and Seaborn. SimPy is unnecessary for the annual time-step model.

**Interpretation:** The dataset labels capacity as a synthetic scenario, and source AADT rows and PCU factors as unverified. Risk thresholds are Low (<0.70 V/C), Medium (0.70–<0.95), and High (≥0.95). The Random Forest classifies that derived risk; annual growth supplies the traffic forecast. Treat the first High year as a threshold crossing under stated assumptions, not a measured road failure year.
