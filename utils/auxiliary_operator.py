"""
Auxiliary Operator 

This module provides functionality for constructing symbols and conditions, including:
1. Symbol wrapper (CustomSym)
2. Condition wrapper (CustomCond)
3. Utility functions for generating random indices, evaluating conditions, and managing symbol metadata.
"""

import string
import itertools
import random
from z3 import *
import re
import numpy as np
import ast
import contextvars
from typing import Optional, List, Union, Any, Dict
from itertools import product
import copy

class CustomSym(dict):
    """
    Symbol wrapper class supporting structured symbol modeling and Z3 variable integration

    Attributes:
        name (str): Symbol group name, used as symbol prefix

        source (Dict[str, List[Union[str, int]]]): Data source

            - Example: {"Grade": [1,2,3], "Subject": ["Math", "Chinese"]}

        attr (Optional[List[str]]): Attributes

            - Example: ["Score", "Difficulty"]

        type (Union[str, List[str]]): Variable type definition, supports:

            - 'Int' (default)/'Bool'/'Real'/'Float'/'BitVec'

            - Type list (needs equal length when attr exists)

        desc (Optional[Union[str, List[str]]]): Description template system

            - Single attribute mode: "Grade variable description"

            - Multi-attribute mode: ["Score description", "Difficulty description"]

    Examples:
        >>> grade_system = CustomSym(
        ...     name="Grade",
        ...     source={"Level": ["A", "B"]},
        ...     attr=["Score"],
        ...     type="Int"
        ... )
        >>> grade_system[("A")]["Score"]  # Returns Int('Grade_A_Score')
    """
    def __init__(
        self,
        name: str,
        source: Dict[str, List[Union[str, int]]],
        attr: Optional[List[str]] = None,
        type: Union[str, List[str]] = "Int",
        desc: Optional[Union[str, List[str]]] = None,
    ):
        super().__init__()
        self._name = name
        self._source = source
        self._attr = attr
        self._type = type
        self._desc = desc
        self._dimension = len(source)
        self._categories = list(source.keys())
        
        #------ 初始化处理流程 ------
        # 生成笛卡尔积作为复合键
        self._keys = list(product(*source.values()))
        
        # Z3变量创建逻辑
        if attr is None:
            #-- 单属性模式 --
            for key in self._get_key_variants():
                var_name = f"{name}_{self._key_to_str(key)}"
                if isinstance(type, str):
                    self[key] = self._create_z3_var(var_name, type)
                    # 为每个变量存储配置
                    self._store_var_config(var_name, key, None)
                else:
                    raise ValueError("When attr is None, type must be str")
        else:
            #-- 多属性模式 --
            # 校验类型列表长度匹配
            if not isinstance(type, list) or len(type) != len(attr):
                raise ValueError("属性类型列表长度需与属性列表一致")
            
            # 构建复合属性字典
            for key in self._get_key_variants():
                key_str = self._key_to_str(key)
                self[key] = {}
                for a, t in zip(attr, type):
                    var_name = f"{name}_{key_str}_{a}"
                    self[key][a] = self._create_z3_var(var_name, t)
                    # 分属性存储元数据
                    self._store_var_config(var_name, key, a)

    def _store_var_config(self, var_name: str, key, attr: Optional[str]):
        """
        Store variable configuration metadata
        Parameters:
            var_name: Z3 variable name (e.g., Grade_A_Math_Score)
            key: Tuple (e.g., ('A', 'Math'))
            attr: Current processing attribute name (e.g., 'Score')
        Storage Format:
            >>> {
            ...    "p": {  # Dimension parameters
            ...         "grade": "A",
            ...         "dim_1": {
            ...             "category": "Subject",
            ...             "value": "Math",
            ...             "init_values": ["Math", "Chinese"]
            ...         }
            ...     },
            ...     "type": "int",  # Variable type
            ...     "desc": "Score variable description"  # Original template
            ... }
        """
        # 维度值字典构建
        if isinstance(key, (tuple, list)):
            p_values = {
                self._categories[i]: key[i] 
                for i in range(len(self._categories))
            }
        else:
            p_values = {self._categories[0]: key}

        # 类型与描述获取
        current_type = (
            self._type if attr is None 
            else self._type[self._attr.index(attr)]
        )
        desc_template = self._get_var_desc(key, attr)

        # 元数据组装
        config = {
            "p": p_values,
            "type": current_type,
            "desc": desc_template
        }
        
        # 多维度附加信息
        if isinstance(key, tuple) and len(key) > 1:
            config["p"].update({
                f"dim_{i}": {
                    "category": cat,
                    "value": key[i],
                    "source_values": self._source[cat]
                }
                for i, cat in enumerate(self._categories[1:], start=1)
            })
        
        # 调用全局存储方法
        store_sym_config(
            self[key][attr] if attr is not None else self[key], 
            config
        )

    def _get_var_desc(self, key, attr: Optional[str]) -> Optional[str]:
        """
        Extract variable description template
        Returns:
            str/None: Original description template; placeholder will be kept
        Example:
            Input key=('12', 'Math'), attr='Score'
            Return possible template: "the score of the student in Grade {{dim_0}} and Subject {{dim_1}}"
            
        仅获取描述模板（不计算具体值）
        """
        if self._desc is None:
            return None
            
        if attr is None:
            return self._desc if isinstance(self._desc, str) else None
        else:
            if not isinstance(self._desc, list):
                return None
            attr_index = self._attr.index(attr)
            return self._desc[attr_index] if attr_index < len(self._desc) else None

    def _key_to_str(self, key) -> str:
        """
        Key value serialization method
        Rules:
            - Single-dimensional key: direct stringification ("A")
            - Multi-dimensional key (for tuples): underscore connection ("A_Math")
        Returns:
            Standardized key string representation
        """
        if isinstance(key, tuple):
            return "_".join(key)
        return str(key)

    def _get_key_variants(self):
        """
        Get standardized key representation
        Methods:
            - Single dimension: returns first-level key list ["A", "B"]
            - Multi-dimension: returns tuple key list [("A", "Math"), ...]
        """
        if self._dimension == 1:
            return [k[0] for k in self._keys]
        return self._keys

    def _create_z3_var(self, name: str, type_str: str) -> Any:
        """
        Z3 variable generation

        Parameters:
            type_str: Type identifier (case-insensitive)
                - 'int' → z3.Int
                - 'bool' → z3.Bool
                - 'real' / 'float' → z3.Real
                - 'bv*' → Bit vector (e.g., bv16 → 16-bit)

        Returns:
            Z3 variable instance

        Raises:
            ValueError: When encountering unsupported type identifiers
        """
        type_str = type_str.lower()
        if type_str == "int":
            return Int(name)
        elif type_str == "bool":
            return Bool(name)
        elif type_str == "real" or type_str == "float":
            return Real(name)
        elif type_str == "bitvec" or type_str.startswith("bv"):
            if type_str == "bitvec":
                return BitVec(name, 8)  # 默认8位
            else:
                # 处理类似"bv16"的格式
                try:
                    bits = int(type_str[2:])
                    return BitVec(name, bits)
                except:
                    return BitVec(name, 8)
        else:
            raise ValueError(f"Unsupported Z3 type: {type_str}")

    def __len__(self):
        return len(self._keys)

    def __iter__(self):
        return iter(self.to_list())

    def get(self, attr: str) -> List[Any]:
        """
        Batch retrieve all variable instances of the specified attribute.

        Parameters:
            attr: Target attribute name

        Returns:
            A list of attribute variables/instances arranged in the order of initialization.

        Raises:
            ValueError: When attr does not exist or is currently in single-attribute mode.
        """
        if self._attr is None:
            raise ValueError("单属性模式请直接使用values()遍历")
        
        if attr not in self._attr:
            raise ValueError(f"不存在的属性 '{attr}'")
        
        return [v[attr] for v in self.values()]

    def to_list(self) -> Union[List[Any], List[List[Any]]]:
        """
        Output a list of Z3 symbols.

        Returns
        
        - Single attribute: [Var1, Var2, ...]

        - Multiple attributes: [[Attribute1 variable list], [Attribute2 variable list], ...]

        Example:
            >>> # Example of multiple attributes and multiple dimensions
            ... [
            ...     [Grade_A_Math_Score, Grade_A_Chinese_Score, ...],  # Score attribute
            ...     [Grade_A_Math_Diff, Grade_A_Chinese_Diff, ...]    # Difficulty attribute
            ... ]
        """
        if self._attr is None:
            return list(self.values())
        return [
            [v[attr] for v in self.values()] 
            for attr in self._attr
        ]

    def __getitem__(self, key):
        """
        Enhanced accessing values by key in dict

        Features:
            - Automatically handles single-dimensional key wrapping
            - Enforces multi-dimensional keys to be accessed in tuple form

        Raises:
            KeyError: Multi-dimensional access not using tuple
        """
        if self._dimension == 1:
            # 自动化解包单维元组
            return super().__getitem__(
                key[0] if isinstance(key, tuple) else key
            )
        
        if not isinstance(key, tuple):
            raise KeyError("多维键必须使用tuple形式访问")
        
        return super().__getitem__(key)

