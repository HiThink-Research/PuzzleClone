import random

def is_valid(grid, row, col, num):
    """检查数字num是否可以放在grid[row][col]位置"""
    # 检查行
    if num in grid[row]:
        return False
    # 检查列
    if num in [grid[i][col] for i in range(9)]:
        return False
    # 检查3x3宫格
    start_row, start_col = 3 * (row // 3), 3 * (col // 3)
    for i in range(3):
        for j in range(3):
            if grid[start_row + i][start_col + j] == num:
                return False
    return True

def solve_sudoku(grid):
    """使用回溯算法求解数独，返回解的个数"""
    for row in range(9):
        for col in range(9):
            if grid[row][col] == 0:
                for num in range(1, 10):
                    if is_valid(grid, row, col, num):
                        grid[row][col] = num
                        if solve_sudoku(grid) == 1:
                            return 1
                        grid[row][col] = 0
                return 0
    return 1

def generate_sudoku():
    """生成一个完整的数独解"""
    grid = [[0] * 9 for _ in range(9)]
    # 随机填充第一行
    first_row = random.sample(range(1, 10), 9)
    grid[0] = first_row
    # 解数独（此时会生成一个随机解）
    solve_sudoku(grid)
    return grid

def generate_sparse_matrix(n, rows=9, cols=9):
    """
    生成一个稀疏0-1矩阵，满足：
    - 每行2~4个非零数
    - 每列2~4个非零数
    - 总共n个非零数
    
    参数：
    n: 非零元素的总数
    rows: 矩阵行数（默认9）
    cols: 矩阵列数（默认9）
    
    返回：
    生成的矩阵（二维列表）
    
    异常：
    如果n无效或无法生成矩阵，则抛出ValueError
    """
    # 验证n的可行性
    min_non_zeros = max(rows * 2, cols * 2)
    max_non_zeros = min(rows * 4, cols * 4)
    if not (min_non_zeros <= n <= max_non_zeros):
        raise ValueError(f"n must be between {min_non_zeros} and {max_non_zeros}. Got n={n}.")
    
    def generate_sum_vector(total, size, min_val, max_val):
        """生成随机和向量：总和=total, 每个元素在[min_val, max_val]之间"""
        vec = [min_val] * size
        residual = total - min_val * size
        if residual < 0:
            return None
        attempts = 0
        max_attempts = 1000
        while residual > 0 and attempts < max_attempts:
            idx = random.randint(0, size - 1)
            if vec[idx] < max_val:
                vec[idx] += 1
                residual -= 1
            attempts += 1
        if residual != 0:
            return None
        return vec
    
    max_attempts = 10000
    for attempt in range(max_attempts):
        # 随机生成行和向量与列和向量
        row_sums = generate_sum_vector(n, rows, 2, 4)
        if row_sums is None:
            continue
        col_sums = generate_sum_vector(n, cols, 2, 4)
        if col_sums is None:
            continue
            
        # 检查向量有效性
        if sum(row_sums) != n or sum(col_sums) != n:
            continue
            
        # 使用贪心算法尝试构建矩阵
        matrix = [[0] * cols for _ in range(rows)]
        row_tuples = [[row_sum, i] for i, row_sum in enumerate(row_sums)]
        col_tuples = [[col_sum, j] for j, col_sum in enumerate(col_sums)]
        valid = True
        
        for _ in range(rows):
            # 按行和降序排序行
            row_tuples.sort(key=lambda x: x[0], reverse=True)
            r_val, r_idx = row_tuples[0]
            if r_val == 0:
                break
                
            # 按列和降序序列
            col_tuples.sort(key=lambda x: x[0], reverse=True)
            # 获取非零列和
            non_zero_cols = [col for col in col_tuples if col[0] > 0]
            if len(non_zero_cols) < r_val:
                valid = False
                break
                
            # 选择前r_val个非零列
            selected_cols = non_zero_cols[:r_val]
            # 在矩阵中放置1并更新列和
            for col_item in selected_cols:
                c_idx = col_item[1]
                matrix[r_idx][c_idx] = 1
                col_item[0] -= 1
                
            # 标记当前行已处理
            row_tuples[0][0] = 0
        
        # 检查矩阵有效性
        if valid:
            # 验证列和
            col_sum_check = [0] * cols
            for col_item in col_tuples:
                col_sum_check[col_item[1]] = col_item[0]
            if any(x != 0 for x in col_sum_check):
                continue
                
            # 验证行和（额外检查）
            for i, row in enumerate(matrix):
                row_count = sum(row)
                if not (2 <= row_count <= 4):
                    valid = False
                    break
            # 验证列和（额外检查）
            if valid:
                for j in range(cols):
                    col_count = sum(matrix[i][j] for i in range(rows))
                    if not (2 <= col_count <= 4):
                        valid = False
                        break
            if valid:
                return matrix
                
    raise ValueError(f"Failed to generate matrix after {max_attempts} attempts. Try adjusting parameters.")

def get_nonzero_indices(matrix):
    """
    返回矩阵中所有非零元素的下标 (row, col)
    """
    return [(i, j) for i in range(len(matrix)) 
                   for j in range(len(matrix[0])) 
                   if matrix[i][j] != 0]

def generate_sudoku_positions(n):
    matrix = generate_sparse_matrix(n)
    nonzero_indices = get_nonzero_indices(matrix)
    return nonzero_indices