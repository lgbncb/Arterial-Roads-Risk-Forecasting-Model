# AADT Simulation Notebook Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver a runnable Jupyter notebook forecasting PCU demand and road risk for 20 Metro Manila roads, 2025–2035.

**Architecture:** The notebook validates historical CSV data, recomputes PCU, trains and evaluates a Random Forest, then runs parameterized annual scenarios. The deterministic V/C threshold remains visible alongside AI predictions.

**Tech Stack:** Python, Jupyter, pandas, NumPy, scikit-learn, matplotlib, seaborn.

**Spec:** `docs/superpowers/specs/2026-10-05-aadt-simulation-design.md`

## Global Constraints

- Include all 20 roads and preserve Circumferential, Radial, and Highway types.
- Record 2025 unchanged; simulate growth from 2026 through 2035.
- Use 0.70 and 0.95 V/C thresholds and synthetic capacity disclosure.
- Use a 2020–2023 training and 2024–2025 evaluation split.

## Review Focus

- Duplicate or missing road-year input must fail validation clearly.
- Nonpositive synthetic capacity must fail validation.
- Missing risk class in training or evaluation must be reported.
- Scenario results must not mutate the 2025 input baseline.
- First High year must follow direct V/C risk, including a High 2025 baseline.

---

### Task 1: Data and PCU pipeline

**Files:** Create `data/metro_manila_aadt_simulation_input_2020_2025.csv`; create `aadt_simulation_2025_2035.ipynb`.

**Interfaces:** `validate_data(df) -> DataFrame`, `add_pcu_and_risk(df) -> DataFrame`.

- [x] Copy the supplied CSV into `data/` and add setup and data validation notebook cells.
- [x] Add PCU recomputation and historical threshold-risk cells.
- [x] Execute validation, including duplicate, capacity, row-count, and 2025 PCU checks.

### Task 2: Random Forest evaluation

**Files:** Modify `aadt_simulation_2025_2035.ipynb`.

**Interfaces:** `make_features(df) -> DataFrame`, `fit_and_evaluate(df) -> classifier`.

- [x] Train on 2020–2023 and evaluate on 2024–2025 with accuracy, macro metrics, support, confusion matrix, and direct-rule comparison.
- [x] Execute the notebook and inspect missing-class and label-leakage disclosures.

### Task 3: Scenarios, outputs, and verification

**Files:** Modify `aadt_simulation_2025_2035.ipynb`; create `README.md` updates.

**Interfaces:** `simulate(df, model, name, growth_rate, transfer_share=0, capacity_increase=0, expansion_year=2028) -> DataFrame`.

- [x] Implement baseline, 7% growth, car-to-bus transfer, and ring-road expansion with 2025–2035 output.
- [x] Add first High year, summary tables, heatmap, trajectories, and CSV exports.
- [x] Run a fresh-kernel notebook execution and check 20 rows/year, threshold boundaries, growth, capacities, and output files.
