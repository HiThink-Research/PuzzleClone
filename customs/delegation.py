import random

def generate_remainders_list(n,total):

    min_threshold = 3
    # 初始化数组，每个元素先分配最小值
    arr = [min_threshold] * n
    remaining = total - n * min_threshold
    
    # 随机分配剩余值
    for _ in range(remaining):
        # 随机选择一个索引并增加1
        idx = random.randint(0, n-1)
        arr[idx] += 1
    
    # 随机打乱数组顺序
    random.shuffle(arr)
    return arr

import itertools

def cal_res(remainders,photos):
    l = len(remainders)
    all_pairs_index = list(itertools.combinations(list(range(l)),2))
    multi = 0
    for index in all_pairs_index:
        multi += remainders[index[0]]*remainders[index[1]]
    return multi % photos

if __name__ == '__main__':
    num_passengers = 40
    num_delega = 4
    remainders = generate_remainders_list(num_delega,num_passengers)
    print(remainders)
    remainders = [15, 30, 11]
    photos = 28
    print(cal_res(remainders,photos))