class CustomCond(str):
    """
    Condition wrapper class for structured condition modeling

    Extends metadata support based on the standard string class to achieve:
    - Binding of conditional expressions to descriptive text
    - Domain identification classification
    - Additional data payload

    Attributes:
        domain (int): Number of expressions
        data (list): Additional data payload

    Inherits:
        All native functionalities and methods of str

    Example:
        >>> cond = CustomCond(domain=1, desc="Score should be greater than 60", data=[[...], [...]])
        >>> print(cond)  # "Score should be greater than 60"
        >>> cond.domain  # 1
    """
    def __new__(cls, domain: int = 0, desc: str = "", data: list = None):
        # 确保字符串实例化正确
        instance = super().__new__(cls, desc)
        instance.domain = domain
        instance._desc = desc
        instance.data = data if data is not None else []
        return instance
    
    @property
    def desc(self):
        """str: Natural langauge description"""
        return str(self)
    
    @desc.setter
    def desc(self, value):
        self.__dict__.update(_desc=value, data=self.data)  # 由于str是不可变类型，这里需要重新创建实例

    # 核心字符串协议实现
    def __str__(self):
        return self._desc
    
    def __add__(self, other):
        return CustomCond(self._desc + str(other), self.data.copy())
    
    def __iadd__(self, other):
        self._desc += str(other)
        return self
    
    def __radd__(self, other):
        return CustomCond(str(other) + self._desc, self.data.copy())

_sym_config = {} # 储存所有symbol的相关信息，包括其依赖的变量p、描述方式等
_user_context_global = {}
_user_context_local = {}
cnt = 0  # 全局计数器，用于生成英文字母时的序列控制

def store_sym_config(key, value):
    if isinstance(key, (list, tuple)):
        _sym_config[_convert_to_hashable(key)] = value
    else:
        _sym_config[key] = value

def set_global_context(ctx):
    global _user_context_global
    _user_context_global = ctx

def set_local_context(ctx):
    global _user_context_local
    _user_context_local = ctx

def _convert_to_hashable(obj):
    """Recursively convert lists/tuples to tuples to ensure hashability."""
    if isinstance(obj, (list, tuple)):
        return tuple(_convert_to_hashable(e) for e in obj)
    else:
        return obj
def get_p(sym, p):
    """Return the value of the binded variable named 'p' for the symbol 'sym'; if 'sym' is a list, do this for each element."""
    # if isinstance(sym, (list, tuple)):
    #     return type(sym)(get_p(item, p) for item in sym)
    key = _convert_to_hashable(sym)
    # print(key, _sym_config)
    if key in _sym_config:
        return _sym_config.get(key)["p"][p]
    elif isinstance(sym, (list, tuple)):
        return type(sym)(get_p(item, p) for item in sym)
    else:
        raise Exception(f"Cannot find the p of {sym}")

