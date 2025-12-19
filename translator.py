from itertools import product
from random import randint, uniform
from model.template import PuzzleTemplate
import json, os
import jsonpickle
import argparse
import yaml

# Custom exception classes for better error handling
class PuzzleGenerationError(Exception):
    """Base exception for puzzle generation errors"""
    pass

class NoSolutionError(PuzzleGenerationError):
    """Raised when Z3 solver cannot find any solution to the constraints"""
    pass

class TooManySolutionsError(PuzzleGenerationError):
    """Raised when the number of solutions exceeds the maximum allowed"""
    pass

class AnswerAssertionError(PuzzleGenerationError):
    """Raised when answer assertion validation fails"""
    pass

class RandomGenerationError(PuzzleGenerationError):
    """Raised when random number/option generation fails after multiple attempts"""
    pass

def ext(s):
    """
    在s前后加空格以适应f" " "环境
    """
    if s == "" or s == None:
        return ""
    return ('\\\"' if s[0] == '\"' else s[0]) + s[1:-1] + ('\\\"' if s[-1] == '\"' else s[-1])

symlist = {}
use_spec_vars = []
def init_program():
    global symlist 
    symlist = {}
    exec("from random import randint, uniform\n", symlist)
    p = """# -*- coding: utf-8 -*-
from z3 import *
from random import randint, uniform, sample, choice
import itertools
from utils import *
from collections.abc import Iterable
from functools import reduce
import re
import os
import sys
set_option(timeout=15000)
INDEX_PATTERN = re.compile(r'^__(\\d+)__$')

# Custom exception classes for better error handling
class PuzzleGenerationError(Exception):
    pass

class NoSolutionError(PuzzleGenerationError):
    pass

class TooManySolutionsError(PuzzleGenerationError):
    pass

class AnswerAssertionError(PuzzleGenerationError):
    pass

class RandomGenerationError(PuzzleGenerationError):
    pass
"""
    return p + "config = {}\n", p + "import jsonpickle\nconfig = jsonpickle.decode(r\'\'\'__config__\'\'\')\n"

def resolve_rand(domain_str: str, isint: bool):
    domain_data = domain_str[1:-1].split(',')
    if isint:
        exec(f"a = randint(int({eval(domain_data[0], symlist)}), int({eval(domain_data[1], symlist)}))", symlist)
        return symlist["a"]
    else:
        exec(f"a = uniform({eval(domain_data[0], symlist)}, {eval(domain_data[1], symlist)})", symlist)
        return symlist["a"]
     
def process_vars(Dict: dict):
    codegen = ""
    codeval = ""
    for var in Dict:
        codesol = ""
        if Dict[var].get("formula"):
            if 'generate_random_list' in Dict[var]["formula"]:
                codesol += "set_local_context(locals())\n"
            codesol += f"{var} = {Dict[var]['formula']}\n"
        else:
            if Dict[var]['type'] == 'int':
                domain_data = Dict[var]['domain'][1:-1].split(',')
                codesol += f"{var} = randint(int({domain_data[0].strip()}), int({domain_data[1].strip()}))\n"
            elif Dict[var]['type'] == 'float' or Dict[var]['type'] == 'real':
                domain_data = Dict[var]['domain'][1:-1].split(',')
                codesol += f"{var} = uniform({domain_data[0].strip()}, {domain_data[1].strip()})\n"
            elif Dict[var]['type'] in ['bool', 'enum']:
                if Dict[var]['type'] == 'bool' and Dict[var]['domain'] is None:
                    domain_data = ['True', 'False']
                else:
                    domain_data = Dict[var]['domain'][1:-1].split(',')
                if len(domain_data) == 1:
                    codesol += f"{var} = {domain_data[0].strip()}\n"
                else:
                    codesol += f"{var} = choice([{', '.join([item.strip() for item in domain_data])}])\n"
            else:
                raise Exception(f"Error: Type {Dict[var]['type']} is not supported")
        codesol += f"config[\"{var}\"] = {var}\n"
        
        codegen += codesol
        codeval += f"{var} = config[\"{var}\"]\n" if var not in use_spec_vars else codesol
    return codegen + '\n\n', codeval + '\n\n'



def process_custom_operator(Dict: dict):
    # res = ""
    # for func in Dict:
    #     res += f"def {func}:\n"
    #     lines = Dict[func].split('\n')
    #     for line in lines:
    #         res += '\t' + line
    # return res + '\n\n'
    def is_valid_path(path_str):
        try:
            _ = os.path.normpath(path_str)
            return True
        except (TypeError, AttributeError):
            return False
    
    res = ""
    for var in Dict:
        if is_valid_path(Dict[var]):
            if os.path.exists(Dict[var]):
                _dirname = os.path.dirname(Dict[var])
                _basename = os.path.basename(Dict[var]).split('.')[0]
                res += f"sys.path.append(\"{_dirname}\")\nfrom {_basename} import {var}\n"
                continue
            # else:
            #     print(f"Warning: Path '{Dict[var]}' does not exist and will be parsed as a function.")
        res += f"{var} = {Dict[var]}\n"
    return res + '\n\n', res + '\n\n'

def process_defined_symbols(sym: str, template: dict):
    res = ""
    if template is None or 'source' not in template:
        return res, res
    types = template["type"]
    type_text = '[' + ', '.join([f"\"{item}\"" for item in types]) + ']' if isinstance(types, list) else f"\"{types}\""
    descs = template["desc"]
    desc_text = '[' + ', '.join([f"\"{ext(item)}\"" for item in descs]) + ']' if isinstance(descs, list) else f"\"{descs}\""
    source = template['source']
    source_text = '{' + ', '.join([f"\"{s}\": {s}" for s in source]) + '}'
    attr = template.get('attr')  # Use .get() to avoid KeyError
    attr_text = None if attr is None else '[' + ', '.join([f"\"{item}\"" for item in attr]) + ']'
    res += f"{sym} = CustomSym(\"{sym}\", {source_text}, {attr_text}, {type_text}, {desc_text})\n"
    return res + '\n\n', res + '\n\n'

