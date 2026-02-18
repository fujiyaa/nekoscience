


def calculate_max_diff(current_score, target_score=200, max_val=300, min_val=10, power=0.2):
    
    t = min(current_score / target_score, 1.0)
    
    max_diff = min_val + (max_val - min_val) * (1 - t**power)

    return max_diff

for score in range(0, 201, 10):
    print(score, calculate_max_diff(score))