def get_desc(sym):
    """Return the description of the symbol 'sym'; if 'sym' is a list, do this for each element."""
    # if isinstance(sym, (list, tuple)):
    #     return type(sym)(get_desc(item) for item in sym)
    key = _convert_to_hashable(sym)
    # print(key, _sym_config)
    if key in _sym_config:
        return _sym_config[key]["desc"]
    elif isinstance(sym, (list, tuple)):
        return type(sym)(get_desc(item) for item in sym)
    else:
        raise Exception(f"Cannot find the description of {sym}")

def get_data(cond):
    """Return the random data bound to the condition 'sym'; if 'sym' is a list, do this for each element."""
    # if isinstance(sym, (list, tuple)):
    #     return type(sym)(get_desc(item) for item in sym)
    key = _convert_to_hashable(cond)
    # print(key, _sym_config)
    if key in _sym_config:
        return _sym_config[key]["data"]
    elif isinstance(cond, (list, tuple)):
        return type(cond)(get_data(item) for item in cond)
    else:
        raise Exception(f"Cannot find the binded data of {cond}") 
    
def get_value(sol, vars):
    '''
    Return the values of 'vars' in the solution 'sol' of the z3-solver.
    '''
    if isinstance(vars, (list, tuple, dict)):
        return [get_value(sol, item) for item in list(vars)]
    else:
        res = sol[vars.decl()]
        if isinstance(res, BoolRef):
            return is_true(res)  # 确保布尔值正确转换
        elif isinstance(res, IntNumRef):
            return res.as_long()  # 将Z3整数转为Python int
        elif isinstance(res, RatNumRef):
            # Z3 有理数 → Python float（例如 Real 类型的解）
            decimal_str = res.as_decimal(10)
            # 去除末尾的问号（如果存在）
            if decimal_str.endswith('?'):
                decimal_str = decimal_str[:-1]
            return float(decimal_str)
        elif isinstance(res, AlgebraicNumRef):
            # 处理代数数（罕见情况，可能需要近似）
            return float(res.approx(10).as_decimal(10)[:-1])  # 取 10 位小数
        else:
            return res

def get_var_name(z3_var):
    """
    Return the string representation of the variable name of the z3 variable.
    """
    return z3_var.decl().name()

def is_option_valid(opt, formula, cond, result, env):
    compiled_formula = compile(formula, "<string>", "eval")
    check = all if cond == 'all' else any
    try:
        if check(eval(compiled_formula, {**env, "_model": _model, "_opt": opt}) for _model in eval("_solutions", env)) != result:
            return False
    except Exception as e:
        print("Failed to evaluate the options.", opt, formula, cond, result, e)
        raise e
    return True

