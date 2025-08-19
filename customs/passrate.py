from random import randint
import math

def calculate_min_pass_rate(correct_rates,cor_num):
    """
    计算考试的最小及格率（做对3题及以上为及格）
    
    参数:
    correct_rates -- 各题的正确率列表，例如 [0.92, 0.86, 0.61, 0.87, 0.57]
    
    返回:
    最小及格率（百分比）
    """
    num = len(correct_rates)  # 题目数量
    wrong_counts = [100 * (1 - rate) for rate in correct_rates]  # 每道题的错误次数
    
    # 初始情况：所有错题都由错cor_num题的人承担（但可能不可行）
    total_wrong = sum(wrong_counts)
    # initial_fail = total_wrong // (n - cor_num + 1)
    # initial_pass = 100 - initial_fail
    
    # 逐步调整：每次排除错误次数最多的题目，重新计算
    sorted_indices = sorted(range(num), key=lambda i: -wrong_counts[i])
    max_fail = 0
    
    for k in range(num):
        # 排除前k个错误次数最多的题目
        considered_indices = sorted_indices[k:]
        if not considered_indices:
            break
            
        # 计算剩余题目的总错误次数
        considered_wrong = [wrong_counts[i] for i in considered_indices]
        sum_considered = sum(considered_wrong)
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  
        # 假设每个人最多错 (cor_num-k) 题
        max_errors_per_person = num - cor_num + 1 - k
        if max_errors_per_person <= 0:
            continue
            
        # 计算可能的最大不及格人数
        current_fail = math.floor(sum_considered // max_errors_per_person)

        if current_fail > wrong_counts[sorted_indices[k]]:
            max_fail = current_fail
            break
    
    # 计算最小及格率
    min_pass = 100 - max_fail
    # min_pass_rate = min_pass / 100

    print(f"这次考试的及格率至少是 {min_pass:.2f}%")  # 输出 65.00%

    return min_pass/100

def generate_correct_rates(num):
    res = []
    for i in range(num):
        res.append(randint(50,100)/100)
    return res


if __name__ == '__main__':
    n = 6
    cor_num = randint(math.ceil(n/2),n-1)
    correct_rates = generate_correct_rates(n)

    # 示例：原题数据
    # n = 5
    # cor_num = 3
    # correct_rates = [0.92, 0.86, 0.61, 0.87, 0.57]

    # n = 6
    # cor_num = 4
    # correct_rates = [0.84, 0.6, 0.8, 0.76, 0.68, 0.53]

    print(correct_rates,n,cor_num)
    min_pass_rate = calculate_min_pass_rate(correct_rates,cor_num)


    # 测试其他数据
    # n = 6
    # cor_num = 4
    # correct_rates = [0.98, 0.98, 0.82, 0.65, 0.7, 0.93]
    # min_pass_rate = calculate_min_pass_rate(correct_rates)
    # print(f"及格率至少是 {min_pass_rate * 100:.2f}%") 71%