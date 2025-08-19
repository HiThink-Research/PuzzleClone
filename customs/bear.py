from collections import deque

def BFS_cal(start, target, colors):
    visited = {}
    queue = deque()
    queue.append((start, 0))  # (当前熊数, 步数)
    visited[start] = (None, None)  # {current: (prev_state, button)}

    while queue:
        current, steps = queue.popleft()

        if current == target:
            break

        # 操作 1：翻倍（最多不能超过 target）
        next_b = current * 2
        if next_b <= target and next_b not in visited:
            visited[next_b] = (current, '1')
            queue.append((next_b, steps + 1))

        # 操作 2：减1（必须 >0）
        next_r = current - 1
        if next_r >= 0 and next_r not in visited:
            visited[next_r] = (current, '2')
            queue.append((next_r, steps + 1))

    # 回溯路径
    path = []
    curr = target
    while curr != start:
        prev, button = visited[curr]
        path.append(button)
        curr = prev
    path.reverse()
    seq = []
    for item in path:
        seq.append(colors[int(item)-1])
    # print(seq)
    return len(path), ','.join(seq)
    # return 1,2

# 执行
if __name__ == '__main__':
    steps, sequence = BFS_cal(5, 37, ['红色','蓝色'])
    print(f"最少要点击 {steps} 次按钮")
    print(f"按钮顺序为：{sequence}")