def generate_random_indices(choose, amount, domain, domain_cond=True, dim=1, dim_cond=[], custom_cond=[], order=[], duplicate=[], env={}):
    """
    Generate random index combinations.

    Parameters:
        choose (List[any]): Number of available elements in each data source, similar to DerivedSymbol.source.
        amount (List[int]): Number of elements to choose in each data source, similar to DerivedSymbol.amount.
            Example: ["2", "1"] indicates selecting 2 from the first data source and 1 from the second source.
        domain (int): Total number of groups to select, similar to DerivedSymbol.domain.
        domain_cond (bool): Same as DerivedSymbol.domain_cond, default True.
        dim (int): Number of dimensions in each symbol, similar to DerivedSymbol.dim.
        dim_cond (List[List[int]]): Same as DerivedSymbol.dim_cond.
        custom_cond (List[Dict]): List of custom constraints, each dictionary contains: (Same as DerivedSymbol.custom_cond)
            - scope: Level of application ('dim'/'domain').
            - fields: List of indices of the involved data sources.
            - constraint: Logical expression for constraints (callable object).
        order (List[bool]): Configuration of arrangement for each dimension. Same as DerivedSymbol.order.
            - True: Arrangement (considering order).
            - False: Combination (not considering order).
        duplicate (List[bool]): Initialization repetition rules. Same as DerivedSymbol.duplicate.
            - True: Allow repeated selections.
            - False: Prohibit repetition.
        env (Dict): Importing the environment variables from code generated by the translator. Used for evaluating some conditional expressions in custom_cond.

    Returns:
        tuple: (Selected indices, Formatted selected indices)
        
            - Example: ([[[1, 2], [3]], [[4, 5], [6]]], ["__1__, __2__", "__3__"])

            - Note: The formatted indices are for configuration purposes, not for direct use in the program. In config files, strings that start and end with "__" are considered as indices rather than values.

    Raises:
        AssertionError: Raised when parameter lengths do not match.
        Exception: Raised when unable to generate valid combinations.

    Implementation Process:
        1. Parameter validation and initialization.
        2. Generate a base pool of combinations based on the provided choose and amount.
        3. Handling custom conditions.
    """
    assert(len(choose) == len(amount)) 

    if order is None or order == []:
        order = [True] * len(choose)
    if duplicate is None or duplicate == []:
        duplicate = [False] * len(choose)
    assert len(order) == len(choose)
    assert len(duplicate) == len(choose)
    choose_lens = [len(item) if isinstance(item, list) else item for item in choose]
    ran = [list(range(0, item)) for item in choose_lens]
    subdim = len(choose)

    # 定义生成选项池的辅助函数
    def generate_pool(j, amount_j):
        if order[j]:
            if duplicate[j]:
                pool = itertools.product(ran[j], repeat=amount_j)
            else:
                pool = itertools.permutations(ran[j], amount_j)
        else:
            if duplicate[j]:
                pool = itertools.combinations_with_replacement(ran[j], amount_j)
            else:
                pool = itertools.combinations(ran[j], amount_j)
        return [list(p) for p in pool]

    # 第一步处理：先处理dim conditions
    if len(dim_cond) == 0:
        dim_cond = [list(range(subdim))]
    flat_dim_cond = [element for row in dim_cond for element in row]
    assert(len(set(flat_dim_cond)) == len(flat_dim_cond)) # 验证dim_cond不能有重复元素
    combs = []
    for c in dim_cond:
        pools_per_dim = [generate_pool(j, amount[j]) for j in c] # 3维: len(c) * (permutation_num * amount)
        pool = [[list(item) for item in prod_tuple] for prod_tuple in itertools.product(*pools_per_dim)] # 3维 product_num * len(c) * amount
        comb_dim = [[list(comb_item) for comb_item in comb] for comb in itertools.combinations(pool, dim)] # 4维 comb_num * dim * (len(c) * amount)
        combs.append(list(comb_dim)) # 5维 len(dim_cond) * comb_num * dim * (len(c) * amount)
    combs = list(itertools.product(*combs)) # 5维 product_num' * len(dim_cond) * dim * (len(c) * amount)
    combs = [[subitem for subitem in item] for item in combs]  # Remove outer tuples
    # combs = np.array(combs).tolist()
    combs_new = [[[None for _l in range(subdim)] for _k in range(dim)] for i in range(len(combs))]
    for i in range(len(combs)):
        assert(len(combs[i]) == len(dim_cond))
        for j in range(len(combs[i])):
            assert(len(combs[i][j]) == dim)
            for k in range(dim):
                # 先合并倒数第二维
                record_per_dim = combs[i][j][k]
                new_record_per_dim = [None for _ in range(subdim)]
                # print(i, j, k, record_per_dim, len(dim_cond[j]), len(record_per_dim))
                # assert(len(dim_cond[j]) == len(record_per_dim))
                for l in range(len(dim_cond[j])):
                    field_idx = dim_cond[j][l]
                    new_record_per_dim[field_idx] = copy.deepcopy(record_per_dim[l])
                # print("Before: ", combs[i][j][k], new_record_per_dim, combs[1][0][0])
                # combs[i][j][k] = copy.deepcopy(new_record_per_dim) # 5维 product_num' * len(dim_cond) * dim * subdim * amount
                for l in range(subdim):
                    if new_record_per_dim[l] is not None:
                        combs_new[i][k][l] = new_record_per_dim[l]

    # 第二步处理custom conditions
    custom_dim_cond = list(filter(lambda item: item['scope'] == 'dim', custom_cond))
    custom_domain_cond = list(filter(lambda item: item['scope'] == 'domain', custom_cond))
    custom_option_cond = list(filter(lambda item: item['scope'] == 'option', custom_cond))
    def source_filter(candidate_comb): # 先对已经能判断的dim类custom condition进行一遍预过滤
        ok = True
        # print(candidate_comb)
        for cond in custom_dim_cond:
            if set(cond["fields"]).issubset(set(flat_dim_cond)): # 如果当前cond涉及到的fields全部已经随机过，执行过滤
                l = []
                for row in candidate_comb:
                    l.append([item for idx, item in enumerate(row) if idx in cond["fields"]])
                func = eval(cond["constraint"])
                # print(l, func(l))
                if not func(l):
                    ok = False
        return ok
    combs_new = list(filter(source_filter, combs_new))


    # 计算剩余dim类custom condition中未处理的fields
    field_idxs = set()
    for cond in custom_dim_cond:
        if not set(cond["fields"]).issubset(set(flat_dim_cond)): # 如果当前cond涉及到的fields全部未随机过，先进行随机
            field_idxs |= set(cond["fields"])
    field_idxs -= set(flat_dim_cond) # 剩余的为尚未随机过的fields
    field_idxs = list(field_idxs)
    # 对剩余dim类custom condition中未处理的fields进行随机，与之前的结果合并
    if len(field_idxs) > 0:
        pools_per_dim = [generate_pool(j, amount[j]) for j in field_idxs] # 3维: len(field_idxs) * (permutation_num * amount)
        pool = [[list(item) for item in prod_tuple] for prod_tuple in itertools.product(*pools_per_dim)] # 3维 product_num * len(field_idxs) * amount
        combs = [[list(comb_item) for comb_item in comb] for comb in itertools.product(pool, repeat=dim)] # 4维 comb_num * dim * (len(field_idxs) * amount)
        for i in range(len(combs)):
            assert(len(combs[i]) == dim)
            for j in range(len(combs[i])):
                # 先合并倒数第二维
                record_per_dim = combs[i][j]
                new_record_per_dim = [None for _ in range(subdim)]
                assert(len(field_idxs) == len(record_per_dim))
                for l in range(len(field_idxs)):
                    field_idx = field_idxs[l]
                    new_record_per_dim[field_idx] = copy.deepcopy(record_per_dim[l])
                combs[i][j] = new_record_per_dim # 4维 comb_num * dim * subdim * amount
        
        combs = list(itertools.product(combs_new, combs)) # 5维 product_num' * 2 * dim * subdim * amount
        combs_new = [[[None for _l in range(subdim)] for _k in range(dim)] for i in range(len(combs))] # 4维 product_num' * dim * subdim * amount
        # 再对dim_cond进行合并
        for i in range(len(combs)):
            for k in range(dim):
                merged = [None for _ in range(subdim)]
                for l in range(subdim):
                    for j in range(2):
                        if combs[i][j][k][l] is not None:
                            merged[l] = combs[i][j][k][l]
                combs_new[i][k] = merged 

        # 二次过滤
        flat_dim_cond = list(set(flat_dim_cond) | set(field_idxs))
        combs_new = list(filter(source_filter, combs_new)) # 4维 product_num' * dim * subdim * amount

    # 第三步：随机选取domain组，并将剩余未随机的部分随机化
    def is_valid(combs, conds):
        # 判断选出的部分是否满足custom domain condition
        for cond in conds:
            l = []
            if 'fields' in cond:
                l = [  [ [comb_dim[i] for i in cond['fields']] for comb_dim in comb ] for comb in combs]
            else:
                l = copy.deepcopy(combs)
            if 'constraint' in cond:
                if isinstance(env, dict):
                    constraint = eval(cond['constraint'], {**env, **globals()})
                else:  
                    constraint = eval(cond['constraint'])
                
                # Handle both function and boolean cases
                if isinstance(constraint, bool):
                    func = lambda l: constraint  # Create a function that always returns the boolean
                else:
                    func = constraint  # It's already a function
            else:
                func = lambda l: len(l) == len(set(l))
            if not func(to_hashable(l)):
                return False
        return True
    
    
    
    max_attempts = 1000  # 设定最大尝试次数

    # 原有条件检查（确保domain_cond为True时有足够元素）
    if domain_cond and domain and len(combs_new) < domain:
        raise Exception("Fail to generate sufficient random indices to fulfill all conditions")

    valid = False
    res_combs = None

    for _ in range(max_attempts):
        # 生成候选组合
        if domain_cond:
            current_candidates = random.sample(combs_new, domain)
        else:
            current_candidates = random.choices(combs_new, k=domain)
        
        # 深拷贝避免污染原始数据
        temp_candidates = copy.deepcopy(current_candidates)
        
        # 处理None值（随机填充）
        for comb in temp_candidates:
            for comb_dim in comb:
                assert len(comb_dim) == subdim
                for i in range(subdim):
                    if comb_dim[i] is None:
                        comb_dim[i] = list(random.sample(ran[i], amount[i]))
        
        # 有效性检查
        # if is_option_valid(temp_candidates, custom_option_cond, choose, env) and is_valid(temp_candidates, custom_domain_cond):
        #     res_combs = temp_candidates
        #     valid = True
        #     break

        if len(custom_option_cond) > 0: # 外部场景是生成选择题选项
            assert(len(custom_option_cond) == 1) # 选择题只能有一个验证公式
            cond = custom_option_cond[0]
            # 将下标带入实际的符号，用于后续判断
            _opts = []
            for comb in temp_candidates:
                assert(len(comb) == 1) # 选项的dim应当为1
                _opts.append([[choose[i][j] for j in comb[0][i]] for i in range(len(comb[0]))])
            
            if all([is_option_valid(_opt, cond["formula"], cond["cond"], cond["result"], env) for _opt in _opts]) and is_valid(temp_candidates, custom_domain_cond):
                res_combs = temp_candidates
                valid = True
                break
        else: # 外部场景是生成condition
            if is_valid(temp_candidates, custom_domain_cond):
                res_combs = temp_candidates
                valid = True
                break

    if not valid:
        raise Exception(f"Failed to generate valid combs after {max_attempts} attempts")

    # 当dim为1时，简化该维
    if dim == 1:
        for idx in range(len(res_combs)):
            res_combs[idx] = res_combs[idx][0]

    def res_to_str(arr):
        if type(arr) == list:
            return [res_to_str(arr[idx]) for idx in range(len(arr))]
        else:
            return f"__{arr}__"

            
    res_combs_str = res_to_str(res_combs)
    # print(res_combs)
    return res_combs, res_combs_str
    
    

