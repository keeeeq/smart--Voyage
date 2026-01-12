-- ============================
-- SmartVoyage 数据库初始化脚本
-- ============================
-- 
-- 知识点：
-- --------
-- 1. CREATE DATABASE IF NOT EXISTS: 如果数据库已存在则不报错
-- 2. CHARACTER SET utf8mb4: 支持 emoji 等 4 字节 Unicode 字符
-- 3. COLLATE utf8mb4_unicode_ci: 不区分大小写的 Unicode 排序规则
-- 4. PRIMARY KEY: 主键，唯一标识每条记录
-- 5. INDEX: 索引，加速查询（在 WHERE、JOIN 常用的列上创建）
-- 6. DECIMAL: 精确小数类型，适合存储金额
-- 7. ENUM: 枚举类型，限制列值只能是预定义的选项

-- 创建数据库
CREATE DATABASE IF NOT EXISTS smart_voyage
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE smart_voyage;

-- ============================
-- 天气数据表
-- ============================
-- 存储各城市的天气预报数据（来自和风天气 API）
CREATE TABLE IF NOT EXISTS weather_data (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    city VARCHAR(50) NOT NULL COMMENT '城市名称',
    city_code VARCHAR(20) NOT NULL COMMENT '城市代码（和风天气 Location ID）',
    fx_date DATE NOT NULL COMMENT '预报日期',
    
    -- 温度信息
    temp_max INT COMMENT '最高温度（摄氏度）',
    temp_min INT COMMENT '最低温度（摄氏度）',
    
    -- 天气状况
    text_day VARCHAR(50) COMMENT '白天天气状况（如：晴、多云、小雨）',
    text_night VARCHAR(50) COMMENT '夜间天气状况',
    icon_day VARCHAR(10) COMMENT '白天天气图标代码',
    icon_night VARCHAR(10) COMMENT '夜间天气图标代码',
    
    -- 风力信息
    wind_dir_day VARCHAR(20) COMMENT '白天风向',
    wind_scale_day VARCHAR(10) COMMENT '白天风力等级',
    wind_dir_night VARCHAR(20) COMMENT '夜间风向',
    wind_scale_night VARCHAR(10) COMMENT '夜间风力等级',
    
    -- 其他气象信息
    humidity INT COMMENT '相对湿度（%）',
    precip DECIMAL(5,2) COMMENT '降水量（毫米）',
    uv_index INT COMMENT '紫外线指数',
    vis INT COMMENT '能见度（公里）',
    
    -- 元数据
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    -- 索引：加速按城市和日期查询
    INDEX idx_city_date (city, fx_date),
    INDEX idx_city_code (city_code),
    
    -- 唯一约束：同一城市同一日期只能有一条记录
    UNIQUE KEY uk_city_date (city, fx_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='天气预报数据表';

-- ============================
-- 火车票数据表
-- ============================
-- 存储火车票信息（可通过爬虫或 API 获取）
CREATE TABLE IF NOT EXISTS train_ticket (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    train_no VARCHAR(20) NOT NULL COMMENT '车次号（如 G1234）',
    
    -- 出发信息
    from_city VARCHAR(50) NOT NULL COMMENT '出发城市',
    from_station VARCHAR(50) NOT NULL COMMENT '出发站',
    departure_time TIME NOT NULL COMMENT '出发时间',
    
    -- 到达信息
    to_city VARCHAR(50) NOT NULL COMMENT '到达城市',
    to_station VARCHAR(50) NOT NULL COMMENT '到达站',
    arrival_time TIME NOT NULL COMMENT '到达时间',
    
    -- 行程信息
    travel_date DATE NOT NULL COMMENT '乘车日期',
    duration VARCHAR(20) COMMENT '行程时长（如 5小时30分）',
    
    -- 票价信息（单位：元）
    price_business DECIMAL(10,2) COMMENT '商务座票价',
    price_first DECIMAL(10,2) COMMENT '一等座票价',
    price_second DECIMAL(10,2) COMMENT '二等座票价',
    price_hard_seat DECIMAL(10,2) COMMENT '硬座票价',
    price_soft_sleeper DECIMAL(10,2) COMMENT '软卧票价',
    price_hard_sleeper DECIMAL(10,2) COMMENT '硬卧票价',
    
    -- 余票信息
    stock_business INT DEFAULT 0 COMMENT '商务座余票',
    stock_first INT DEFAULT 0 COMMENT '一等座余票',
    stock_second INT DEFAULT 0 COMMENT '二等座余票',
    
    -- 元数据
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    -- 索引
    INDEX idx_from_to_date (from_city, to_city, travel_date),
    INDEX idx_train_no (train_no),
    INDEX idx_travel_date (travel_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='火车票信息表';

-- ============================
-- 机票数据表
-- ============================
CREATE TABLE IF NOT EXISTS flight_ticket (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    flight_no VARCHAR(20) NOT NULL COMMENT '航班号（如 CA1234）',
    airline VARCHAR(50) COMMENT '航空公司',
    
    -- 出发信息
    from_city VARCHAR(50) NOT NULL COMMENT '出发城市',
    from_airport VARCHAR(50) NOT NULL COMMENT '出发机场',
    departure_time DATETIME NOT NULL COMMENT '出发时间',
    
    -- 到达信息
    to_city VARCHAR(50) NOT NULL COMMENT '到达城市',
    to_airport VARCHAR(50) NOT NULL COMMENT '到达机场',
    arrival_time DATETIME NOT NULL COMMENT '到达时间',
    
    -- 航班信息
    flight_date DATE NOT NULL COMMENT '航班日期',
    duration VARCHAR(20) COMMENT '飞行时长',
    aircraft_type VARCHAR(50) COMMENT '机型',
    
    -- 票价信息
    price_economy DECIMAL(10,2) COMMENT '经济舱票价',
    price_business DECIMAL(10,2) COMMENT '商务舱票价',
    price_first DECIMAL(10,2) COMMENT '头等舱票价',
    
    -- 折扣信息
    discount DECIMAL(3,2) COMMENT '折扣（如 0.7 表示 7 折）',
    
    -- 元数据
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    -- 索引
    INDEX idx_from_to_date (from_city, to_city, flight_date),
    INDEX idx_flight_no (flight_no)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='机票信息表';

-- ============================
-- 演唱会票务表
-- ============================
CREATE TABLE IF NOT EXISTS concert_ticket (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    concert_name VARCHAR(200) NOT NULL COMMENT '演唱会名称',
    artist VARCHAR(100) NOT NULL COMMENT '艺人/乐队名称',
    
    -- 场地信息
    city VARCHAR(50) NOT NULL COMMENT '城市',
    venue VARCHAR(100) NOT NULL COMMENT '场馆名称',
    
    -- 时间信息
    show_date DATE NOT NULL COMMENT '演出日期',
    show_time TIME COMMENT '演出时间',
    
    -- 票务信息
    status ENUM('预售', '在售', '售罄', '已结束') DEFAULT '在售' COMMENT '售票状态',
    price_min DECIMAL(10,2) COMMENT '最低票价',
    price_max DECIMAL(10,2) COMMENT '最高票价',
    
    -- 其他信息
    description TEXT COMMENT '演出介绍',
    ticket_url VARCHAR(500) COMMENT '购票链接',
    
    -- 元数据
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    -- 索引
    INDEX idx_city_date (city, show_date),
    INDEX idx_artist (artist),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='演唱会票务信息表';

-- ============================
-- 城市代码表
-- ============================
-- 存储城市名称与和风天气城市代码的映射
CREATE TABLE IF NOT EXISTS city_code (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    city_name VARCHAR(50) NOT NULL COMMENT '城市名称',
    city_code VARCHAR(20) NOT NULL COMMENT '城市代码（和风天气 Location ID）',
    province VARCHAR(50) COMMENT '省份',
    
    -- 唯一约束
    UNIQUE KEY uk_city_name (city_name),
    INDEX idx_city_code (city_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='城市代码映射表';

-- ============================
-- 插入热门城市代码（和风天气 Location ID）
-- ============================
INSERT IGNORE INTO city_code (city_name, city_code, province) VALUES
('北京', '101010100', '北京'),
('上海', '101020100', '上海'),
('广州', '101280101', '广东'),
('深圳', '101280601', '广东'),
('杭州', '101210101', '浙江'),
('南京', '101190101', '江苏'),
('成都', '101270101', '四川'),
('重庆', '101040100', '重庆'),
('武汉', '101200101', '湖北'),
('西安', '101110101', '陕西'),
('苏州', '101190401', '江苏'),
('天津', '101030100', '天津'),
('长沙', '101250101', '湖南'),
('郑州', '101180101', '河南'),
('青岛', '101120201', '山东'),
('大连', '101070201', '辽宁'),
('厦门', '101230201', '福建'),
('昆明', '101290101', '云南'),
('三亚', '101310201', '海南'),
('拉萨', '101140101', '西藏');

-- ============================
-- 插入示例天气数据
-- ============================
INSERT IGNORE INTO weather_data (city, city_code, fx_date, temp_max, temp_min, text_day, text_night, humidity, uv_index) VALUES
('北京', '101010100', CURDATE(), 28, 18, '晴', '多云', 45, 6),
('北京', '101010100', DATE_ADD(CURDATE(), INTERVAL 1 DAY), 30, 20, '多云', '多云', 50, 5),
('北京', '101010100', DATE_ADD(CURDATE(), INTERVAL 2 DAY), 27, 19, '小雨', '阴', 70, 3),
('上海', '101020100', CURDATE(), 32, 25, '多云', '多云', 65, 7),
('上海', '101020100', DATE_ADD(CURDATE(), INTERVAL 1 DAY), 33, 26, '晴', '晴', 60, 8),
('广州', '101280101', CURDATE(), 35, 27, '晴', '晴', 70, 9),
('深圳', '101280601', CURDATE(), 34, 26, '多云', '阵雨', 75, 8);

-- ============================
-- 插入示例火车票数据
-- ============================
INSERT IGNORE INTO train_ticket (train_no, from_city, from_station, departure_time, to_city, to_station, arrival_time, travel_date, duration, price_second, price_first, stock_second, stock_first) VALUES
('G1', '北京', '北京南站', '07:00', '上海', '上海虹桥站', '11:36', CURDATE(), '4小时36分', 553.00, 933.00, 100, 50),
('G3', '北京', '北京南站', '08:00', '上海', '上海虹桥站', '12:40', CURDATE(), '4小时40分', 553.00, 933.00, 80, 30),
('G5', '北京', '北京南站', '09:00', '上海', '上海虹桥站', '13:28', CURDATE(), '4小时28分', 553.00, 933.00, 120, 60),
('G7', '上海', '上海虹桥站', '07:00', '北京', '北京南站', '11:30', CURDATE(), '4小时30分', 553.00, 933.00, 90, 40),
('D301', '北京', '北京南站', '20:00', '上海', '上海站', '07:20', DATE_ADD(CURDATE(), INTERVAL 1 DAY), '11小时20分', 309.00, 494.00, 200, 100);

SELECT '数据库初始化完成！' AS message;