def process_multiple_derived_symbols(sym: str, templates: str):
    codegen = ""
    codeval = ""
    if templates is None:
        return codegen, codeval
    codegen += f"""
_total = {templates["total"]}
_num_of_templates = {len(templates["templates"])}
_pool_domain = generate_random_list_with_total(_num_of_templates,  [0, _total], _total, {[template["domain"] if "domain" in template else None for template in templates["templates"]]})
config["{sym}"] = {{"pool_domain": _pool_domain, "pool": []}}
_index = 0
{sym} = []
_desc = []
"""
    codeval += f"""
_pool_domain = config["{sym}"]["pool_domain"]
_index = 0
{sym} = []
_desc = []
"""
    for i, template in enumerate(templates["templates"]):
        codegen += f"""
# Generate Symbols for Template #{i}
_domain = _pool_domain[{i}]
_domain_cond = {template['domain_cond']}
_dim = {template['dim']}
_dim_cond = {template['dim_cond']}
_custom_cond = {template['custom_cond']}
_pool_len = [{', '.join('len(' + str(i) + ')' for i in template['source'])}]
_pool_amount = [{', '.join(str(i) for i in template['amount']) if template["amount"] else "1 for _ in range(len(_pool_len))"}]
try:
    _pool_indices, _pool_indices_str = generate_random_indices(_pool_len, _pool_amount, _domain, domain_cond=_domain_cond, dim=_dim, dim_cond=_dim_cond, custom_cond=_custom_cond, order={template['order']}, duplicate={template['duplicate']}, env=globals())
except Exception as e:
    raise RandomGenerationError(f"Failed to generate random indices for multiple derived symbols template #{i}: {{str(e)}}. This typically happens when the constraints are too restrictive or conflicting, making it impossible to generate valid random samples. Please retry, use '-c' for continuous mode, or review and revise the domain conditions, dimensions, and custom conditions for this template.")
config["{sym}"]["pool"].append(_pool_indices_str)
_pool_sources = [{', '.join(template['source'])}]
"""
        if template['dim'] == 1:
            codegen += f"""
_pool_vals = [[[list(src)[idx] for idx in idx_tuple] for src, idx_tuple in zip(_pool_sources, item) ] for item in _pool_indices ]
for _ind, _sym in zip(_pool_indices, _pool_vals):
    {'_sym = [item[0] for item in _sym]' if not template['amount'] else ''}
    {'_ind = [item[0] for item in _ind]' if not template['amount'] else ''}
    set_local_context(locals())
    _s = {template['formula']}
    _d = f\"\"\"{ext(template['desc'])}\"\"\"
    {sym}.append(_s)
    _desc.append(_d)
    _index += 1
    store_sym_config(_s, {{"desc": _d, "data": _sym}})
"""
            codeval += f"""
# Generate Symbols for Template #{i}
_domain = _pool_domain[{i}]
_pool_indices = config["{sym}"]["pool"][{i}]
_pool_sources = [{', '.join(template['source'])}]
_pool_vals = [[[list(src)[int(m.group(1))] if (m := INDEX_PATTERN.match(str(idx))) else idx for idx in idx_tuple] for src, idx_tuple in zip(_pool_sources, item) ] for item in _pool_indices ]
for _ind, _sym in zip(_pool_indices, _pool_vals):
    {'_sym = [item[0] for item in _sym]' if not template['amount'] else ''}
    {'_ind = [item[0] for item in _ind]' if not template['amount'] else ''}
    set_local_context(locals())
    _s = {template['formula']}
    _d = f\"\"\"{ext(template['desc'])}\"\"\"
    {sym}.append(_s)
    _desc.append(_d)
    _index += 1
    store_sym_config(_s, {{"desc": _d, "data": _sym}})
"""
        else:
            codegen += f"""
_pool_vals = [[[[list(src)[idx] for idx in idx_tuple] for src, idx_tuple in zip(_pool_sources, _idx_dim) ] for _idx_dim in _idx_domain] for _idx_domain in _pool_indices ]
for _pool_vals_domain in _pool_vals:
    _ss = []
    _dd = []
    for _sym in _pool_vals_domain:
        {'_sym = [item[0] for item in _sym]' if not template['amount'] else ''}
        set_local_context(locals())
        _s = {template['formula']}
        _d = f\"\"\"{ext(template['desc'])}\"\"\"
        _ss.append(_s)
        _dd.append(_d)
        store_sym_config(_s, {{"desc": _d, "data": _sym}})
    {sym}.append(_ss)
    _desc.append(_dd)
    _index += 1
"""
            codeval += f"""
# Generate Symbols for Template #{i}
_domain = _pool_domain[{i}]
_pool_indices = config["{sym}"]["pool"]["{i}"]
_pool_sources = [{', '.join(template['source'])}]
_pool_vals = [[[[list(src)[int(m.group(1))] if (m := INDEX_PATTERN.match(str(idx))) else idx for idx in idx_tuple] for src, idx_tuple in zip(_pool_sources, _idx_dim) ] for _idx_dim in _idx_domain ] for _idx_domain in _pool_indices ]
for  _index, _pool_vals_domain in enumerate(_pool_vals):
    _ss = []
    _dd = []
    for _sym in _pool_vals_domain:
        {'_sym = [item[0] for item in _sym]' if not template['amount'] else ''}
        set_local_context(locals())
        _s = {template['formula']}
        _d = f\"\"\"{ext(template['desc'])}\"\"\"
        _ss.append(_s)
        _dd.append(_d)
        store_sym_config(_s, {{"desc": _d, "data": _sym}})
    {sym}.append(_ss)
    _desc.append(_dd)
    _index += 1
"""

    codegen += f"""
store_sym_config({sym}, {{"desc": _desc, "data": _pool_vals}})
"""
    codeval += f"""
store_sym_config({sym}, {{"desc": _desc, "data": _pool_vals}})
"""
    return codegen, codeval