def generate_letters(n, lang='en'):
    """
    Generate a set of letter identifiers.

    Parameters:
        n (int): The number of identifiers to generate.
        lang (str): Language option, 'en' for English (default), other values for Chinese.

    Returns:
        list: In English mode, returns a list formatted like ['A1', 'A2', ...].
        str: In Chinese mode, returns a string containing the specified number of characters.

    Description:

    - English mode: Uses a looped sequence of letters A-Z combined with numbers (resets letters every 26 iterations).
    
    - Chinese mode: Uses a fixed alphabet "甲乙丙丁..." to return the first n characters.
    """
    global cnt
    if lang=='en':
        # 计算当前起始字母：按26字母循环（A=0, B=1,... Z=25）
        base = string.ascii_uppercase[cnt % 26]
        cnt += 1  # 更新全局计数器
        # 生成字母+数字序列（如 ['A1', 'A2', ..., 'An']）
        return [base + str(i + 1) for i in range(n)]
    else:
        CN_names = "甲乙丙丁戊己庚辛壬癸子丑寅卯辰巳午未申酉戌亥"
        # 返回前n个汉字组成的字符串
        return CN_names[:n]
        

def generate_var_names(n):
    """
    Return an array of default variable names with a length of n. 

    - When n <= 3, the order is x, y, z.
    - When 4 <= n <= 11, the order is p, q, r, ... .
    - When n > 11, the order is x1, x2, ... .
    """
    if n <= 3:
        return ['x', 'y', 'z'][:n]
    elif 3 < n <= 11:
        return ['p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z'][:n]
    else:
        return [f"x{i}" for i in range(1, n+1)]

