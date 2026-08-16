"""Synthetic ride-log data for the CascadeCycle bike-share demo pipeline.

CascadeCycle is an invented city bike-share operator. None of this data
represents any real system; it exists purely to give the orchestrator
something realistic-looking to chew on.
"""

from __future__ import annotations

import random

STATIONS = [
    "Elm & 5th",
    "Riverside Landing",
    "Old Mill Square",
    "Harbor View",
    "Cedar Park",
    "Union Depot",
    "Willow Creek",
    "Founders Plaza",
]


def generate_rides(seed: int, count: int) -> list[dict]:
    """Generate `count` synthetic ride records, deterministic for a given seed.

    A small, fixed fraction of records are intentionally malformed
    (missing station, non-positive duration) to give the validation
    task real work to do.
    """
    rng = random.Random(seed)
    rides: list[dict] = []

    for i in range(count):
        start_station = rng.choice(STATIONS)
        end_station = rng.choice(STATIONS)
        duration_minutes = round(rng.uniform(3, 45), 1)
        distance_km = round(rng.uniform(0.5, 8.0), 2)

        # ~8% of rides are malformed, simulating real-world data quality issues.
        is_malformed = rng.random() < 0.08
        if is_malformed:
            defect = rng.choice(["missing_station", "bad_duration"])
            if defect == "missing_station":
                start_station = ""
            else:
                duration_minutes = -duration_minutes

        rides.append(
            {
                "ride_id": f"ride-{i:06d}",
                "start_station": start_station,
                "end_station": end_station,
                "duration_minutes": duration_minutes,
                "distance_km": distance_km,
                "hour_of_day": rng.randint(0, 23),
            }
        )

    return rides
