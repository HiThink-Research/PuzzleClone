from z3 import *

def cal_workers(num_AB,num_C,hour_A,hour_B,hour_C,num_worker_A,num_worker_B):
    # 创建变量（全部使用实数类型以避免类型冲突）
    w = Real('w')  # 每个工人每小时加工量
    m = Real('m')  # 每台输送机每小时加工量
    n = Real('n')  # 丙仓库需要的工人数（暂时用实数）
    s = Real('s')  # 每个仓库的面粉总量

    # 创建求解器
    opt = Optimize()

    # 添加约束条件
    # 甲仓库：num_AB台机器+num_worker_A个工人，hour_A小时加工完
    opt.add(hour_A * (num_AB * m + num_worker_A * w) == s)

    # 乙仓库：num_AB台机器+num_worker_B个工人，hour_B小时加工完
    opt.add(hour_B * (num_AB * m + num_worker_B * w) == s)

    # 丙仓库：num_C台机器+n个工人，n小时加工完
    opt.add(hour_C * (num_C * m + n * w) == s)

    opt.add(num_worker_B*hour_B > num_worker_A*hour_A)

    # 确保变量为正数
    opt.add(w > 0, m > 0, n >= 0, s > 0)

    # 最小化工人数n
    opt.minimize(n)

    # 检查是否有解
    if opt.check() == sat:
        m = opt.model()
        # 将n转换为整数（向上取整，因为工人数必须为整数）
        n_rounded = int(math.ceil(float(m[n].as_decimal(2))))
        print(f"至少需要 {n_rounded} 个工人")
        return n_rounded
        # print(f"每个工人每小时搬运量: {m[w]}")
        # print(f"每台输送机每小时搬运量: {m[m]}")
        # print(f"每个仓库面粉总量: {m[s]}")
    else:
        print("无解")
        return -1

if __name__ == '__main__':

    num_AB = 1
    num_C = 2
    hour_A = 5
    hour_B = 3
    hour_C = 2
    num_worker_A = 12
    num_worker_B = 28

    res = cal_workers(num_AB,num_C,hour_A,hour_B,hour_C,num_worker_A,num_worker_B)