def process_single_derived_symbols(sym: str, template: str):
    codegen = ""
    codeval = ""
    if template is None:
        return codegen, codeval

    # 随机化参数
    codegen += f"""
_domain = {template['domain']}
_domain_cond = {template['domain_cond']}
_dim = {template['dim']}
_dim_cond = {template['dim_cond']}
_custom_cond = {template['custom_cond']}
_pool_len = [{', '.join('len(' + str(i) + ')' for i in template['source'])}]
"""
    if template['amount']:
        codegen += f"_pool_amount = [{', '.join(str(i) for i in template['amount'])}]\n"
    else:
        codegen += f"_pool_amount = [1 for _ in range(len(_pool_len))]\n"
    codegen += f"""
try:
    _pool_indices, _pool_indices_str = generate_random_indices(_pool_len, _pool_amount, _domain, domain_cond=_domain_cond, dim=_dim, dim_cond=_dim_cond, custom_cond=_custom_cond, order={template['order']}, duplicate={template['duplicate']}, env=globals())
except Exception as e:
    raise RandomGenerationError(f"Failed to generate random indices for single derived symbol '{sym}': {{str(e)}}. This typically happens when the constraints are too restrictive or conflicting, making it impossible to generate valid random samples. Please retry, use '-c' for continuous mode, or review and revise the domain conditions, dimensions, and custom conditions.")
config["{sym}"] = {{"pool": _pool_indices_str}}
_pool_sources = [{', '.join(template['source'])}]
{sym} = []
_desc = []
"""
    if template['dim'] == 1:
        codegen += f"""
_pool_vals = [[[list(src)[idx] for idx in idx_tuple] for src, idx_tuple in zip(_pool_sources, item) ] for item in _pool_indices ]
for _index, _sym in enumerate(_pool_vals):
    {'_sym = [item[0] for item in _sym]' if not template['amount'] else ''}
    set_local_context(locals())
    _s = {template['formula']}
    _d = f\"\"\"{ext(template['desc'])}\"\"\"
    {sym}.append(_s)
    _desc.append(_d)
store_sym_config({sym}, {{\"desc\": _desc, \"data\": _pool_vals}})
for _index, _sym in enumerate({sym}):
    store_sym_config(_sym, {{\"desc\": _desc[_index], \"data\": _pool_vals[_index]}})
"""
        codeval += f"""
_domain = {template['domain']}
_pool_indices = config[\"{sym}\"][\"pool\"]
_pool_sources = [{', '.join(template['source'])}]
_pool_vals = [[[list(src)[int(m.group(1))] if (m := INDEX_PATTERN.match(str(idx))) else idx for idx in idx_tuple] for src, idx_tuple in zip(_pool_sources, item) ] for item in _pool_indices ]
{sym} = []
_desc = []
for _index, _sym in enumerate(_pool_vals):
    {'_sym = [item[0] for item in _sym]' if not template['amount'] else ''}
    set_local_context(locals())
    _s = {template['formula']}
    _d = f\"\"\"{ext(template['desc'])}\"\"\"
    {sym}.append(_s)
    _desc.append(_d)
store_sym_config({sym}, {{\"desc\": _desc, \"data\": _pool_vals}})
for _index, _sym in enumerate({sym}):
    store_sym_config(_sym, {{\"desc\": _desc[_index], \"data\": _pool_vals[_index]}})
"""
    else:
        codegen += f"""
_pool_vals = [[[[list(src)[idx] for idx in idx_tuple] for src, idx_tuple in zip(_pool_sources, _idx_dim) ] for _idx_dim in _idx_domain] for _idx_domain in _pool_indices ]
for  _index, _pool_vals_domain in enumerate(_pool_vals):
    _ss = []
    _dd = []
    for _sym in _pool_vals_domain:
        {'_sym = [item[0] for item in _sym]' if not template['amount'] else ''}
        set_local_context(locals())
        _s = {template['formula']}
        _d = f\"\"\"{ext(template['desc'])}\"\"\"
        _ss.append(_s)
        _dd.append(_d)
    {sym}.append(_ss)
    _desc.append(_dd)
store_sym_config({sym}, {{\"desc\": _desc, \"data\": _pool_vals}})
for _idx_domain, _sym_d in enumerate({sym}):
    for _idx_dim, _sym in enumerate(_sym_d):
        store_sym_config(_sym, {{\"desc\": _desc[_idx_domain][_idx_dim], \"data\": _pool_vals[_idx_domain][_idx_dim]}})
"""
        codeval += f"""
_domain = {template['domain']}
_pool_indices = config[\"{sym}\"][\"pool\"]
_pool_sources = [{', '.join(template['source'])}]
{sym} = []
_desc = []
_pool_vals = [[[[list(src)[int(m.group(1))] if (m := INDEX_PATTERN.match(str(idx))) else idx for idx in idx_tuple] for src, idx_tuple in zip(_pool_sources, _idx_dim) ] for _idx_dim in _idx_domain ] for _idx_domain in _pool_indices ]
for  _index, _pool_vals_domain in enumerate(_pool_vals):
    _ss = []
    _dd = []
    for _sym in _pool_vals_domain:
        {'_sym = [item[0] for item in _sym]' if not template['amount'] else ''}
        set_local_context(locals())
        _s = {template['formula']}
        _d = f\"\"\"{ext(template['desc'])}\"\"\"
        _ss.append(_s)
        _dd.append(_d)
    {sym}.append(_ss)
    _desc.append(_dd)
store_sym_config({sym}, {{\"desc\": _desc, \"data\": _pool_vals}})
for _idx_domain, _sym_d in enumerate({sym}):
    for _idx_dim, _sym in enumerate(_sym_d):
        store_sym_config(_sym, {{\"desc\": _desc[_idx_domain][_idx_dim], \"data\": _pool_vals[_idx_domain][_idx_dim]}})
"""

    
    return codegen + '\n\n', codeval + '\n\n'

def process_symbols(Dict: dict):
    codegen = ""
    codeval = ""
    for item in Dict:
        if "type" in Dict[item]: # DefinedSymbol
            codesol = process_defined_symbols(item, Dict[item])
            codegen += codesol[0]
            codeval += codesol[1]
        elif "total" in Dict[item] and "templates" in Dict[item]: # DerivedSymbols
            codesol = process_multiple_derived_symbols(item, Dict[item])
            codegen += codesol[0]
            codeval += codesol[1]
        else: # DerivedSymbol
            codesol = process_single_derived_symbols(item, Dict[item])
            codegen += codesol[0]
            codeval += codesol[1]
    return codegen + '\n\n', codeval + '\n\n'


def process_static_conditions(sym: str, template: dict):
    res = ""
    if template['desc']:
        res += f"{sym} = f\"{ext(template['desc'])}\"\n"
    else:
        res += f"{sym} = ''\n"
    res += f"conditions += {sym}\n"
    res += f"_conditions.append({template['formula']})\n"
    return res + '\n\n', res + '\n\n'

def process_dynamic_conditions(sym: str, template: dict):
    codegen = ""
    codeval = ""
    if template['source'] is None:
        codesol = f"""{sym} = CustomCond(desc = f\"{ext(template['desc'])}\")
_conditions.append({template['formula']})
conditions += ({sym}.desc if {sym}.desc else '')
"""
        codegen += codesol
        codeval += codesol
        return codegen + '\n\n', codeval + '\n\n'

    # 生成随机domain
    if template['domain']:
        codegen += f"_num = randint({template['domain'][1:-1]})\n"
    else:
        codegen += f"_num = 1\n"
    codegen += f"config[\"{sym}\"] = {{\"domain\": _num}}\n"
    codeval += f"_num = config[\"{sym}\"][\"domain\"]\n"
    # 生成随机下标
    codegen += f"_pool_len = [{', '.join('len(' + str(i) + ')' for i in template['source'])}]\n"
    if template['amount']:
        codegen += f"_pool_amount = [{', '.join(str(i) for i in template['amount'])}]\n"
    else:
        codegen += f"_pool_amount = [1 for _ in range(len(_pool_len))]\n"
    codegen += f"""
try:
    _pool_indices, _pool_indices_str = generate_random_indices(_pool_len, _pool_amount, _num, domain_cond={template['domain_cond']}, custom_cond={template['custom_cond']}, env=globals())
except Exception as e:
    raise RandomGenerationError(f"Failed to generate random indices for dynamic condition '{sym}': {{str(e)}}. This typically happens when the constraints are too restrictive or conflicting, making it impossible to generate valid random samples. Please retry, use '-c' for continuous mode, or review and revise the domain conditions and custom conditions.")
config["{sym}"]["pool"] = _pool_indices_str
"""
    codeval += f"_pool_indices = config[\"{sym}\"][\"pool\"]\n"
    codegen += f"_pool_sources = [{', '.join(template['source'])}]\n"
    codeval += f"_pool_sources = [{', '.join(template['source'])}]\n"
    codegen += "_pool_vals = [[[list(src)[idx] for idx in idx_tuple] for src, idx_tuple in zip(_pool_sources, item) ] for item in _pool_indices ]\n"
    codeval += "_pool_vals = [[[list(src)[int(m.group(1))] if (m := INDEX_PATTERN.match(str(idx))) else idx for idx in idx_tuple] for src, idx_tuple in zip(_pool_sources, item) ] for item in _pool_indices ]\n"
    codegen += f"{sym} = CustomCond(domain=_num, data=_pool_vals)\n"
    codeval += f"{sym} = CustomCond(domain=_num, data=_pool_vals)\n"

    codegen += f"""for _index, _sym in enumerate(_pool_vals):\n
    {'_sym = [item[0] for item in _sym]' if template['amount'] is None else ''}
    {'_ind = [item[0] for item in _pool_indices[_index]]' if template['amount'] is None else '_ind = _pool_indices[_index]'}
    _conditions.append({template['formula']})
    {sym}.desc += f\"{ext(template['desc'])}\"
conditions += ({sym}.desc if {sym}.desc else '')
"""
    codeval += f"""for _index, _sym in enumerate(_pool_vals):\n
    {'_sym = [item[0] for item in _sym]' if template['amount'] is None else ''}
    {'_ind = [item[0] for item in _pool_indices[_index]]' if template['amount'] is None else '_ind = _pool_indices[_index]'}
    {'_ind = [int(m.group(1)) if (m := INDEX_PATTERN.match(str(idx))) else idx for idx in _ind]' if template['amount'] is None else '_ind = [[int(m.group(1)) if (m := INDEX_PATTERN.match(str(idx))) else idx  for idx in item] for item in _ind]'}
    _conditions.append({template['formula']})
    {sym}.desc += f\"{ext(template['desc'])}\"
conditions += ({sym}.desc if {sym}.desc else '')
"""
    return codegen + '\n\n', codeval + '\n\n'

