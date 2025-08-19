from datetime import datetime, timedelta

def is_rest_day(day_in_cycle, work_rest_pattern):
    """
    判断某一天是否是休息日
    day_in_cycle: 当前是周期内的第几天（从0开始）
    work_rest_pattern: [工作天数, 休息天数]
    """
    work_days, rest_days = work_rest_pattern
    cycle = work_days + rest_days
    return (day_in_cycle % cycle) >= work_days

def count_substitute_days(start_date, end_date, worker_info, m):
    """
    主函数：统计替补护士代班天数
    
    参数：
    start_date: 起始日期 [year, month, day]
    end_date: 结束日期 [year, month, day]（ year_start < year_end < year_start + 10 ）
    worker_info: 护士工作制二维数组 [[work_days1, rest_days1], ...]，如 [[3,1], [5,2]]
    m: 少于m个护士上班时需要替补护士上班，（0 < m < n）
    
    返回：
    替补护士需要代班的总天数
    """
    # 转换为 datetime 对象
    start = datetime(*start_date)
    end = datetime(*end_date)

    # 检查起始和结束日期是否合法
    if start > end:
        raise ValueError("起始日期不能晚于结束日期")

    # 计算总天数
    total_days = (end - start).days + 1
    print(total_days)

    substitute_days = 0

    for day in range(total_days):
        current_day_in_cycle = day  # 假设周期从第一天开始计算

        working_nurses = 0
        for pattern in worker_info:
            if not is_rest_day(current_day_in_cycle, pattern):
                working_nurses += 1

        if working_nurses < m:
            substitute_days += 1

    return substitute_days

# ========================
# ====== 示例使用 ========
# ========================

if __name__ == "__main__":
    # start_date = [2019, 1, 1]
    # end_date = [2019, 12, 31]
    # worker_info = [[3, 1], [5, 2]]  # A: 工作3天休1天；B: 工作5天休2天
    # m = 1  # 当少于1个护士上班时，替补护士要上班（即没人上班时才上）

    start_date = [2019, 3, 15]
    end_date = [2019, 8, 27]
    worker_info = [[3,3], [8,6], [5,1], [4,4], [6,5]]
    m = 1 

    result = count_substitute_days(start_date, end_date, worker_info, m)
    print(f"在 {start_date} 到 {end_date} 之间，替补护士共需代班 {result} 天")


    # 问题：
    # 某医院有2名正式护士A、B和1名替补护士C，从2019年1月1日开始到2019年12月31日为止，A每工作3天休息1天，B每工作5天休息2天。如果某天正式护士上班的人数少于1人，那么需要替补护士C代班。则在这段时间内，替补护士C需要代班几天？

    # 某医院有3名正式护士A、B、C和1名替补护士D，从2022年2月11日开始到2024年6月24日为止，A每工作3天休息1天，B每工作5天休息2天，C每工作7天休息3天。如果某天正式护士上班的人数少于2人，那么需要替补护士D代班。则在这段时间内，替补护士D需要代班几天？