def generate_random_list(size, ele_type, ele_domain, cond=[], per_ele_domain=None):
    """
    Return a random array with element-level range control.

    Parameters:
        size (int): Length of the array.
        ele_type (str): Type of elements in the array, such as 'int', 'bool', 'enum', 'float'.
        ele_domain (list or tuple): Global value range for elements (used when element-level range is not defined).
        cond (list): List of conditions that elements must satisfy, each as a function string, e.g., "lambda l: sum(l) == 5".
        per_ele_domain (list, optional): Independent value range for each element, must have the same length as size. Can be None or contain None values, indicating that the element should use the global value range.
    """
    # 参数有效性检查
    if not isinstance(size, int) or size <= 0:
        raise ValueError("size must be a positive integer")
    
    supported_types = ['int', 'bool', 'float', 'enum']
    if ele_type not in supported_types:
        raise ValueError(f"Unsupported element type: {ele_type}")
    
    # 验证全局值域 ele_domain
    if ele_type in ['int', 'float']:
        if len(ele_domain) < 2:
            raise ValueError("ele_domain must have at least two elements for int/float types")
        if ele_domain[0] > ele_domain[1]:
            raise ValueError("ele_domain[0] must be <= ele_domain[1] for int/float types")
    elif ele_type in ['bool', 'enum']:
        if not isinstance(ele_domain, (list, tuple)) or len(ele_domain) == 0:
            raise ValueError(f"ele_domain must be a non-empty list/tuple for {ele_type} type")
    
    # 检查 per_ele_domain 参数 (如提供)
    if per_ele_domain is not None:
        if len(per_ele_domain) != size:
            raise ValueError("per_ele_domain length must match size")
        
        # 验证每个元素的值域格式（忽略None值）
        for i, domain in enumerate(per_ele_domain):
            if domain is None:
                continue  # 该元素使用全局值域
                
            if ele_type in ['int', 'float']:
                if not isinstance(domain, (list, tuple)) or len(domain) < 2:
                    raise ValueError(f"Invalid domain for index {i}: must be list/tuple with [min, max]")
                if domain[0] > domain[1]:
                    raise ValueError(f"Invalid domain for index {i}: min must be <= max")
            elif ele_type in ['bool', 'enum']:
                if not isinstance(domain, (list, tuple)) or len(domain) == 0:
                    raise ValueError(f"Invalid domain for index {i}: must be non-empty list/tuple")
    
    # 转换条件字符串为函数
    conditions = []
    for c in cond:
        try:
            # 假设存在上下文变量 _user_context_global 和 _user_context_local
            conditions.append(eval(c, {**(_user_context_global or {}),**(_user_context_local or {}),**globals()}))
        except:
            raise ValueError(f"Invalid condition string: {c}")
    
    # 生成满足条件的列表
    while True:
        # 生成候选列表
        lst = []
        for i in range(size):
            # 确定当前元素的值域（优先使用元素级值域，None表示使用全局值域）
            if per_ele_domain is not None and per_ele_domain[i] is not None:
                current_domain = per_ele_domain[i]
            else:
                current_domain = ele_domain
            
            # 根据元素类型生成随机值
            if ele_type == 'int':
                element = random.randint(current_domain[0], current_domain[1])
            elif ele_type == 'bool':
                element = random.choice(current_domain)
            elif ele_type == 'float':
                element = round(random.uniform(current_domain[0], current_domain[1]), 2)
            elif ele_type == 'enum':
                element = random.choice(current_domain)
            else:
                raise ValueError("Unsupported element type")
            lst.append(element)
        
        # 检查条件
        satisfied = True
        for cond_func in conditions:
            try:
                if not cond_func(lst):
                    satisfied = False
                    break
            except Exception as e:
                satisfied = False
                break
        if satisfied:
            return lst
        
import random

def generate_random_list_with_total(size, ele_domain, total, per_ele_domain=None):
    """
    Return a random integer array with a total sum of total, supporting element-level range control.

    Parameters:
        size (int): Length of the array.
        ele_domain (list or tuple): Global value range for elements (two integers: [min, max]).
        total (int): The total sum of all elements in the array.
        per_ele_domain (list, optional): Independent value range for each element, must have the same length as size. Can be None or contain None values, indicating that the element should use the global value range.
    """
    # 参数有效性检查
    if not isinstance(size, int) or size <= 0:
        raise ValueError("size must be a positive integer")
    
    # 检查全局值域格式
    if not isinstance(ele_domain, (list, tuple)) or len(ele_domain) != 2 or not isinstance(ele_domain[0], int) or not isinstance(ele_domain[1], int):
        raise ValueError("ele_domain must be a list/tuple of two integers")
    min_global, max_global = ele_domain
    if min_global > max_global:
        raise ValueError("ele_domain[0] must be <= ele_domain[1]")
    
    # 检查 per_ele_domain 参数 (如提供)
    min_arr = []
    max_arr = []
    if per_ele_domain is not None:
        if len(per_ele_domain) != size:
            raise ValueError("per_ele_domain length must match size")
        for i, domain in enumerate(per_ele_domain):
            if domain is None:
                min_arr.append(min_global)
                max_arr.append(max_global)
            else:
                if not isinstance(domain, (list, tuple)) or len(domain) != 2 or not isinstance(domain[0], int) or not isinstance(domain[1], int):
                    raise ValueError(f"Invalid domain for index {i}: must be list/tuple of two integers")
                if domain[0] > domain[1]:
                    raise ValueError(f"Invalid domain for index {i}: min must be <= max")
                min_arr.append(domain[0])
                max_arr.append(domain[1])
    else:
        min_arr = [min_global] * size
        max_arr = [max_global] * size

    # 计算最小总和与最大总和
    min_sum = sum(min_arr)
    max_sum = sum(max_arr)
    if total < min_sum or total > max_sum:
        raise ValueError(f"total={total} is out of range. It must be in [{min_sum}, {max_sum}]")

    R = total - min_sum  # 需要分配的总增量
    # 如果无需增量，直接返回最小值列表
    if R == 0:
        return min_arr

    # 计算每个元素的可分配空间
    space_arr = [max_arr[i] - min_arr[i] for i in range(size)]
    total_space = sum(space_arr)
    if total_space < R:
        raise RuntimeError("Internal error: total_space < R")

    # 基础分配: 按比例分配基础增量
    increment = [0] * size
    base_assigned = 0
    for i in range(size):
        if total_space > 0:  # 避免除零
            base_inc = (space_arr[i] * R) // total_space
        else:
            base_inc = 0
        increment[i] = base_inc
        base_assigned += base_inc

    rem = R - base_assigned  # 剩余待分配增量

    # 如果还有剩余增量，则进行随机分配
    if rem > 0:
        # 初始化剩余空间列表
        remaining_space = [space_arr[i] - increment[i] for i in range(size)]
        # 创建一个权重数组，用于随机选择
        weights = remaining_space[:]
        total_remaining = sum(remaining_space)
        
        if total_remaining < rem:
            raise RuntimeError("Internal error: total_remaining < rem")
        
        # 批量分配剩余增量
        for _ in range(rem):
            # 根据权重随机选择一个索引
            r = random.randint(1, total_remaining)
            acc = 0
            for i in range(size):
                acc += weights[i]
                if acc >= r:
                    # 增加选定元素的增量
                    increment[i] += 1
                    weights[i] = max(0, weights[i] - 1)  # 权重减少但至少为0
                    total_remaining -= 1
                    break

    # 构建最终结果
    res = [min_arr[i] + increment[i] for i in range(size)]
    return res

