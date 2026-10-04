# Metro Manila AADT simulation notebook design

## Purpose and scope

Build a reproducible Jupyter Notebook that forecasts daily PCU demand and risk for all 20 roads in the supplied 2020–2025 CSV through 2035. Retain the CSV's Circumferential, Radial, and Highway road types in outputs. The intended audience is the project team and peer reviewers. Results are scenario projections for decision support, not measured future capacity or instructions to implement policy.

## Inputs and assumptions

- The CSV is the sole input dataset. Each of the 20 roads should have one record for each year 2020–2025. Verify that structure and numeric fields before fitting or simulation.
- Use the vehicle-class counts and the CSV's PCEF fields to recompute PCU per day. Check the recomputed value against `Road_PCU_Volume_Per_Day`, reporting material discrepancies rather than silently replacing them.
- Use the 2025 row for each road to initialize vehicle counts and `Capacity_Limit_PCU_Per_Day`. Capacity remains fixed in the baseline. The CSV explicitly labels these capacities as synthetic, not measured; carry that disclosure into charts and exported results.
- Apply 4.5% compound growth to each vehicle class once per year in the baseline. Record 2025 unchanged, then calculate 2026–2035. This preserves vehicle mix in the baseline; any altered mix belongs to a named scenario.
- Calculate V/C as simulated PCU per day divided by synthetic capacity per day. Use Low for V/C < 0.70, Medium for 0.70 ≤ V/C < 0.95, and High for V/C ≥ 0.95. The first High year is the projected threshold-crossing year within the simulated horizon, not proof of physical road failure.

## Notebook architecture

1. **Setup and configuration:** imports, dataset path, random seed, years, growth rate, thresholds, and scenario parameters. Use Pandas, NumPy, scikit-learn, and Matplotlib/Seaborn. SimPy is unnecessary for an annual fixed-step model.
2. **Ingest and validate:** read the CSV, check required columns, missing/duplicate road-year records, positive capacities, vehicle counts, road types, and supplied status flags. Summarize any source verification and pandemic flags.
3. **PCU standardization:** compute class-weighted PCU and vehicle proportions with named functions. Keep raw and computed fields distinct.
4. **Historical risk and AI evaluation:** derive risk labels using V/C. Train a Random Forest classifier on historical road-year rows using features available in a simulated year. Hold out 2024–2025 for time-based evaluation, with 2020–2023 for training; report support, confusion matrix, accuracy, macro precision/recall/F1, and a direct-threshold baseline. If a class is absent from training or holdout, show that limitation explicitly. Avoid random row splits that mix years from the same roads. State that PCU and capacity determine the labels, so high classification accuracy is largely formula recovery rather than independent congestion prediction.
5. **Simulation engine:** for each road, initialize `Current_Year`, per-class counts, `Road_PCU_Volume`, `Capacity_Limit`, and `Risk_Level` from 2025. Advance one annual step, update counts and PCU, calculate V/C, obtain the Random Forest classification and direct-threshold classification, and append one output row. Keep both risk values visible; use direct-threshold risk for the first High year so tree extrapolation cannot hide a threshold crossing. Flag disagreements.
6. **Scenarios:** run baseline 4.5% growth first. Add separate runs for 7% growth, a defined 20% car-to-bus transfer, and 20% capacity expansion on named critical Circumferential roads starting in 2028. Document transfer mechanics and targeted roads in configuration before interpreting these optional scenarios. Do not present them as observed changes.
7. **Results:** road-year table, V/C heatmap, trajectories by road type, first High year, class counts by year, and scenario comparison. Export reviewable CSV outputs from the notebook. Label every output with scenario and capacity assumption.

## Evaluation and interpretation

The Random Forest meets the paper's requested AI step, but it does not forecast traffic volume: the annual growth rule does that. Compare its predictions with the deterministic risk rule, especially beyond the training range. Report the paper's 80% accuracy target as a target, not a guaranteed result. The forecast has no uncertainty interval under a single fixed growth assumption; scenario variation is sensitivity analysis rather than a calibrated probability range. AADT cannot represent peak-hour queues, incidents, weather, or vehicle-level behavior.

## Acceptance checks

- A fresh Jupyter kernel runs every notebook cell in order using the supplied dataset.
- Exactly 20 roads appear in every simulated year from 2025 through 2035, with no duplicate road-year rows.
- The 2025 simulated PCU matches the recomputed 2025 baseline within rounding tolerance; baseline capacity stays fixed.
- For each road, 2026 counts equal 2025 counts × 1.045 and later years compound once per step.
- Threshold boundary checks classify 0.70 as Medium and 0.95 as High.
- The Random Forest evaluation and the direct-rule comparison are both displayed, including discrepancies.
- Tables and plots distinguish synthetic capacity, scenario assumptions, and observed historical input.