def process_conditions(Dict: dict):
    codegen = ""
    codeval = ""
    codesol = """
_conditions = []
conditions = ""
"""
    codegen += codesol
    codeval += codesol
    for item in Dict:
        if "source" in Dict[item]: # DynamicCondition
            codesol = process_dynamic_conditions(item, Dict[item])
            codegen += codesol[0]
            codeval += codesol[1]
        else: # StaticCondition
            codesol = process_static_conditions(item, Dict[item])
            codegen += codesol[0]
            codeval += codesol[1]
    return codegen + '\n\n', codeval + '\n\n'

def process_post_generation(Dict: dict, calc_solution=True):
    codegen = ""
    codeval = ""
    # 随机选取一个解，作为生成问题的基准
    codesol = """_solver = Solver()
for cond in _conditions:
    _solver.add(cond)
_solver_size = len(_solver.assertions())
_solutions = []
_solver.set('random_seed', 50)
cnt = 0 
while _solver.check() == sat and cnt < 10: # 只取前10组解
    model = _solver.model()  # 获取当前解
    _solutions.append(model)  # 保存解
    cnt += 1
    
    # 添加排除条件：排除当前解的所有变量赋值
    block = []
    for var in model:
        block.append(var() != model[var])  # 对每个变量添加反向约束
    _solver.add(Or(block))  # 要求至少有一个变量与当前解不同
sort_solutions(_solutions)
"""
    codegen += codesol + """_sol_id = 0
config["_sol_id"] = _sol_id
_sol = _solutions[_sol_id] 
"""
    codeval += codesol + """_sol_id = config["_sol_id"]
_sol = _solutions[_sol_id]
"""
    # 对于post_gen_vars中的每个符号，代入目标解中的值
    codegen += "_post_gen_conditions = []\n"
    codeval += "_post_gen_conditions = []\n"
    codegen += "post_gen_conditions = \"\"\n"
    codeval += "post_gen_conditions = \"\"\n"
    if Dict["post_gen_vars"]:
        for sym, val in Dict["post_gen_vars"].items():
            codegen += f"""
{sym} = {val}
config["{sym}"] = {sym}
"""
            codeval += f"""
{sym} = config["{sym}"]
""" if sym not in use_spec_vars else f"""
{sym} = {val}
config["{sym}"] = {sym}
"""
    # 对于post_gen_condition中的每个条件，代入新问题
    if calc_solution:
        if Dict["post_gen_conditions"]:
            codesol2 = ""
            for item in Dict["post_gen_conditions"]:
                codesol2 += f"""
{item} = f\"{ext(Dict["post_gen_conditions"][item]['desc'])}\"
_post_gen_conditions.append({Dict["post_gen_conditions"][item]['formula']})
if {item} != '':
    post_gen_conditions += {item} + ';'
"""
            codegen += codesol2
            codeval += codesol2
                
        codesol3 = """
_solver.reset()
for cond in _conditions:
    _solver.add(cond)
for cond in _post_gen_conditions:
    _solver.add(cond)
_solver_size = len(_solver.assertions())
_solutions = []
while _solver.check() == sat:
    model = _solver.model()  # 获取当前解
    _solutions.append(model)  # 保存解
    
    # 添加排除条件：排除当前解的所有变量赋值
    block = []
    for var in model:
        block.append(var() != model[var])  # 对每个变量添加反向约束
    _solver.add(Or(block))  # 要求至少有一个变量与当前解不同
"""
        codegen += codesol3
        codeval += codesol3
    else:
        codesol3 = "_solver_size = 0\n"
        codegen += codesol3
        codeval += codesol3
    return codegen, codeval

def process_optimize(Dict: dict):
    codegen = ""
    codeval = ""
    optimize_type = Dict["type"]
    optimize_formula = Dict["formula"]
    codesol = f"""_solver = Optimize()
for cond in _conditions:
    _solver.add(cond)
_optimize_type = f\"{optimize_type}\"
_optimize_formula = {optimize_formula}
if _optimize_type == 'minimize':
    _solver.minimize(_optimize_formula)
else:
    _solver.maximize(_optimize_formula)
_solver_size = len(_solver.assertions())
_solutions = []
_value = None
# print(_solver)
try:
    if _solver.check() == sat:
        model = _solver.model()  # 获取当前解
        _solutions.append(model)  # 保存解
        _value = model.evaluate(_optimize_formula)
        # 添加排除条件：排除当前解的所有变量赋值
        block = []
        for var in model:
            block.append(var() != model[var])  # 对每个变量添加反向约束
        _solver.add(Or(block))  # 要求至少有一个变量与当前解不同
        _solver.add((_optimize_formula) == _value)
        if _solver.check() == sat:
            raise RandomGenerationError(f"The optimization problem has multiple optimal solutions with value {{_value}}. This makes the puzzle ambiguous. Please retry, use '-c' for continuous mode, or add additional constraints to ensure a unique optimal solution.")
    else:
        raise NoSolutionError(f"Z3 optimizer could not find any solution that satisfies the constraints for {{_optimize_type}} optimization of {{_optimize_formula}}. Please retry, use '-c' for continuous mode, or review your constraints and optimization objective.")
except Exception as e:
    if isinstance(e, (NoSolutionError, RandomGenerationError)):
        raise e
    else:
        raise RandomGenerationError(f"Z3 optimizer encountered an error: {{str(e)}}. This might be due to timeout, resource constraints, or complex optimization objectives. Please retry, use '-c' for continuous mode, or try again or simplify the problem.")

assert(len(_solutions) == 1)
_solutions = _solutions[0]
# print(_solutions, _value)
"""
    codegen += codesol
    codeval += codesol
    codegen += "print(\"Number of solutions:\", len(_solutions)) \n"
    return codegen, codeval
