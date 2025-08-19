
import sys
from pathlib import Path

# 获取上级目录的绝对路径并添加到 sys.path
parent_dir = str(Path(__file__).resolve().parent.parent)
sys.path.append(parent_dir)

# 导入 utils 模块中的函数
from utils import faker_utils
from utils import auxiliary_operator
import random

def cal_sports(n,num_list):
    cannot = [n-item for item in num_list]
    return n-sum(cannot)

def cal_min_two_inter(n,num_list):
    return sum(num_list[:2])-n

# generate_random_list(size, ele_type, ele_domain, cond=[], per_ele_domain=None)

if __name__ == '__main__':
    # n_sports = random.randint(1,5)
    # sports = faker_utils.get_faker(n_sports,'sport')
    # n = random.randint(40,80)
    # num_list = [random.randint(10,n-1) for _ in range(n_sports)]
    n_sports = 3
    sports = ['游泳','自行车','乒乓球']
    n = 48
    num_list = [27,33,40]
    # num_list = auxiliary_operator.generate_random_list(n_sports, 'int', [10,n-1], cond=["lambda num_list: sum(num_list)<=n-1"])
    
    print('、'.join(list(map(lambda x, y: f"{x}人会{y}", num_list, sports))))
    
    res = cal_sports(n,num_list)
    both_two = cal_min_two_inter(n,num_list)
    print(n,sports,num_list,res,both_two)