from __future__ import annotations

import unittest

import numpy as np

from ml_model import FEATURE_COLUMNS, train_lst_model


class ModelTests(unittest.TestCase):
    def test_random_forest_learns_driver_relationship(self) -> None:
        rng = np.random.default_rng(42)
        samples = []
        for _ in range(180):
            ndvi = float(rng.uniform(0, 0.7))
            ndbi = float(rng.uniform(-0.1, 0.6))
            built_up = float(np.clip((ndbi + 0.2) / 0.7, 0, 1))
            air = float(rng.uniform(28, 35))
            wind = float(rng.uniform(0.5, 5))
            humidity = float(rng.uniform(45, 85))
            vegetation_deficit = float(1 - (ndvi + 0.2))
            lst = 24 + 9 * built_up - 7 * ndvi + 0.45 * air - 0.35 * wind + rng.normal(0, 0.35)
            samples.append(
                {
                    "LST": float(lst),
                    "NDVI": ndvi,
                    "NDBI": ndbi,
                    "built_up": built_up,
                    "vegetation_deficit": vegetation_deficit,
                    "air_temperature": air,
                    "relative_humidity": humidity,
                    "wind_speed": wind,
                }
            )

        result = train_lst_model(samples)

        self.assertEqual(result.rows_used, 180)
        self.assertIsNotNone(result.r2)
        self.assertGreater(result.r2 or 0, 0.75)
        self.assertLess(result.mae or 99, 1.5)
        self.assertEqual(set(result.feature_importance), set(FEATURE_COLUMNS))
        self.assertAlmostEqual(sum(result.grouped_importance.values()), 1.0, places=3)


if __name__ == "__main__":
    unittest.main()