def choose(candidates, group_size, group_num):
    '''
    Select group_num tuples of length group_size from a set of symbols/events (candidates).
    '''
    if type(candidates) == dict:
        candidates = candidates.values()
    # 生成所有唯一的组合，确保顺序不影响
    unique_combinations = set()
    for comb in itertools.combinations(candidates, group_size):
        unique_combinations.add(comb)
    all_combinations = list(unique_combinations)
    m = len(all_combinations)
    
    if m == 0:
        return []
    
    if group_num <= m:
        return random.sample(all_combinations, group_num)
    else:
        base = group_num // m
        remainder = group_num % m
        result = []
        
        # 添加基数次数的组合，每次打乱顺序
        for _ in range(base):
            shuffled = random.sample(all_combinations, m)
            result.extend(shuffled)
        
        # 处理余数部分
        if remainder > 0:
            shuffled_remainder = random.sample(all_combinations, m)
            result.extend(shuffled_remainder[:remainder])
        
        # 打乱整个结果列表以确保随机性
        random.shuffle(result)
        return result
    
# def mapSolutionsToVar(satisfied_solutions, unsatisfied_solutions, events):
#     '''
#     将z3.solver的解(_solution)转换为答案
#     返回一个list，每个元素为一个tuple，包含每组解中的变量
#     '''
#     def work(sols):
#         res = []
#         for solution in sols:
#             vars = []
#             for var in solution:
#                 tmp = get_p
#                 vars.append(tmp)
#             res.append(tuple(vars))
#         return res
#     return work(satisfied_solutions), work(unsatisfied_solutions)


class SafeTemplate:
    def __init__(self, template):
        self.template = template
        self._parsed = self._validate_syntax()

    def _get_call_func_name(self, node):
        """解析被调用函数名称"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return node.attr
        return 'unknown'
    def _validate_syntax(self):
        """通过AST验证模板语法安全性"""
        try:
            tree = ast.parse(f"f{repr(self.template)}", mode='eval')
            for node in ast.walk(tree):
                # 禁止以下不安全结构
                if isinstance(node, ast.Call):
                    func_name = self._get_call_func_name(node.func)
                    if func_name not in _user_context_global and func_name not in _user_context_local and func_name not in globals():
                        raise ValueError(f"禁止调用的函数: {func_name}")
                # if isinstance(node, ast.Subscript):
                #     raise ValueError("禁止下标操作")
            return True
        except SyntaxError:
            return False

    def render(self, context):
        if not self._parsed:
            return self.template
        
        try:
            code = compile(f"f{repr(self.template)}", "<string>", "eval")
            # print(code, context, f"f{repr(self.template)}", get_p(context["_operand_l"], "names"))
            # print(context["students"], context["_index"])
            return eval(code, {'__builtins__': None}, context) 
        except Exception as e:
            raise e
            return self.template
# def generate_events(config):
#     """
#     生成带自然语言描述的逻辑表达式
#     返回: tuple (z3_expr, description)
#     """
#     op_translation = {
#         'eq': ('==', '等于'),
#         'neq': ('!=', '不等于'),
#         'lt': ('<', '小于'),
#         'gt': ('>', '大于'),
#         'lte': ('<=', '小于等于'),
#         'gte': ('>=', '大于等于'),
#         'and': (And, '并且'),
#         'or': (Or, '或者'),
#         'implies': (Implies, '则')
#     }

#     def generate_operand(domain_config):
#         # 处理离散集合（列表、range、NumPy数组等）
#         if isinstance(domain_config, (list, range, np.ndarray)):
#             if isinstance(domain_config, np.ndarray):
#                 return np.random.choice(domain_config)
#             else:
#                 return random.choice(list(domain_config))
#         # 处理连续区间（通过元组表示范围，如(0,1)）
#         elif isinstance(domain_config, tuple) and len(domain_config) == 2:
#             return random.uniform(domain_config[0], domain_config[1])
#         else:
#             return domain_config

#     def build_expr(config_node):
#         """递归构建表达式与描述"""
#         if not isinstance(config_node, dict):  # 叶子节点（变量/常量）
#             val = generate_operand(config_node)
#             display_val = val.decl().name() if isinstance(val, z3.ExprRef) else val
#             if isinstance(display_val, bool):
#                 display_val = '真' if display_val else '假'
#             return val, display_val

#         # 解析当前节点配置
#         candidates_operators = list(op_translation.keys()) if (not isinstance(config_node["operand_l"], dict) and not isinstance(config_node["operand_r"], dict)) else ["and", "or", "implies"]
#         operators = config.get('operator', candidates_operators)
#         if type(operators) != list:
#             operators = [operators]
#         op_type = random.choice(operators)
#         op_symbol, op_desc = op_translation[op_type]
#         left_expr, left_desc = build_expr(config_node['operand_l'])
#         right_expr, right_desc = build_expr(config_node['operand_r'])

#         # 构建Z3表达式
#         z3_op, _ = op_translation[op_type]
#         if callable(z3_op):
#             z3_expr = z3_op(left_expr, right_expr)
#         else:
#             z3_expr = eval(f"left_expr {z3_op} right_expr")

#         # 准备模板变量
#         template_vars = {
#             '_operator': op_symbol,
#             '_operand_l': left_expr,
#             '_operand_r': right_expr,
#             **(_user_context_global or {}),
#             **(_user_context_local or {}),
#             **(globals())
#         }
#         # print(template_vars["students"], template_vars["_index"])
#         # print(_user_context_local)

#         # 渲染描述模板
#         # desc_template = config_node.get('desc', 
#         #     f"{left_desc} {op_desc} {right_desc}"
#         # )

#         template = SafeTemplate(config_node.get('desc', f"{left_desc} {op_desc} {right_desc}"))
#         description = template.render(template_vars)

#         # description = eval(f"f'{desc_template}'", None, template_vars)

#         return z3_expr, description

