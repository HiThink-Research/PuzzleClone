# 已知条件

# 设总层数为 n，总楼梯数为 (n-1)*2*18
# 甲的时间：t_a = (n-1)*2*18 / 6
# 乙的时间：t_b = [(n-1)*2*18 - 120] / 4
# 由于时间相等，解方程：(n-1)*2*18 / 6 = [(n-1)*2*18 - 120] / 4

# 解方程

from sympy import symbols, Eq, solve

def cal_stairs(l,stairs_per_floor,v_a,v_b,delta):

    n = symbols('n')
    equation = Eq(l*(n-1)*2*stairs_per_floor / v_a, (l*(n-1)*2*stairs_per_floor - delta) / v_b)
    solution = solve(equation, n)

    print(f"这幢高层建筑有 {solution[0]} 层楼")

    return solution[0]

# def cal_delta(num,v_a,v_a):

if __name__ == "__main__":
    stairs_per_floor = 18
    v_a = 6  # 甲的速度（级/秒）
    v_b = 4  # 乙的速度（级/秒）
    delta = 120  # 甲到达底层时，乙未走完的级数
    l = 1 # 走了多少趟来回

    res = cal_stairs(l,stairs_per_floor,v_a,v_b,delta)

    # 输出结果
    # print(f"这幢高层建筑有 {res} 层楼")

