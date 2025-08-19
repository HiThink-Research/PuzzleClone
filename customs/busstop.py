from random import randint

def generate_move_direc_list(stop_list):
    res = []
    for i in range(len(stop_list)):
        if i == len(stop_list)-1:
            res.append(stop_list[0])
            continue
        res.append(stop_list[i+1])
    return res

def generate_move_list(num_direc,move_max_buses,move_min_buses):
    
    return [randint(move_min_buses,move_max_buses) for _ in range(num_direc)]

def generate_buses_list(num_busstop,main_buses,normal_max_buses,normal_min_buses):
    return [main_buses] + [randint(normal_min_buses,normal_max_buses) for _ in range(num_busstop-1)]