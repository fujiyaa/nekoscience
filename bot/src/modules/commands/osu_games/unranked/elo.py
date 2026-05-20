import math

def calculate_expected(rating_a, rating_b):
    """
    Рассчитывает ожидаемый результат (вероятность победы) для игрока A.

    Args:
        rating_a (float): рейтинг игрока A
        rating_b (float): рейтинг игрока B

    Returns:
        float: вероятность победы игрока A (от 0 до 1)
    """
    return 1 / (1 + 10 ** ((rating_b - rating_a) / 400))


def update_elo(rating_a, rating_b, result_a, k_factor=20):
    """
    Обновляет рейтинги двух игроков после матча.

    Args:
        rating_a (float): текущий рейтинг игрока A
        rating_b (float): текущий рейтинг игрока B
        result_a (float): результат матча для игрока A:
                         1 — победа, 0.5 — ничья, 0 — поражение
        k_factor (int): K‑фактор (коэффициент развития)

    Returns:
        tuple: (новый рейтинг игрока A, новый рейтинг игрока B)
    """
    expected_a = calculate_expected(rating_a, rating_b)
    expected_b = 1 - expected_a

    new_rating_a = rating_a + k_factor * (result_a - expected_a)
    new_rating_b = rating_b + k_factor * ((1 - result_a) - expected_b)

    return round(new_rating_a), round(new_rating_b)

def run_elo_tests():
    test_scenarios = [
        # (рейтинг A, рейтинг B, результат A)
        (1000, 800, 1),
        (1000, 900, 1),
        (1000, 1000, 1),
        (1000, 1100, 1),
        (1000, 1200, 1),

        (1200, 1000, 0),
        (1200, 1100, 0),
        (1200, 2000, 0),

        (1200, 1000, 0.5),
        (1200, 1100, 0.5),
        (1200, 2000, 0.5),
    ]

    for rating_a, rating_b, result_a in test_scenarios:
        print(f"{rating_a} vs {rating_b}, первый победил: {result_a}")

        expected_a = calculate_expected(rating_a, rating_b)
        expected_b = 1 - expected_a
        print(f"{expected_a:.3f} vs {expected_b:.3f}")

        new_a, new_b = update_elo(rating_a, rating_b, result_a)

        change_a = new_a - rating_a
        change_b = new_b - rating_b
        print(f"{new_a} ({change_a:+d}), {new_b} ({change_b:+d})")
        # print('\n')

if __name__ == "__main__":
    run_elo_tests()
