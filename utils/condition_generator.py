'''
该模块用来生成不同模板问题的约束条件
'''


from z3 import *
from utils.auxiliary_operator import CustomSym


def gen_event_count_condition(events, fact, num=0):
    """
    Return conditions where at most, least, or exactly num events are true in the event array.

    :param events: Array of type z3.Bool.
    :param fact: Objective fact about the events: "most" (at most), "least" (least), or "equal" (exactly).
    :param num: The quantity, which must be greater than 0 and less than or equal to the length of the event list.
    """

    if type(events) == dict:
        events = events.values()
    elif isinstance(events, CustomSym):
        events = events.to_list()
        
    n = len(events)
    
    # 检查 num 的范围
    if num <= 0:
        num = 0
    elif num > n:
        num = n
    
    if fact == "most":
        return [Sum([If(v, 1, 0) for v in events]) <= num]

    if fact == "least":
        return [Sum([If(v, 1, 0) for v in events]) >= num]

    if fact == "equal":
        return [Sum([If(v, 1, 0) for v in events]) == num]

    if fact == "distinct":
        return [Distinct(*events)]

def gen_multi_event_count_condition(events, op, target):
    """
    Generate conditions based on a multidimensional event array.

    :param events: Array of events, where each element is a symbol.
    :param op: Operator, such as wc (word count).
    :param target: The target value for the condition.
    """
    # events = zip(*events)
    # print(events)
    if op == "wc":
        constraints = []
        group_counts = []
        # allowed_counts = [i for i, cnt in enumerate(target) if cnt > 0]

        # 生成每组的真事件数并添加范围约束
        for group in events:
            count = Sum([If(e, 1, 0) for e in group])
            group_counts.append(count)
            # constraints.append(Or([count == k for k in allowed_counts]))  # 每组必须符合允许的计数

        # 添加分布约束
        for i, required in enumerate(target):
            if required < 0:
                raise ValueError(f"Invalid target count at index {i}: {required}")
            if required == 0:
                continue
            
            # 统计实际满足i个真事件的组数
            actual = Sum([If(gc == i, 1, 0) for gc in group_counts])
            constraints.append(actual == required)

        return constraints


if __name__ == "__main__":

    pass

    