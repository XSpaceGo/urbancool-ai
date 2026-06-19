from __future__ import annotations

import unittest

from gee_service import list_areas, scenario_summary, select_optimal_scenario


class ScenarioTests(unittest.TestCase):
    def test_scenario_summary_and_optimizer(self) -> None:
        scenarios = scenario_summary(
            {
                "greening_avg_reduction": 1.2,
                "cool_roof_avg_reduction": 1.0,
                "blue_green_avg_reduction": 0.8,
                "estimated_avg_reduction": 3.4,
            }
        )
        optimal = select_optimal_scenario(scenarios)

        self.assertEqual(len(scenarios), 4)
        self.assertEqual(optimal["key"], "combined")
        self.assertEqual(optimal["best_value_key"], "cool_roof")
        self.assertGreater(optimal["mean_reduction_c"], 3)

    def test_empty_optimizer_is_stable(self) -> None:
        optimal = select_optimal_scenario([])
        self.assertEqual(optimal["key"], "combined")

    def test_area_catalog_contains_distinct_city_bounds(self) -> None:
        areas = list_areas()
        identifiers = {area["id"] for area in areas}
        bounds = {tuple(area["bbox"]) for area in areas}
        self.assertIn("mumbai", identifiers)
        self.assertIn("delhi", identifiers)
        self.assertEqual(len(areas), len(bounds))


if __name__ == "__main__":
    unittest.main()
