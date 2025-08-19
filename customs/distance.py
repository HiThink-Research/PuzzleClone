from z3 import *

def cal_dis(v1,v2,down_rate,up_rate,delta_distance):
    v1_after = v1 * (100 - down_rate) / 100
    v2_after = v2 * (100 + up_rate) / 100
    t1 = v1_after*delta_distance/(v1*v1_after-v2*v2_after)
    return round((v1+v2)*t1, 2)



if __name__ == '__main__':
    # 创建变量
    s = Real('s')    # A、B两地距离（千米）
    v1 = Real('v1')  # 甲初始速度
    v2 = Real('v2')  # 乙初始速度
    t1 = Real('t1')  # 相遇前行驶时间
    t2 = Real('t2')  # 相遇后行驶时间

    # 创建求解器
    solver = Solver()

    # 添加约束条件
    # 1. 初始速度比为5:4
    solver.add(v1 / v2 == 5 / 4)

    # 2. 相遇时，甲、乙行驶路程之和等于总距离
    solver.add(v1 * t1 + v2 * t1 == s)

    # 3. 相遇后甲的速度减少20%，乙的速度增加20%
    v1_after = v1 * 0.8
    v2_after = v2 * 1.2

    # 4. 相遇后甲行驶的路程等于相遇前乙行驶的路程
    solver.add(v1_after * t2 == v2 * t1)

    # 5. 相遇后乙行驶的路程等于相遇前甲行驶的路程减去10千米
    solver.add(v2_after * t2 == v1 * t1 - 10)

    solver.add(And([v2_after * t2 > 0,v1 * t1 - 10 > 10]))

    # 检查是否有解
    if solver.check() == sat:
        m = solver.model()
        # 计算总距离
        total_distance = m[s].as_decimal(2)
        print(f"A、B两地相距 {total_distance} 千米")
    else:
        print("无解")