import random

def generate_weather_list():
    # 预留每个数至少 10
    remaining = 100 - 3 * 10
    # 生成两个 1-69 之间的随机分割点
    a, b = sorted(random.sample(range(1, remaining), 2))
    # 转换为每个数的值（均大于 10）
    return [10 + a, 10 + b - a, 10 + remaining - b]

