## 贪心问题

import heapq
from random import randint

def generate_repairs(num_trams,min_repair,max_repair):
    return [randint(min_repair,max_repair) for _ in range(num_trams)]

def waiting_minutes(repairs,num_workers):
    # 维修时间列表（按升序排列）
    # repairs = [8, 12, 14, 17, 18, 23, 30]
    repairs = sorted(repairs)
    
    # 初始化三名工人的总维修时间（使用最小堆）
    workers = [(0, i) for i in range(num_workers)]  # (总时间, 工人编号)
    heapq.heapify(workers)
    
    # 记录每个工人的任务列表
    worker_tasks = [[] for _ in range(num_workers)]
    
    # 分配任务
    for time in repairs:
        current_time, worker_id = heapq.heappop(workers)
        worker_tasks[worker_id].append(time)
        new_time = current_time + time
        heapq.heappush(workers, (new_time, worker_id))
    
    # 计算总停开时间
    total_waiting = 0
    minutes = []
    for tasks in worker_tasks:
        n = len(tasks)
        minutes.append(sum(tasks))
        for i, time in enumerate(tasks):
            total_waiting += time * (n - i)  # 后续任务数 + 1
    
    # 计算最小损失
    # loss = total_waiting * 11
    return total_waiting, minutes, worker_tasks


# 执行计算
if __name__ == '__main__':

    num_workers = 4
    num_trams = 7
    loss_per_min = 11
    min_repair,max_repair = randint(6,12),randint(25,40)

    # repairs = [8, 12, 14, 17, 18, 23, 30]
    repairs = generate_repairs(num_trams,min_repair,max_repair)

    total_waiting, minutes, worker_tasks = waiting_minutes(repairs,num_workers)
    print(f"维修时间: {'、'.join(str(item) for item in repairs)} 分钟")
    print(f"最小损失: {total_waiting*loss_per_min} 元")
    print("工作时间:")
    for i, mintue in enumerate(minutes):
        print(f"工人 {i+1}: {mintue}")
    print("分配方案:")
    for i, tasks in enumerate(worker_tasks):
        print(f"工人 {i+1}: {tasks}")