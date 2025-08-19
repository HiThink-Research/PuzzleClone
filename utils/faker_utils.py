from faker import Faker
from faker.providers import DynamicProvider

providers = [DynamicProvider(
    provider_name="major",
    elements=[
        "计算机科学", "软件工程", "人工智能", 
        "电子信息工程", "机械工程", "土木工程",
        "金融学", "经济学", "会计学",
        "临床医学", "护理学", "药学",
        "法学", "新闻传播学", "教育学",
        "数学与应用数学", "物理学", "化学",
        "英语", "日语", "法语",
        "美术学", "音乐学", "舞蹈学"
    ]
), DynamicProvider(
    provider_name="color_name_cn",
    elements=[
        "红色", "橙色", "黄色", "绿色", "蓝色",
        "靛蓝", "紫色", "粉色", "棕色", "灰色",
        "黑色", "白色", "金色", "银色", "青色",
        "珊瑚色", "栗色", "橄榄色", "藏青色", "茶色",
        "米色", "卡其色", "琥珀色", "翡翠绿", "天蓝色",
        "桃红色", "紫红色", "柠檬黄", "象牙白", "咖啡色"
    ]
), DynamicProvider(
    provider_name="chinese_drink",
    elements=[
        "可口可乐", "雪碧", "芬达", "冰红茶", "绿茶",
        "乌龙茶", "珍珠奶茶", "拿铁咖啡", "美式咖啡", "橙汁",
        "苹果汁", "葡萄汁", "柠檬水", "矿泉水", "苏打水",
        "椰汁", "杏仁露", "酸梅汤", "王老吉", "红牛"
    ]
), DynamicProvider(
    provider_name="pet_category",
    elements=[
        "猫", "狗", "仓鼠", "兔子", "鹦鹉",
        "金鱼", "乌龟", "蜥蜴", "蛇", "蜘蛛",
        "荷兰猪", "龙猫", "刺猬", "蜜袋鼯", "宠物猪",
        "八哥", "鸽子", "孔雀鱼", "蝾螈", "变色龙"
    ]
), DynamicProvider(
    provider_name="fruit_cn",
    elements=[
        "苹果", "香蕉", "橙子", "梨", "葡萄",
        "草莓", "西瓜", "桃子", "李子", "菠萝",
        "芒果", "猕猴桃", "樱桃", "蓝莓", "石榴",
        "柚子", "柠檬", "火龙果", "荔枝", "龙眼",
        "山竹", "榴莲", "椰子", "木瓜", "杨桃",
        "百香果", "桑葚", "无花果", "柿子", "哈密瓜"
    ]
), DynamicProvider(
    provider_name="hobby_cn",
    elements=[
        # 艺术类
        "摄影", "绘画", "书法", "雕塑", "陶艺",
        # 音乐类
        "钢琴", "吉他", "小提琴", "声乐", "作曲",
        # 舞蹈类
        "芭蕾舞", "街舞", "民族舞", "拉丁舞", "现代舞",
        # 运动类
        "篮球", "足球", "羽毛球", "游泳", "瑜伽",
        # 手工类
        "编织", "木工", "烘焙", "插花", "手工皮具",
        # 其他
        "阅读", "写作", "旅行", "棋牌", "园艺"
    ]
), DynamicProvider(
    provider_name="foreign_name_cn",
    elements=[
        # 男性常见译名
        "约翰", "迈克尔", "大卫", "詹姆斯", "罗伯特",
        "威廉", "理查德", "查尔斯", "约瑟夫", "托马斯",
        "丹尼尔", "马修", "安东尼", "唐纳德", "史蒂文",
        "保罗", "马克", "乔治", "肯尼思", "爱德华",
        
        # 女性常见译名
        "玛丽", "安娜", "丽莎", "米歇尔", "桑德拉",
        "艾米", "杰西卡", "莎拉", "金伯利", "伊丽莎白",
        "玛格丽特", "艾玛", "朱莉娅", "凯瑟琳", "南希",
        "劳拉", "维多利亚", "奥利维亚", "索菲娅", "艾米丽",
        
        # 中性译名
        "克里斯", "亚历克斯", "泰勒", "乔丹", "凯瑞"
    ]
), DynamicProvider(
    provider_name="product_cn",
    elements=[
        # 食品类
        "奶油饼干", "巧克力蛋糕", "草莓冰淇淋", "全麦面包", "芝士披萨",
        "牛肉干", "水果罐头", "酸奶", "薯片", "坚果礼盒",
        # 饮料类
        "冰红茶", "拿铁咖啡", "鲜榨橙汁", "珍珠奶茶", "气泡水",
        # 日用品类
        "洗衣液", "洗发水", "牙膏", "抽纸", "保鲜膜",
        # 电子产品
        "无线耳机", "智能手表", "蓝牙音箱", "充电宝", "电子书阅读器",
        # 服饰类
        "纯棉T恤", "牛仔裤", "运动鞋", "羽绒服", "针织帽"
    ]
), DynamicProvider(
    provider_name="car_brand",
    elements=[
        # 德系品牌
        "奥迪", "宝马", "奔驰", "大众", "保时捷",
        # 日系品牌
        "丰田", "本田", "日产", "马自达", "雷克萨斯",
        # 美系品牌
        "福特", "雪佛兰", "凯迪拉克", "特斯拉", "林肯",
        # 韩系品牌
        "现代", "起亚", "捷尼赛思",
        # 国产品牌
        "比亚迪", "吉利", "长城", "长安", "红旗",
        # 意大利品牌
        "法拉利", "兰博基尼", "玛莎拉蒂", "阿尔法·罗密欧",
        # 英国品牌
        "路虎", "捷豹", "宾利", "劳斯莱斯",
        # 法系品牌
        "标致", "雪铁龙", "雷诺", "DS"
    ]
), DynamicProvider(
    provider_name="occupation_cn",
    elements=[
        # 医疗健康类
        "医生", "护士", "药剂师", "牙医", "心理医生",
        # 教育类
        "教师", "大学教授", "幼儿园老师", "校长", "辅导员",
        # 科技类
        "软件工程师", "数据分析师", "人工智能工程师", "网络安全专家", "系统架构师",
        # 金融类
        "会计师", "金融分析师", "投资顾问", "银行职员", "保险经纪人",
        # 艺术创意类
        "设计师", "摄影师", "作家", "画家", "音乐家",
        # 服务行业
        "厨师", "服务员", "理发师", "导游", "健身教练",
        # 管理类
        "项目经理", "人力资源经理", "运营总监", "市场经理", "销售经理",
        # 蓝领职业
        "电工", "木匠", "水管工", "建筑工人", "汽车修理工"
    ]
), DynamicProvider(
    provider_name="metal_ore",
    elements=[
        "铁矿石", "铜矿石", "铝土矿", "铅锌矿", "镍矿",
        "锡矿石", "钨矿石", "钼矿石", "锰矿石", "铬铁矿",
        "钛铁矿", "钒钛磁铁矿", "金矿石", "银矿石", "铂矿石",
        "稀土矿", "铀矿石", "钴矿石", "锑矿石", "汞矿石"
    ]
), DynamicProvider(
    provider_name="flower_name",
    elements=[
        "樱花", "桃花", "杏花", "海棠", "迎春花", "郁金香",
        "玫瑰", "百合", "茉莉", "栀子花", "向日葵", "睡莲",
        "菊花", "桂花", "芙蓉", "彼岸花", "金盏花", "木芙蓉",
        "腊梅", "山茶", "一品红", "君子兰", "仙客来", "水仙"
    ]
), DynamicProvider(
    provider_name="sport",
    elements=[
        "百米跑", "跳高", "跳远", "铅球", "标枪", 
        "110米栏", "撑杆跳高", "三级跳远", "马拉松", "链球",
        "足球", "篮球", "排球", "乒乓球", "羽毛球",
        "网球", "棒球", "垒球", "手球", "曲棍球",
        "自由泳", "蛙泳", "蝶泳", "仰泳", "跳水",
        "水球", "花样游泳", "皮划艇", "赛艇", "帆船",
        "自由体操", "鞍马", "吊环", "跳马", "双杠",
        "单杠", "高低杠", "平衡木", "艺术体操", "蹦床",
        "举重", "拳击", "击剑", "跆拳道", "柔道",
        "摔跤", "射击", "射箭", "自行车", "马术"
    ]
), DynamicProvider(
    provider_name="office_supplies",
    elements=[
        '手机', '笔记本', '鼠标', 'U盘', '签字笔',
        '订书机', '胶带', '便签纸', '计算器', '耳机',
        '移动硬盘', '充电器', '墨水', '文件夹', '便利贴'
    ]
)]
from faker import Faker

