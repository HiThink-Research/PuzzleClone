def pos(t, S, up_speed, down_speed, initial_direction="down"):
    '''
    计算t时间时运动员距离坡顶距离current_pos、跑过的总距离total_distance，以及当前运动方向direction
    args:
        - up_speed: 上坡速度
        - down_speed: 下坡速度
        - initial_direction: down 表示从坡顶开始下坡，up 表示从坡底开始上坡
    '''
    total_distance = 0
    current_pos = 0 if initial_direction == 'down' else S
    direction = initial_direction  # 'down' 或 'up'
    remaining_time = t
    
    while remaining_time > 0:
        if direction == 'down':
            speed = down_speed
            distance_to_next = S - current_pos
        else:
            speed = up_speed
            distance_to_next = current_pos
        
        time_to_next = distance_to_next / speed if speed != 0 else float('inf')
        
        if time_to_next <= remaining_time:
            remaining_time -= time_to_next
            total_distance += distance_to_next
            if direction == 'down':
                current_pos = S
                direction = 'up'
            else:
                current_pos = 0
                direction = 'down'
        else:
            distance = speed * remaining_time
            total_distance += distance
            if direction == 'down':
                current_pos += distance
            else:
                current_pos -= distance
            remaining_time = 0
    
    return current_pos, total_distance, direction


def find_nth_meeting(n, S, upslope, downhill, initial_direction, dt=0.0001, max_t=1000):
    '''
    upslope、downhill为一个长度为2的数组，分别表示两个运动员在上坡、下坡的速度
    '''
    meetings = []
    t = 0
    last_met = False
    last_abs = S

    while len(meetings) < n or (len(meetings) == n and last_met):
        pA, sA, dirA = pos(t, S, upslope[0], downhill[0], initial_direction[0])
        pB, sB, dirB = pos(t, S, upslope[1], downhill[1], initial_direction[1])
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
    t = 18
    S = 50
    up_speed, down_speed = 5, 10
    print(pos(t, S, up_speed, down_speed, initial_direction="down"))

    upslope = [3, 2]
    downhill = [5, 3]
    initial_direction = ["up", "down"]
    meetings = find_nth_meeting(5, 110, upslope, downhill, initial_direction)
    for i, (t, pA, pB, sA, sB, dirA, dirB, mt) in enumerate(meetings, 1):
        print(f"第{i}次相遇：时间={t:.4f}s，相遇时男距离坡顶A={pA:.4f}m，女距离坡顶A={pB:.4f}m，男行走了{sA:.4f}m，女行走了{sB:.4f}m，男方向：{dirA}，女方向：{dirB}，类型={mt}")

    # 男女运动员同时从A/B点出发
    # 问题：男、女两名田径运动员在长110米的斜坡上练习跑步(坡顶为A，坡底为B)。男运动员从A点出发，女运动员同时从B点出发，他们在A、B之间不停地往返奔跑。如果男运动员上坡速度是每秒3米，下坡速度是每秒5米；女运动员上坡速度是每秒2米，下坡速度是每秒3米。那么两人第2次相遇时（注：相遇包括迎面相遇和同向追上两种情况），（1）此时已经过了多长时间？（单位为秒）（2）男运动员总共走了多少米？以上结果均保留1位小数，最终的回答格式形如："52.1,188.6"