def process_query(Dict: dict):
    codegen = ""
    codeval = ""
    codesol = """queries = ''
ans = []
"""
    codegen += codesol
    codegen += "config['_queries'] = {}\n"
    codeval += codesol
    cnt = 0
    for q in Dict:
        cnt += 1
        
        
        if "source" in Dict[q] or "templates" in Dict[q]: # 选择题
            codegen += f"{q} = CustomCond(desc=f\"{ext(Dict[q]['desc'])}\" + '\\n')\n"
            codeval += f"{q} = CustomCond(desc=f\"{ext(Dict[q]['desc'])}\" + '\\n')\n"
            if "templates" not in Dict[q]:
                tmpcode = process_single_query(q, Dict[q], cnt)
                codegen += tmpcode[0]
                codeval += tmpcode[1]
            else:
                tmpcode = process_multiple_query(q, Dict[q], cnt)
                codegen += tmpcode[0]
                codeval += tmpcode[1]
    
        else: # 问答题
            codegen += f"""
_ans = {Dict[q]['ans_formula']}
try:
    assert({Dict[q]['ans_assertion']})
except AssertionError as e:
    raise AnswerAssertionError(f"Answer assertion failed for query '{q}': {{str(e) if str(e) else 'Assertion condition not met'}}. The generated answer '{{_ans}}' does not satisfy the assertion '{Dict[q]['ans_assertion']}'. This indicates that the constraints or answer formula may be inconsistent. Please retry, use '-c' for continuous mode, or review and revise the query specification.")
except Exception as e:
    raise AnswerAssertionError(f"Answer assertion evaluation failed for query '{q}': {{str(e)}}. There may be an error in the assertion formula '{Dict[q]['ans_assertion']}' or the answer formula '{Dict[q]['ans_formula']}'. Please retry, use '-c' for continuous mode, or check the syntax and logic in your specification.")
{q} = CustomCond(desc=f\"{ext(Dict[q]['desc'])}\" + '\\n')
queries += \"{cnt}. \" + {q}.desc
ans.append(str({Dict[q]['ans_text']}))
"""
            codeval += f"""
_ans = {Dict[q]['ans_formula']}
try:
    assert({Dict[q]['ans_assertion']})
except AssertionError as e:
    raise AnswerAssertionError(f"Answer assertion failed for query '{q}': {{str(e) if str(e) else 'Assertion condition not met'}}. The generated answer '{{_ans}}' does not satisfy the assertion '{Dict[q]['ans_assertion']}'. This indicates that the constraints or answer formula may be inconsistent. Please retry, use '-c' for continuous mode, or review and revise the query specification.")
except Exception as e:
    raise AnswerAssertionError(f"Answer assertion evaluation failed for query '{q}': {{str(e)}}. There may be an error in the assertion formula '{Dict[q]['ans_assertion']}' or the answer formula '{Dict[q]['ans_formula']}'. Please retry, use '-c' for continuous mode, or check the syntax and logic in your specification.")
{q} = CustomCond(desc=f\"{ext(Dict[q]['desc'])}\" + '\\n')
queries += \"{cnt}. \" + {q}.desc
ans.append(str({Dict[q]['ans_text']}))
"""
    codegen += "ans = '===='.join([str(v) for v in ans])\n"
    codeval += "ans = '===='.join([str(v) for v in ans])\n"
    return codegen + '\n\n', codeval + '\n\n'


def process_single_query(q: str, qconfig: str, cnt: int):
    codegen = ""
    codeval = ""
    # 生成随机数池
    codegen += f"""
_source = [{', '.join(qconfig['source'])}]
_amount = [{', '.join(qconfig['amount']) if qconfig['amount'] else ', '.join(['1' for i in range(len(qconfig['source']))])}]
_correct_num = {1 if qconfig['select_type'] else qconfig['opt_num'] - 1}
_incorrect_num = {1 if not qconfig['select_type'] else qconfig['opt_num'] - 1}
try:
    _satisfied_configs, _unsatisfied_configs, _satisfied, _unsatisfied = find_required_event_groups(_source, _correct_num, _incorrect_num, _solutions, "{qconfig['opt_formula']}", cond = "{qconfig['cond']}", event_num = _amount, order = {qconfig['order']}, duplicate = {qconfig['duplicate']}, custom_cond = {qconfig['custom_cond']}, env = globals())
except Exception as e:
    raise RandomGenerationError(f"Failed to generate options for query '{q}': {{str(e)}}. This typically happens when it's impossible to find enough valid/invalid options that satisfy the constraints. Please retry, use '-c' for continuous mode, or review and revise the query conditions, source data, or reduce the number of required options.")
"""         

    # 生成选项
    if qconfig['select_type'] == True: # 问的是正确选项：1个正确项 + （opt_num - 1)个错误项
        codegen += f"""
opt_num = {qconfig['opt_num']}
_ans_index = randint(0, opt_num - 1)
_opts = _unsatisfied[:_ans_index] + _satisfied + _unsatisfied[_ans_index:]
_configs = _unsatisfied_configs[:_ans_index] + _satisfied_configs + _unsatisfied_configs[_ans_index:]
config["_queries"]["{q}"] = {{"pool": _configs}}
"""
    else: # 问的是错误选项：1个错误项 + （opt_num - 1)个正确项
        codegen += f"""
opt_num = {qconfig['opt_num']}
_ans_index = randint(0, opt_num - 1)
_opts = _satisfied[:_ans_index] + _unsatisfied + _satisfied[_ans_index:]
_configs = _satisfied_configs[:_ans_index] + _unsatisfied_configs + _satisfied_configs[_ans_index:]
config["_queries"]["{q}"] = {{"pool": _configs}}
"""
    codeval += f"""
_source = [{', '.join(qconfig['source'])}]
_config_opts = config["_queries"][\"{q}\"]["pool"]
_opts = []
for _opt in _config_opts:
    _opts.append([[list(src)[int(m.group(1))] if (m := INDEX_PATTERN.match(str(idx))) else list(src)[idx] for idx in idx_tuple] for src, idx_tuple in zip (_source, _opt)])

_ans_index = ""
for _ind, _opt in enumerate(_opts):
    if is_option_valid(_opt, \"{qconfig['opt_formula']}\", \"{qconfig['cond']}\", {qconfig['select_type']}, globals()):
        _ans_index += chr(_ind + 65)
"""

    # 生成选项文本
    codegen += f"""
_opt_text = []
for _index, _opt in enumerate(_opts):
    _opt_text.append(chr(_index + 65) + '. ' + f\"{qconfig['opt_text']}\")
{q}.desc += '\\n'.join(_opt_text) + '\\n'
"""
    codeval += f"""
_opt_text = []
for _index, _opt in enumerate(_opts):
    _opt_text.append(chr(_index + 65) + '. ' + f\"{qconfig['opt_text']}\")
{q}.desc += '\\n'.join(_opt_text) + '\\n'
"""


    codegen += f"queries += \"{cnt}. \" + {q}.desc + '\\n'\n"
    codeval += f"queries += \"{cnt}. \" + {q}.desc + '\\n'\n"

    # 生成答案
    codegen += f"ans.append(chr(_ans_index + 65))\n"
    codeval += f"ans.append(_ans_index)\n"
    return codegen, codeval