def get_faker(num, provider_name, locale='zh_CN', seed=None):
    """
    Generate a specified number of unique fake data entries using Faker.

    Parameters:
        num: The number of data entries to generate.

        provider_name: Name of the provider (also the method name to call).

        providers: List of provider classes to add.

        locale: Locale setting (default is Chinese).
        
        seed: Random seed.

    Returns:
        A list of generated unique data.

    Exceptions:
        AttributeError: When the provider_name does not exist.
        
        ValueError: When it is not possible to generate enough unique data.
    """
    fake = Faker(locale)
    if seed is not None:
        fake.seed(seed)
    
    # 添加自定义Providers
    for provider in providers:
        fake.add_provider(provider)
    
    # 检查provider是否存在
    if not hasattr(fake, provider_name):
        raise AttributeError(f"Faker has no provider named '{provider_name}'")
    
    method = getattr(fake, provider_name)
    results = set()
    max_attempts = num * 100  # 最大尝试次数
    attempts = 0
    
    # 生成唯一数据
    while len(results) < num and attempts < max_attempts:
        data = method()
        results.add(data)
        attempts += 1
    
    # 检查是否生成足够数据
    if len(results) < num:
        raise ValueError(
            f"Only generated {len(results)}/{num} unique elements after {max_attempts} attempts. "
            f"Try increasing max attempts or using a different provider."
        )
    
    return list(results)