import unittest
from pathlib import Path

import pandas as pd

from aadt_model import add_pcu_and_risk, simulate, validate_data


class SimulationFallbackTests(unittest.TestCase):
    def test_simulation_keeps_threshold_results_when_random_forest_is_unavailable(self):
        root = Path(__file__).resolve().parents[1]
        history = add_pcu_and_risk(
            validate_data(pd.read_csv(root / "data" / "metro_manila_aadt_simulation_input_2020_2025.csv"))
        )

        result = simulate(history, None, "Test fallback", growth_rate=0.045)
        year = result.loc[result.Year.eq(2025)]

        self.assertEqual(len(year), 20)
        self.assertTrue(year.Risk_Level.isin(["Low", "Medium", "High"]).all())
        self.assertTrue(year.RF_Risk_Level.eq("N/A").all())
        self.assertTrue(year.RF_Disagreement.isna().all())