def process_multiple_query(q: str, qconfig: str, cnt: int):
    codegen = ""
    codeval = ""
    codegen += f"""
opt_num = {qconfig["opt_num"]}
_num_of_templates = {len(qconfig["templates"])}
_pool_domain = generate_random_list_with_total(_num_of_templates, [0, opt_num], opt_num, {[eval(template["domain"]) if "domain" in template else None for template in qconfig["templates"]]})
config["_queries"]["{q}"] = {{"pool_domain": _pool_domain, "pool": []}}
"""
    if qconfig["select_type"]: # 问的是正确选项：1个正确项 + （opt_num - 1)个错误项
        codegen += f"""
_pool_incorrect_num = generate_random_list_with_total(_num_of_templates,  [0, opt_num - 1], opt_num - 1, [[0, v] for v in _pool_domain])
_pool_correct_num = [x - y for x, y in zip(_pool_domain, _pool_incorrect_num)]
config["_queries"]["{q}"] = {{"pool_domain": _pool_domain, "pool_correct_num": _pool_correct_num, "pool_incorrect_num": _pool_incorrect_num, "pool": []}}
"""
    else:
        codegen += f"""
_pool_correct_num = generate_random_list_with_total(_num_of_templates, [0, opt_num - 1], opt_num - 1, [[0, v] for v in _pool_domain])
_pool_incorrect_num = [x - y for x, y in zip(_pool_domain, _pool_correct_num)]
config["_queries"]["{q}"] = {{"pool_domain": _pool_domain, "pool_correct_num": _pool_correct_num, "pool_incorrect_num": _pool_incorrect_num, "pool": []}}
"""

    codeval += f"""
_pool_domain = config["_queries"]["{q}"]["pool_domain"]
_pool_correct_num = config["_queries"]["{q}"]["pool_correct_num"]
_pool_incorrect_num = config["_queries"]["{q}"]["pool_incorrect_num"]
"""
    
    codegen += f"""
_pool_satisfied_configs = []
_pool_unsatisfied_configs = []
_pool_satisfied = []
_pool_unsatisfied = []
"""
    
    for i, template in enumerate(qconfig["templates"]):
        assert('dim' not in template or template['dim'] == 1)
        # 生成随机数池
        codegen += f"""
# Generate Options for Template #{i}
_domain = _pool_domain[{i}]
_source = [{', '.join(template['source'])}]
_amount = [{', '.join(template['amount']) if template['amount'] else ', '.join(['1' for i in range(len(template['source']))])}]
_correct_num = _pool_correct_num[{i}]
_incorrect_num = _pool_incorrect_num[{i}]
try:
    _satisfied_configs, _unsatisfied_configs, _satisfied, _unsatisfied = find_required_event_groups(_source, _correct_num, _incorrect_num, _solutions, "{template['opt_formula']}", cond = "{template['cond']}", event_num = _amount, order = {template['order']}, duplicate = {template['duplicate']}, custom_cond = {template['custom_cond']}, env = globals())
except Exception as e:
    raise RandomGenerationError(f"Failed to generate options for multiple query '{q}' template #{i}: {{str(e)}}. This typically happens when it's impossible to find enough valid/invalid options that satisfy the constraints for this template. Please retry, use '-c' for continuous mode, or review and revise the query conditions, source data, or reduce the number of required options.")
_pool_satisfied_configs.extend(map(lambda item: {{"template_id": {i}, "config": item}}, _satisfied_configs))
_pool_unsatisfied_configs.extend(map(lambda item: {{"template_id": {i}, "config": item}}, _unsatisfied_configs))
_pool_satisfied.extend(_satisfied)
_pool_unsatisfied.extend(_unsatisfied)
"""
        
    # 生成选项
    if qconfig['select_type'] == True: # 问的是正确选项：1个正确项 + （opt_num - 1)个错误项
        codegen += f"""
_ans_index = randint(0, opt_num - 1)
_opts = _pool_unsatisfied[:_ans_index] + _pool_satisfied + _pool_unsatisfied[_ans_index:]
_configs = _pool_unsatisfied_configs[:_ans_index] + _pool_satisfied_configs + _pool_unsatisfied_configs[_ans_index:]
config["_queries"]["{q}"]["pool"] = _configs
"""
    else: # 问的是错误选项：1个错误项 + （opt_num - 1)个正确项
        codegen += f"""
_ans_index = randint(0, opt_num - 1)
_opts = _pool_satisfied[:_ans_index] + _pool_unsatisfied + _pool_satisfied[_ans_index:]
_configs = _pool_satisfied_configs[:_ans_index] + _pool_unsatisfied_configs + _pool_satisfied_configs[_ans_index:]
config["_queries"]["{q}"]["pool"] = _configs
"""
        
    codegen += f"""
_opt_text = []
_opt_texts = {[template["opt_text"] for template in qconfig["templates"]]}
for _index, _opt in enumerate(_opts):
    _opt_template_id = _configs[_index]["template_id"]
    _opt_text_template = "f\\\"" + _opt_texts[_opt_template_id] + "\\\""
    _opt_text.append(chr(_index + 65) + '. ' + eval(_opt_text_template))
{q}.desc += '\\n'.join(_opt_text) + '\\n'
queries += \"{cnt}. \" + {q}.desc + '\\n'
ans.append(chr(_ans_index + 65))
"""

    _sources = []
    for template in qconfig["templates"]:
        _sources.append('[' + ','.join(template["source"]) + ']')
    codeval += f"""
_config_opts = config["_queries"][\"{q}\"]["pool"]
_opts = []
_sources = [{', '.join(_sources)}]
for _opt in _config_opts:
    _opt_template_id = _opt["template_id"]
    _opt_config = _opt["config"]
    _opts.append([[list(src)[int(m.group(1))] if (m := INDEX_PATTERN.match(str(idx))) else list(src)[idx] for idx in idx_tuple] for src, idx_tuple in zip(_sources[_opt_template_id], _opt_config)])

_opt_text = []
_opt_texts = {[template["opt_text"] for template in qconfig["templates"]]}
for _index, (_opt_config, _opt) in enumerate(zip(_config_opts, _opts)):
    _opt_template_id = _opt_config["template_id"]
    _opt_text_template = "f\\"" + _opt_texts[_opt_template_id] + "\\""
    _opt_text.append(chr(_index + 65) + '. ' + eval(_opt_text_template))
{q}.desc += '\\n'.join(_opt_text) + '\\n'
_ans_index = ""
for _ind, (_opt_config, _opt) in enumerate(zip(_config_opts, _opts)):
    _opt_template_id = _opt_config["template_id"]
    _opt_formulas = {[template["opt_formula"] for template in qconfig["templates"]]}
    _conds = {[template["cond"] for template in qconfig["templates"]]}
    if is_option_valid(_opt, _opt_formulas[_opt_template_id], _conds[_opt_template_id], {qconfig["select_type"]}, globals()):
        _ans_index += chr(_ind + 65)
queries += \"{cnt}. \" + {q}.desc + '\\n'
ans.append(_ans_index)
"""

    return codegen, codeval
