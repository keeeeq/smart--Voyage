-- ============================
-- SmartVoyage 测试数据插入脚本
-- ============================
-- 运行方式: mysql -u root -p smart_voyage < database/insert_test_data.sql

USE smart_voyage;

-- 清空旧数据（可选）
-- TRUNCATE TABLE train_ticket;
-- TRUNCATE TABLE flight_ticket;
-- TRUNCATE TABLE concert_ticket;

-- ============================
-- 火车票测试数据
-- ============================
INSERT INTO train_ticket (train_no, from_city, from_station, departure_time, to_city, to_station, arrival_time, travel_date, duration, price_second, price_first, stock_second, stock_first) VALUES
-- 北京-上海
('G1', '北京', '北京南站', '07:00', '上海', '上海虹桥', '11:36', CURDATE(), '4h36m', 553.00, 933.00, 100, 50),
('G3', '北京', '北京南站', '08:00', '上海', '上海虹桥', '12:40', CURDATE(), '4h40m', 553.00, 933.00, 80, 30),
('G5', '北京', '北京南站', '09:00', '上海', '上海虹桥', '13:28', CURDATE(), '4h28m', 553.00, 933.00, 120, 60),
('G7', '北京', '北京南站', '10:00', '上海', '上海虹桥', '14:36', CURDATE(), '4h36m', 553.00, 933.00, 150, 80),
-- 上海-北京
('G2', '上海', '上海虹桥', '07:00', '北京', '北京南站', '11:30', CURDATE(), '4h30m', 553.00, 933.00, 90, 40),
('G4', '上海', '上海虹桥', '08:00', '北京', '北京南站', '12:36', CURDATE(), '4h36m', 553.00, 933.00, 100, 50),
-- 北京-杭州
('G31', '北京', '北京南站', '08:05', '杭州', '杭州东站', '13:23', CURDATE(), '5h18m', 626.00, 1056.00, 80, 40),
('G33', '北京', '北京南站', '09:15', '杭州', '杭州东站', '14:48', CURDATE(), '5h33m', 626.00, 1056.00, 60, 30),
-- 上海-杭州
('G7501', '上海', '上海虹桥', '07:00', '杭州', '杭州东站', '07:59', CURDATE(), '59m', 73.00, 117.00, 200, 100),
('G7503', '上海', '上海虹桥', '07:30', '杭州', '杭州东站', '08:29', CURDATE(), '59m', 73.00, 117.00, 180, 90),
-- 明天的票
('G1', '北京', '北京南站', '07:00', '上海', '上海虹桥', '11:36', DATE_ADD(CURDATE(), INTERVAL 1 DAY), '4h36m', 553.00, 933.00, 200, 100),
('G3', '北京', '北京南站', '08:00', '上海', '上海虹桥', '12:40', DATE_ADD(CURDATE(), INTERVAL 1 DAY), '4h40m', 553.00, 933.00, 180, 80)
ON DUPLICATE KEY UPDATE stock_second = VALUES(stock_second), stock_first = VALUES(stock_first);

-- ============================
-- 机票测试数据
-- ============================
INSERT INTO flight_ticket (flight_no, airline, from_city, from_airport, departure_time, to_city, to_airport, arrival_time, flight_date, duration, price_economy, price_business, discount) VALUES
-- 北京-上海
('CA1501', '中国国航', '北京', '首都机场T3', CONCAT(CURDATE(), ' 07:00:00'), '上海', '虹桥机场T2', CONCAT(CURDATE(), ' 09:20:00'), CURDATE(), '2h20m', 1200.00, 3600.00, 0.8),
('MU5101', '东方航空', '北京', '大兴机场', CONCAT(CURDATE(), ' 08:00:00'), '上海', '浦东机场T1', CONCAT(CURDATE(), ' 10:30:00'), CURDATE(), '2h30m', 1100.00, 3300.00, 0.7),
('CZ3101', '南方航空', '北京', '大兴机场', CONCAT(CURDATE(), ' 09:00:00'), '上海', '虹桥机场T2', CONCAT(CURDATE(), ' 11:15:00'), CURDATE(), '2h15m', 1150.00, 3450.00, 0.75),
-- 上海-北京
('CA1502', '中国国航', '上海', '虹桥机场T2', CONCAT(CURDATE(), ' 07:30:00'), '北京', '首都机场T3', CONCAT(CURDATE(), ' 09:50:00'), CURDATE(), '2h20m', 1200.00, 3600.00, 0.8),
('MU5102', '东方航空', '上海', '浦东机场T1', CONCAT(CURDATE(), ' 08:30:00'), '北京', '大兴机场', CONCAT(CURDATE(), ' 11:00:00'), CURDATE(), '2h30m', 1100.00, 3300.00, 0.7),
-- 北京-广州
('CA1301', '中国国航', '北京', '首都机场T3', CONCAT(CURDATE(), ' 07:00:00'), '广州', '白云机场T2', CONCAT(CURDATE(), ' 10:10:00'), CURDATE(), '3h10m', 1600.00, 4800.00, 0.65),
('CZ3001', '南方航空', '北京', '大兴机场', CONCAT(CURDATE(), ' 08:30:00'), '广州', '白云机场T2', CONCAT(CURDATE(), ' 11:35:00'), CURDATE(), '3h05m', 1550.00, 4650.00, 0.7),
-- 上海-深圳
('MU5301', '东方航空', '上海', '浦东机场T1', CONCAT(CURDATE(), ' 08:00:00'), '深圳', '宝安机场T3', CONCAT(CURDATE(), ' 10:30:00'), CURDATE(), '2h30m', 1300.00, 3900.00, 0.75),
-- 明天的航班
('CA1501', '中国国航', '北京', '首都机场T3', CONCAT(DATE_ADD(CURDATE(), INTERVAL 1 DAY), ' 07:00:00'), '上海', '虹桥机场T2', CONCAT(DATE_ADD(CURDATE(), INTERVAL 1 DAY), ' 09:20:00'), DATE_ADD(CURDATE(), INTERVAL 1 DAY), '2h20m', 1200.00, 3600.00, 0.85)
ON DUPLICATE KEY UPDATE price_economy = VALUES(price_economy);

