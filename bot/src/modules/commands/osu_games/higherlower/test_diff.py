def calculate_max_diff(current_score, target_score=100, max_val=150, min_val=10, power=0.3):
    
    t = min(current_score / target_score, 1.0)
    
    max_diff = min_val + (max_val - min_val) * (1 - t**power)

    return max_diff

for score in range(0, 101, 5):
    print('#',score, " ", f"{calculate_max_diff(score):.2f}pp max")