def translator(spec: dict):
    codegen, codeval = init_program() # the result program
    
    # process custom operator
    if spec.get('custom_operator'):
        res = process_custom_operator(spec['custom_operator'])
        codegen += res[0]
        codeval += res[1]

    # process variables
    if spec.get('variables'):
        res = process_vars(spec['variables'])
        codegen += res[0]
        codeval += res[1]

    if spec.get('symbols'):
        res = process_symbols(spec['symbols'])
        codegen += res[0]
        codeval += res[1]

    # Initialize _conditions even if no conditions are specified
    if spec.get('conditions'):
        res = process_conditions(spec['conditions'])
        codegen += res[0]
        codeval += res[1]
    else:
        # Initialize empty conditions
        codesol = """
_conditions = []
conditions = ""
"""
        codegen += codesol
        codeval += codesol

    if spec.get('post_generation'):
        res = process_post_generation(spec['post_generation'], calc_solution=spec['calc_solution'])
        codegen += res[0]
        codeval += res[1]
    elif spec.get('optimize'):
        res = process_optimize(spec['optimize'])
        codegen += res[0]
        codeval += res[1]
    elif spec.get('calc_solution'):
        codesol = f"""_solver = Solver()
for cond in _conditions:
    _solver.add(cond)
_solver_size = len(_solver.assertions())
_solutions = []
try:
    while _solver.check() == sat:
        model = _solver.model()  # 获取当前解
        _solutions.append(model)  # 保存解
        if(len(_solutions) > {spec['max_solution']}):
            raise TooManySolutionsError(f"Found {{len(_solutions)}} solutions, which exceeds the maximum allowed ({spec['max_solution']}). This typically means the constraints are too loose. Please retry, use '-c' for continuous mode, or consider adding more specific constraints to reduce the solution space, or increase the max_solution limit if appropriate.")
        
        # 添加排除条件：排除当前解的所有变量赋值
        block = []
        for var in model:
            block.append(var() != model[var])  # 对每个变量添加反向约束
        _solver.add(Or(block))  # 要求至少有一个变量与当前解不同
except Exception as e:
    if isinstance(e, TooManySolutionsError):
        raise e
    else:
        raise RandomGenerationError(f"Z3 solver encountered an error during solution generation: {{str(e)}}. This might be due to timeout or resource constraints. Please retry, use '-c' for continuous mode, or try again or simplify the constraints.")

if len(_solutions) == 0:
    # Get more detailed information about why there's no solution
    _unsat_core = _solver.unsat_core() if hasattr(_solver, 'unsat_core') else []
    _core_info = f" Unsatisfiable core: {{[str(c) for c in _unsat_core]}}" if _unsat_core else ""
    raise NoSolutionError(f"Z3 solver could not find any solution that satisfies all the given constraints. This means the constraints are contradictory or too restrictive.{{_core_info}} Please retry, use '-c' for continuous mode, or review your puzzle specification and ensure the constraints are consistent and achievable.")
"""
        codegen += codesol
        codeval += codesol
        codegen += "print(\"solution number:\", len(_solutions)) \n"
        # if spec["assert_one_solution"]:
        #     codegen += "assert(len(_solutions) == 1)\n"
        #     codeval += "assert(len(_solutions) == 1)\n"
    else:
        codesol = "_solver_size = 0\n"
        codegen += codesol
        codeval += codesol

    # process queries
    if spec.get('queries'):
        res = process_query(spec['queries'])
        codegen += res[0]
        codeval += res[1]

    codesol = f"""problem = f\"\"\"{ext(spec['desc'])}\"\"\"
print(problem)
print('answer: ', ans)
"""
    codegen += codesol
    codeval += codesol

    # with open("output.py", "w", encoding='utf-8') as fp:
    #     fp.write(codegen)
    
    return codegen, codeval


def process(puzzle_template, mode, input_filename_base='example'):
    try:
        codegen, codeval = translator(puzzle_template)
        #   print(code)

        # for debug
        if '-t' in mode:
            with open(f"{input_filename_base}_synthesizer.py", "w", encoding="utf-8") as output_file:
                output_file.write(codegen)

        symlist_code = {}
        #   print(config)
        exec(codegen, symlist_code)
        config = symlist_code['config']
        encoded_config = json.loads(jsonpickle.encode(config))
        encoded_config_str = json.dumps(encoded_config, ensure_ascii=False)
        codeval = codeval.replace("__config__", encoded_config_str)
        if '-t' in mode:
            with open(f"{input_filename_base}_validator.py", "w", encoding="utf-8") as output_file:
                output_file.write(codeval)
            with open(f"{input_filename_base}_config.json", "w", encoding="utf-8") as output_file:
                output_file.write(encoded_config_str)
        problem = symlist_code["problem"]
        answer = symlist_code["ans"]
        sym_num = 0
        symbols = puzzle_template.get("symbols", {})
        if symbols:
            defined_symbols = {k: v for k, v in symbols.items() if 'type' in v}
            for var in defined_symbols:
                sym_num += len(symlist_code[var])
            sym_type = list(set(
                item 
                for v in defined_symbols.values() 
                for item in (v["type"] if isinstance(v["type"], list) else [v["type"]])
            ))
        else:
            defined_symbols = {}
            sym_type = []
        cond_num = int(symlist_code["_solver_size"])
        return {
            "problem": problem,
            "answer": answer,
            # "solution": codeval,
            "parameters": {
                "cond_num": cond_num,
                "sym_num": sym_num,
                "sym_type":  sym_type,
                **({"opt_solution": str(symlist_code['_solutions'])} if puzzle_template["optimize"] is not None else {})
            },
            "config": encoded_config
        }
    except (NoSolutionError, TooManySolutionsError, AnswerAssertionError, RandomGenerationError) as e:
        # Re-raise our custom exceptions with their detailed messages
        raise e
    except Exception as e:
        # Catch any other unexpected errors and provide a generic message
        raise PuzzleGenerationError(f"Unexpected error during puzzle generation: {str(e)}. Please retry, use '-c' for continuous mode, or check your puzzle specification for syntax errors or invalid configurations, and try again.")