#     return build_expr(config)

def make_expr(op: str, *operands):
    """
    Construct a Z3 expression.

    Parameters:
        op (str): Operator identifier, supporting the following forms:

            - Comparison operators: `"eq"`/`"=="`, `"neq"`/`"!="`, `"gt"`/`">"`, `"ge"`/`">="`, `"lt"`/`"<"`, `"le"`/`"<="`
            
            - Logical operators: `"and"`/`"&&"`, `"or"`/`"||"`, `"not"`/`"!"`, `"implies"`/`"=>"`
            
            - Arithmetic operators: `"add"`/`"+"`, `"sub"`/`"-"`, `"mul"`/`"*"`, `"div"`/`"/"`

        *operands (z3.ExprRef): Z3 expression operands, the number determined by the operator:

            - Unary operators: 1 operand (e.g., `not`)

            - Binary operators: 2 operands (e.g., `+`, `==`)

            - N-ary operators: Any number (e.g., `and`, `or`)

    Returns:
        z3.ExprRef: The generated Z3 expression object.

    Raises:
        ValueError: 
            - When an unsupported operator is used.
            - When the number of operands does not meet the operator's requirements.

    Examples:
        >>> x, y = Ints('x y')
        >>> make_expr(">=", x, 5)     # Creates x >= 5
        >>> make_expr("&&", x > 0, y < 10)  # Creates And(x > 0, y < 10)

    Notes:
        - Logical operators `and`/`or` support any number of operands.
        - Arithmetic operator `+` actually calls the `Sum` function (e.g., `a + b + c` converts to `Sum(a, b, c)`).
    """
    # 运算符映射表（支持 "eq" 和 "==" 两种形式）
    op_to_z3_func = {
        # 比较运算符
        "eq": lambda x, y: x == y,   "==": lambda x, y: x == y,
        "neq": lambda x, y: x != y,   "!=": lambda x, y: x != y,
        "gt": lambda x, y: x > y,    ">": lambda x, y: x > y,
        "ge": lambda x, y: x >= y,   ">=": lambda x, y: x >= y,
        "lt": lambda x, y: x < y,    "<": lambda x, y: x < y,
        "le": lambda x, y: x <= y,   "<=": lambda x, y: x <= y,
        # 逻辑运算符
        "and": And,     "&&": And,
        "or": Or,       "||": Or,
        "not": Not,     "!": Not,
        "implies": Implies, "=>": Implies,
        # 算术运算符
        "add": Sum,     "+": lambda *args: Sum(*args),
        "sub": lambda x, y: x - y, "-": lambda x, y: x - y,
        "mul": lambda x, y: x * y, "*": lambda x, y: x * y,
        "div": lambda x, y: x / y, "/": lambda x, y: x / y,
    }

    # 检查运算符是否支持
    if op not in op_to_z3_func:
        raise ValueError(f"Unsupported operator: '{op}'")

    # 获取对应的 Z3 函数
    z3_func = op_to_z3_func[op]

    # 检查算子数量是否合法
    if op in ("not", "!") and len(operands) != 1:
        raise ValueError(f"Operator '{op}' requires exactly 1 operand")
    elif op in ("eq", "ne", "gt", "ge", "lt", "le", "==", "!=", ">", ">=", "<", "<=", "+", "-", "*", "/"):
        if len(operands) != 2:
            raise ValueError(f"Operator '{op}' requires exactly 2 operands")
    # 对于可变参数的运算符（如 And/Or），不检查数量

    # 动态调用 Z3 函数
    return z3_func(*operands)


def to_hashable(element):
    """
    Recursively convert nested structures to hashable types.

    Parameters:
        element (Any): Input element, supports nested lists/tuples.

    Returns:
        Hashable object: Converts lists to tuples, preserving the nested structure.

    Examples:
        >>> to_hashable([1, [2, 3]])  # Returns (1, (2, 3))
        >>> to_hashable({1, 2})       # Returns the original set (since sets are not hashable).

    Notes:
        - Mainly used to use nested structures as dictionary keys or set elements.
        - Only processes list types; other container types (e.g., dict) need to be handled separately.
    """
    if isinstance(element, list):
        return tuple(to_hashable(e) for e in element)
    return element

def to_unique(l):
    """
    Remove duplicates from a list (preserving order).

    Parameters:
        l (Union[list, Any]): Input list or any type.

    Returns:
        A deduplicated list (maintaining the order of elements); returns the input directly if it's not a list.

    Examples:
        >>> to_unique([1, 2, 1, 3])  # Returns [1, 2, 3]
        >>> to_unique("abcaba")      # Returns ["a", "b", "c"]
    """
    if not isinstance(l, list):
        return l
    res = []
    s = set()
    for item in l:
        item_hash = to_hashable(item)
        if item_hash not in s:
            s.add(item_hash)
            res.append(item)
    return res

def sort_solutions(solutions, key_func=None):
    """
    Sort the list of solutions obtained from the Z3 solver.

    Parameters:
        solutions (list): The list of solutions to be sorted, where each element is a Z3 model.
        key_func (callable, optional): A function to generate the sorting key, which takes a model and returns a sortable value. Defaults to a tuple of values sorted by variable names.
    """
    if not solutions:
        return  # 无解，无需排序
    
    if key_func is None:
        # 提取所有变量并按名称排序
        vars = sorted(solutions[0], key=lambda v: v.name())
        
        def default_key(model):
            key = []
            for var in vars:
                val = model[var]
                # 将所有值统一转换为字符串
                if isinstance(val, IntNumRef):
                    key.append(str(val.as_long()))
                elif isinstance(val, BoolRef):
                    # 将布尔值转换为字符串 "True" 或 "False"
                    key.append(str(is_true(val)))
                elif isinstance(val, BitVecNumRef):
                    key.append(str(val.as_signed_long()))
                else:
                    key.append(str(val))  # 其他类型转为字符串
            return tuple(key)
        
        key_func = default_key
    
    # 原地排序
    solutions.sort(key=key_func)