-- ============================
-- 演唱会测试数据
-- ============================
INSERT INTO concert_ticket (concert_name, artist, city, venue, show_date, show_time, status, price_min, price_max, description) VALUES
('周杰伦「嘉年华」世界巡回演唱会-北京站', '周杰伦', '北京', '鸟巢体育场', DATE_ADD(CURDATE(), INTERVAL 30 DAY), '19:30', '预售', 380.00, 1880.00, '周杰伦2026年最新世界巡回演唱会'),
('五月天「人生无限公司」演唱会-上海站', '五月天', '上海', '梅赛德斯奔驰文化中心', DATE_ADD(CURDATE(), INTERVAL 14 DAY), '19:00', '在售', 280.00, 1280.00, '五月天年度大型演唱会'),
('林俊杰「圣所」世界巡回演唱会-广州站', '林俊杰', '广州', '广州体育馆', DATE_ADD(CURDATE(), INTERVAL 21 DAY), '19:30', '在售', 320.00, 1580.00, 'JJ林俊杰最新巡演'),
('薛之谦「天外来物」巡回演唱会-杭州站', '薛之谦', '杭州', '黄龙体育中心', DATE_ADD(CURDATE(), INTERVAL 7 DAY), '19:30', '在售', 280.00, 1280.00, '薛之谦全新专辑巡演'),
('邓紫棋「启示录」世界巡回演唱会-深圳站', '邓紫棋', '深圳', '深圳湾体育中心', DATE_ADD(CURDATE(), INTERVAL 10 DAY), '19:30', '在售', 299.00, 1299.00, 'G.E.M.邓紫棋震撼开唱'),
('华晨宇「火星演唱会」-成都站', '华晨宇', '成都', '成都露天音乐公园', DATE_ADD(CURDATE(), INTERVAL 45 DAY), '19:00', '预售', 380.00, 1680.00, '华晨宇火星系列演唱会'),
('张杰「未·LIVE」巡回演唱会-南京站', '张杰', '南京', '南京奥体中心', DATE_ADD(CURDATE(), INTERVAL 28 DAY), '19:30', '在售', 280.00, 1180.00, '张杰全国巡演南京站')
ON DUPLICATE KEY UPDATE status = VALUES(status);

-- ============================
-- 更新天气数据（确保有今天的数据）
-- ============================
INSERT INTO weather_data (city, city_code, fx_date, temp_max, temp_min, text_day, text_night, humidity, wind_dir_day, precip, uv_index) VALUES
('北京', '101010100', CURDATE(), 5, -3, '晴', '晴', 35, '北风', 0.0, 4),
('北京', '101010100', DATE_ADD(CURDATE(), INTERVAL 1 DAY), 6, -2, '多云', '多云', 40, '东北风', 0.0, 3),
('北京', '101010100', DATE_ADD(CURDATE(), INTERVAL 2 DAY), 4, -4, '阴', '小雪', 55, '西北风', 2.0, 2),
('上海', '101020100', CURDATE(), 12, 5, '多云', '阴', 65, '东风', 0.0, 5),
('上海', '101020100', DATE_ADD(CURDATE(), INTERVAL 1 DAY), 14, 7, '晴', '晴', 55, '东南风', 0.0, 6),
('广州', '101280101', CURDATE(), 22, 15, '晴', '晴', 60, '北风', 0.0, 7),
('深圳', '101280601', CURDATE(), 23, 16, '多云', '多云', 65, '东北风', 0.0, 6),
('杭州', '101210101', CURDATE(), 10, 3, '阴', '小雨', 70, '东风', 3.0, 3),
('成都', '101270101', CURDATE(), 12, 6, '阴', '阴', 75, '西风', 0.0, 2),
('南京', '101190101', CURDATE(), 8, 1, '多云', '晴', 50, '西北风', 0.0, 4)
ON DUPLICATE KEY UPDATE temp_max = VALUES(temp_max), temp_min = VALUES(temp_min), text_day = VALUES(text_day);

SELECT '测试数据插入完成！' AS message;
SELECT CONCAT('今天日期: ', CURDATE()) AS today;
SELECT COUNT(*) AS train_count FROM train_ticket;
SELECT COUNT(*) AS flight_count FROM flight_ticket;
SELECT COUNT(*) AS concert_count FROM concert_ticket;
SELECT COUNT(*) AS weather_count FROM weather_data;