def repeat_process(puzzle_spec_path, output_path, new_puzzles_num=100, mode = "-t"):
    
    puzzle_template = None
    try:
        with open(puzzle_spec_path, "r", encoding="utf-8") as file:
            content = file.read()
            # for yaml files
            if puzzle_spec_path.endswith(".yaml"):
                content = yaml.load(content, Loader=yaml.FullLoader)
                puzzle_template = PuzzleTemplate.model_validate(content)
            else: 
                puzzle_template = PuzzleTemplate.model_validate_json(content)
            # puzzle_template_json = puzzle_template.model_dump_json(indent=2)  # 转换为 JSON str
            puzzle_template = puzzle_template.model_dump()  # 转换为 JSON Data
    except Exception as e:
        print(e)

    if not puzzle_template:
        return False

    # Extract filename without extension for debug output files
    input_filename_base = os.path.splitext(os.path.basename(puzzle_spec_path))[0]

    with open(output_path, "w", encoding="utf-8", buffering=1) as output_file:
        for i in range(new_puzzles_num):
            while True:  # Keep retrying until successful
                try:
                    sample = process(puzzle_template, mode, input_filename_base)
                    output_file.write(json.dumps(sample, ensure_ascii=False) + '\n')
                    break  # Exit the while loop and move to next puzzle
                except (NoSolutionError, TooManySolutionsError, AnswerAssertionError, RandomGenerationError) as e:
                    if '-c' not in mode:
                        raise e
                    # In continuous mode, just retry the same puzzle
                    continue
                except Exception as e:
                    if '-c' not in mode:
                        raise e
                    # In continuous mode, just retry the same puzzle
                    continue
    return True 

import json

def parse_config_file(config_file):
    config_list = []
    
    try:
        with open(config_file, "r", encoding="utf-8") as file:
            # Parse based on file extension
            if config_file.endswith('.json'):
                # Parse as JSON (single object)
                # data = jsonpickle.decode(file.read())
                data = file.read()
                config_list.append(data)
            elif config_file.endswith('.jsonl'):
                # Process as JSONL (each line is a JSON object)
                for line_number, line in enumerate(file, 1):
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        data = json.loads(line)
                        if "config" not in data:
                            raise ValueError(f"Line {line_number} does not contain 'config' field")
                        config_list.append(data["config"])
                    except json.JSONDecodeError as e:
                        raise ValueError(f"Invalid JSON at line {line_number}: {str(e)}")
            else:
                raise ValueError(f"Unsupported file extension. Expected .json or .jsonl, got: {config_file}")
                
        return config_list
        
    except Exception as e:
        print(f"Error processing config file: {str(e)}")
        raise

def process_with_config(puzzle_spec_path, output_path, config_file):
    puzzle_template = None
    try:
        with open(puzzle_spec_path, "r", encoding="utf-8") as file:
            content = file.read()
            # for yaml files
            if puzzle_spec_path.endswith(".yaml"):
                content = yaml.load(content, Loader=yaml.FullLoader)
                puzzle_template = PuzzleTemplate.model_validate(content)
            else: 
                puzzle_template = PuzzleTemplate.model_validate_json(content)
            puzzle_template = puzzle_template.model_dump()  # 转换为 JSON Data
    except Exception as e:
        print(e)

    if not puzzle_template:
        return False
    
    # Extract filename without extension for debug output files
    input_filename_base = os.path.splitext(os.path.basename(puzzle_spec_path))[0]
    
    configs = parse_config_file(config_file)

    codegen, codeval = translator(puzzle_template)

    with open(output_path, "w", encoding="utf-8") as output_file:
        for config_idx, config in enumerate(configs):
            try:
                # config_index = codeval.find("__config__")
                # config_next_line_index = codeval[config_index:].find("\n") + config_index
                # codeval = codeval[:config_next_line_index] + f'\n__use_spec_vars__ = {use_spec_vars}' + codeval[config_next_line_index:]
                codeval_new = codeval.replace("__config__", str(config))

                # for debug
                if '-t' in mode:
                    with open(f"{input_filename_base}_synthesizer.py", "w", encoding="utf-8") as debug_file:
                        debug_file.write(codeval_new)

                symlist_code = {}
                exec(codeval_new, symlist_code)
                problem = symlist_code["problem"]
                answer = symlist_code["ans"]
                config_modified = symlist_code['config'] # the config after generating the new puzzle
                encoded_config = json.loads(jsonpickle.encode(config_modified))
                # encoded_config_str = json.dumps(encoded_config, ensure_ascii=False)
                sym_num = 0
                symbols = puzzle_template.get("symbols", {})
                if symbols:
                    defined_symbols = {k: v for k, v in symbols.items() if 'type' in v}
                    for var in defined_symbols:
                        sym_num += len(symlist_code[var])
                    sym_type = list(set(
                        item 
                        for v in defined_symbols.values() 
                        for item in (v["type"] if isinstance(v["type"], list) else [v["type"]])
                    ))
                else:
                    defined_symbols = {}
                    sym_type = []
                cond_num = int(symlist_code["_solver_size"])
                res = {
                    "problem": problem,
                    "answer": answer,
                    # "solution": codeval,
                    "parameters": {
                        "cond_num": cond_num,
                        "sym_num": sym_num,
                        "sym_type":  sym_type,
                        **({"opt_solution": str(symlist_code['_solutions'])} if puzzle_template["optimize"] is not None else {})
                    },
                    "config": encoded_config
                }
                output_file.write(json.dumps(res, ensure_ascii=False) + '\n')
            except (NoSolutionError, TooManySolutionsError, AnswerAssertionError, RandomGenerationError) as e:
                print(f"\n⚠️  Config-based puzzle generation failed for config #{config_idx + 1}:")
                print(f"   {type(e).__name__}: {str(e)}")
                print("   Skipping this configuration...")
                continue
            except Exception as e:
                print(f"\n❌ Unexpected error processing config #{config_idx + 1}: {str(e)}")
                print("   Skipping this configuration...")
                continue

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--deploy', 
                        help="Enable deploy mode")
    parser.add_argument('-t', '--test', 
                        help="Enable test mode")
    parser.add_argument('-n', '--num', 
                        help="Enable test mode")
    parser.add_argument('-c','--continuous',
                        action='store_true',
                        help="Enable continuous search")
    parser.add_argument('-o', '--output', 
                        help="Specify output file name")
    parser.add_argument('-g', '--config', 
                        help="Specify configuration file",
                        required=False)
    parser.add_argument('-u', '--use-spec-vars', nargs='+',
                        help="Variables whose values depend on the specification during config-based generation",
                        required=False)
    args = parser.parse_args()

    mode =  []
    if args.continuous:
        mode.append("-c")
    
    # 根据参数选择模式
    if not args.deploy and not args.test:
        raise Exception("Either -d or -t should be specified.")
    elif args.deploy:
        # Mode 2
        puzzle_spec_path = args.deploy
        new_puzzles_num = int(args.num) if args.num else 1000
        input_filename_base = os.path.splitext(os.path.basename(puzzle_spec_path))[0]
        output_path = args.output if args.output else os.path.join(os.path.dirname(puzzle_spec_path), f"{input_filename_base}_output_1k.jsonl")
        mode.append("-d")
        mode.append("-c")
    else:
        # Mode 1
        puzzle_spec_path = args.test
        new_puzzles_num = int(args.num) if args.num else 1
        input_filename_base = os.path.splitext(os.path.basename(puzzle_spec_path))[0]
        output_path = args.output if args.output else os.path.join(os.path.dirname(puzzle_spec_path), f"{input_filename_base}_output.jsonl")
        mode.append("-t")
    
    if args.config:
        use_spec_vars = args.use_spec_vars if args.use_spec_vars else []
        process_with_config(puzzle_spec_path, output_path, args.config)
    else:
        repeat_process(puzzle_spec_path, output_path, new_puzzles_num, mode=mode)
