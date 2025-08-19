import numpy as np

def pos_A(t, S, v):
    # 输入时间t，两地距离，A的速度，返回t时间A的位置，行走的总距离，以及行走的朝向
    d = v * t
    times = int(d // S)
    if times % 2 == 0:
        return d % S, d, "right"
    else:
        return S - (d % S), d, "left"

def pos_B(t, S, v):
    d = v * t
    times = int(d // S)
    if times % 2 == 0:
        return S - (d % S), d, "left"
    else:
        return d % S, d, "right"

def find_nth_meeting(n, S, a, b, dt=0.0001, max_t=1000):
    meetings = []
    t = 0
    last_met = False
    last_abs = S

    while len(meetings) < n or (len(meetings) == n and last_met):
        pA, sA, dirA = pos_A(t, S, a)
        pB, sB, dirB = pos_B(t, S, b)
        meeting_type = "反向" if dirA != dirB else "同向"

        this_abs = abs(pA - pB)
        if this_abs < 0.1:  # 相遇
            if last_met:
                if this_abs < last_abs:
                    meetings[-1] = (t, pA, pB, sA, sB, dirA, dirB, meeting_type)
                    last_abs = this_abs
            else:
                meetings.append((t, pA, pB, sA, sB, dirA, dirB, meeting_type))
                last_abs = this_abs
                last_met = True
        else:
            last_met = False

        t += dt

        if t > max_t:
            break  # 防止无限循环
    return meetings

if __name__ == "__main__":
    meetings = find_nth_meeting(10, 8, 1, 3)
    meetings = find_nth_meeting(10, 8, 3, 3)
    print(meetings)
    # meetings = find_nth_meeting(10, 9, 1, 3)
    # meetings = find_nth_meeting(10, 9, 1, 2.5)
    # meetings = find_nth_meeting(10, 6, 1, 2)
    # meetings = find_nth_meeting(20, 6, 2.5, 1)

    for i, (t, pA, pB, sA, sB, dirA, dirB, mt) in enumerate(meetings, 1):
        print(f"第{i}次相遇：时间={t:.4f}s，相遇时A距离甲={pA:.4f}m，相遇时B距离甲={pB:.4f}m，A行走了{sA:.4f}m，B行走了{sB:.4f}m，A方向：{dirA}，B方向：{dirB}，类型={mt}")

    # 问题：
    # A、B两只蚂蚁在相距S米的甲、乙两地往返搬运粮食，A从甲地出发，B从乙地同时出发，A的速度是a米/秒，B的速度是b米/秒。当两只蚂蚁第n次相遇时（注：相遇包括迎面相遇和同向追上两种情况，蚂蚁搬运粮食的时间忽略不计）（1）A/B蚂蚁走了多少米？（结果请保留1位小数）（2）此时A、B两只蚂蚁是同向还是反向行走？（请回答"同向"或者"反向"）。最终的回答格式形如："20.0,同向"