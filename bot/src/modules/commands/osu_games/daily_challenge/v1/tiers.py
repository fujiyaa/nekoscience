


import random

BASE_POINTS = {
    1: 80,
    2: 60,
    3: 30,
    4: 15
}



def calculate_points_for_tier(tier: int, time_taken_seconds: float) -> int:
    base = BASE_POINTS.get(tier, 0)

    TIME_COEFFICIENTS = [
        (30*60, 1.0),
        (60*60, 0.9),
        (2*60*60, 0.8),
        (3*60*60, 0.7),
        (float('inf'), 0.6)
    ]
    for limit, coeff in TIME_COEFFICIENTS:
        if time_taken_seconds <= limit:
            time_multiplier = coeff
            break         

    random_multiplier = random.uniform(0.75, 1.0)

    points = int(base * time_multiplier * random_multiplier)
    return max(points, 1)

def calculate_penalty_for_tier(tier: int, time_taken_seconds: float) -> int:
    base = BASE_POINTS.get(tier, 0)

    TIME_COEFFICIENTS = [
        (60, 1.1),
        (60*60, 1.0),
        (2*60*60, 0.9),
        (float('inf'), 0.8)
    ]
    for limit, coeff in TIME_COEFFICIENTS:
        if time_taken_seconds <= limit:
            time_multiplier = coeff
            break            

    random_multiplier = random.uniform(0.95, 1.0)

    points = int(base * time_multiplier * random_multiplier)
    return max(points, 1)
