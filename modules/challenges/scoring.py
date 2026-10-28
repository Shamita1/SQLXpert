"""
Scoring and reward calculations based on completion time and difficulty.
"""

def calculate_reward(base_xp: int, base_coins: int, time_remaining: int, total_time: int) -> tuple[int, int]:
    """
    Calculates final XP and SQL-Coins using speed multiplier:
    Final XP = Base XP * (1 + Time Remaining / Total Time)
    """
    if total_time <= 0:
        multiplier = 1.0
    else:
        multiplier = 1.0 + max(0.0, float(time_remaining) / float(total_time))
    
    earned_xp = int(base_xp * multiplier)
    earned_coins = int(base_coins * multiplier)
    return earned_xp, earned_coins