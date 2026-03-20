"""
DateTimeStrategy 新参数测试用例

覆盖 anchor, offset, timezone, date_range, time_range, specific_date, specific_time 等新参数
"""
import re
from datetime import datetime

import pytest

from data_builder import DateTimeStrategy, StrategyContext, DataBuilder, BuilderConfig, FieldPolicy
from data_builder import datetime as datetime_strategy
from data_builder.strategies.value.registry import StrategyRegistry


def _ctx(**kwargs):
    """创建测试用 StrategyContext"""
    defaults = dict(field_path="test", field_schema={}, root_data={}, parent_data={}, index=0)
    defaults.update(kwargs)
    return StrategyContext(**defaults)


class TestAnchorKeyword:
    """anchor 关键字测试"""

    def test_anchor_now(self):
        """anchor="now" - 当前时刻附近"""
        s = DateTimeStrategy(anchor="now")
        v = s.generate(_ctx())
        # 验证格式
        assert re.match(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", v)

    def test_anchor_today(self):
        """anchor="today" - 今天范围内"""
        s = DateTimeStrategy(anchor="today")
        v = s.generate(_ctx())
        # 验证格式
        assert re.match(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", v)
        # 验证是今天
        today = datetime.now().strftime("%Y-%m-%d")
        assert v.startswith(today)

    def test_anchor_yesterday(self):
        """anchor="yesterday" - 昨天范围内"""
        s = DateTimeStrategy(anchor="yesterday")
        v = s.generate(_ctx())
        # 验证格式
        assert re.match(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", v)

    def test_anchor_week(self):
        """anchor="week" - 本周范围内"""
        s = DateTimeStrategy(anchor="week")
        v = s.generate(_ctx())
        # 验证格式
        assert re.match(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", v)

    def test_anchor_month(self):
        """anchor="month" - 本月范围内"""
        s = DateTimeStrategy(anchor="month")
        v = s.generate(_ctx())
        # 验证格式
        assert re.match(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", v)
        # 验证是当月
        current_month = datetime.now().strftime("%Y-%m")
        assert v.startswith(current_month)

    def test_anchor_year(self):
        """anchor="year" - 今年范围内"""
        s = DateTimeStrategy(anchor="year")
        v = s.generate(_ctx())
        # 验证格式
        assert re.match(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", v)
        # 验证是今年
        current_year = datetime.now().strftime("%Y")
        assert v.startswith(current_year)


class TestOffset:
    """offset 偏移量测试"""

    def test_offset_days_positive(self):
        """offset="+1d" - 天的正向偏移"""
        s = DateTimeStrategy(anchor="today", offset="+1d")
        v = s.generate(_ctx())
        assert re.match(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", v)

    def test_offset_days_negative(self):
        """offset="-1d" - 天的负向偏移"""
        s = DateTimeStrategy(anchor="today", offset="-1d")
        v = s.generate(_ctx())
        assert re.match(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", v)

    def test_offset_hours_positive(self):
        """offset="+2h" - 小时的偏移"""
        s = DateTimeStrategy(anchor="now", offset="+2h")
        v = s.generate(_ctx())
        assert re.match(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", v)

    def test_offset_hours_negative(self):
        """offset="-2h" - 小时的负向偏移"""
        s = DateTimeStrategy(anchor="now", offset="-2h")
        v = s.generate(_ctx())
        assert re.match(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", v)

    def test_offset_weeks_positive(self):
        """offset="+1w" - 周的偏移"""
        s = DateTimeStrategy(anchor="today", offset="+1w")
        v = s.generate(_ctx())
        assert re.match(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", v)

    def test_offset_weeks_negative(self):
        """offset="-1w" - 周的负向偏移"""
        s = DateTimeStrategy(anchor="today", offset="-1w")
        v = s.generate(_ctx())
        assert re.match(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", v)

    def test_offset_months_positive(self):
        """offset="+1M" - 月的偏移"""
        s = DateTimeStrategy(anchor="today", offset="+1M")
        v = s.generate(_ctx())
        assert re.match(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", v)

    def test_offset_months_negative(self):
        """offset="-1M" - 月的负向偏移"""
        s = DateTimeStrategy(anchor="today", offset="-1M")
        v = s.generate(_ctx())
        assert re.match(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", v)

    def test_offset_combined(self):
        """offset="+1d 2h 30m" - 组合偏移"""
        s = DateTimeStrategy(anchor="today", offset="+1d 2h 30m")
        v = s.generate(_ctx())
        assert re.match(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", v)


class TestTimezone:
    """timezone 时区测试"""

    def test_timezone_utc(self):
        """timezone="UTC" - UTC 时区"""
        s = DateTimeStrategy(anchor="now", timezone="UTC")
        v = s.generate(_ctx())
        assert re.match(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", v)

    def test_timezone_iana(self):
        """timezone="Asia/Shanghai" - IANA 时区"""
        s = DateTimeStrategy(anchor="now", timezone="Asia/Shanghai")
        v = s.generate(_ctx())
        assert re.match(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", v)

    def test_timezone_offset(self):
        """timezone="+08:00" - UTC 偏移"""
        s = DateTimeStrategy(anchor="now", timezone="+08:00")
        v = s.generate(_ctx())
        assert re.match(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", v)

    def test_timezone_negative_offset(self):
        """timezone="-05:00" - 负 UTC 偏移"""
        s = DateTimeStrategy(anchor="now", timezone="-05:00")
        v = s.generate(_ctx())
        assert re.match(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", v)


class TestDateRange:
    """date_range 测试"""

    def test_date_range_month(self):
        """date_range="2024-01-01,2024-01-31" - 月内范围"""
        s = DateTimeStrategy(date_range="2024-01-01,2024-01-31")
        for _ in range(10):
            v = s.generate(_ctx())
            dt = datetime.strptime(v, "%Y-%m-%d %H:%M:%S")
            assert datetime(2024, 1, 1) <= dt <= datetime(2024, 1, 31, 23, 59, 59)

    def test_date_range_single_day(self):
        """date_range="2024-01-15,2024-01-15" - 单日范围"""
        s = DateTimeStrategy(date_range="2024-01-15,2024-01-15")
        for _ in range(10):
            v = s.generate(_ctx())
            assert v.startswith("2024-01-15")

    def test_date_range_year(self):
        """date_range="2024-01-01,2024-12-31" - 年内范围"""
        s = DateTimeStrategy(date_range="2024-01-01,2024-12-31")
        for _ in range(10):
            v = s.generate(_ctx())
            dt = datetime.strptime(v, "%Y-%m-%d %H:%M:%S")
            assert datetime(2024, 1, 1) <= dt <= datetime(2024, 12, 31, 23, 59, 59)


class TestTimeRange:
    """time_range 测试"""

    def test_time_range_work_hours(self):
        """time_range="09:00:00,17:00:00" - 工作时间范围"""
        s = DateTimeStrategy(date_range="2024-01-15,2024-01-15", time_range="09:00:00,17:00:00")
        for _ in range(10):
            v = s.generate(_ctx())
            # 提取时间部分
            time_part = v.split(" ")[1]
            hour = int(time_part.split(":")[0])
            assert 9 <= hour <= 17

    def test_time_range_full_day(self):
        """time_range="00:00:00,23:59:59" - 全天范围"""
        s = DateTimeStrategy(date_range="2024-01-15,2024-01-15", time_range="00:00:00,23:59:59")
        v = s.generate(_ctx())
        assert re.match(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", v)


class TestSpecificDateTime:
    """specific_date/specific_time 测试"""

    def test_specific_date(self):
        """specific_date="2024-05-15" - 指定日期"""
        s = DateTimeStrategy(specific_date="2024-05-15")
        v = s.generate(_ctx())
        assert "2024-05-15" in v

    def test_specific_date_with_time(self):
        """specific_date + specific_time - 指定日期时间"""
        s = DateTimeStrategy(specific_date="2024-05-15", specific_time="14:30:00")
        v = s.generate(_ctx())
        assert "2024-05-15" in v
        assert "14:30:00" in v

    def test_specific_date_with_format(self):
        """specific_date + custom format"""
        s = DateTimeStrategy(specific_date="2024-05-15", format="%Y/%m/%d")
        v = s.generate(_ctx())
        assert "2024/05/15" in v


class TestPriority:
    """参数优先级测试"""

    def test_anchor_priority_over_start_end(self):
        """anchor 优先于 start/end"""
        # anchor 参数应该生效
        s = DateTimeStrategy(anchor="today", start=datetime(2020, 1, 1), end=datetime(2020, 12, 31))
        v = s.generate(_ctx())
        # 应该生成今天的日期，不是 2020 年的
        today = datetime.now().strftime("%Y-%m-%d")
        assert v.startswith(today)

    def test_specific_date_priority_over_date_range(self):
        """specific_date 优先于 date_range"""
        s = DateTimeStrategy(
            specific_date="2024-05-15",
            date_range="2024-01-01,2024-01-31"
        )
        v = s.generate(_ctx())
        # 应该生成 2024-05-15，不是 2024-01 月的
        assert "2024-05-15" in v

    def test_specific_time_priority_over_time_range(self):
        """specific_time 优先于 time_range"""
        s = DateTimeStrategy(
            specific_date="2024-05-15",
            specific_time="14:30:00",
            time_range="09:00:00,17:00:00"
        )
        v = s.generate(_ctx())
        # 应该生成 14:30:00，不是工作时间内
        assert "14:30:00" in v


class TestErrorHandling:
    """错误处理测试"""

    def test_invalid_anchor(self):
        """无效的 anchor 值"""
        s = DateTimeStrategy(anchor="invalid_anchor")
        with pytest.raises(Exception):
            s.generate(_ctx())

    def test_invalid_offset_format(self):
        """无效的 offset 格式"""
        s = DateTimeStrategy(anchor="today", offset="invalid")
        with pytest.raises(Exception):
            s.generate(_ctx())

    def test_invalid_date_range_format(self):
        """无效的 date_range 格式"""
        s = DateTimeStrategy(date_range="invalid")
        with pytest.raises(Exception):
            s.generate(_ctx())

    def test_invalid_time_range_format(self):
        """无效的 time_range 格式"""
        s = DateTimeStrategy(date_range="2024-01-01,2024-01-02", time_range="invalid")
        with pytest.raises(Exception):
            s.generate(_ctx())

    def test_invalid_timezone(self):
        """无效的 timezone"""
        s = DateTimeStrategy(anchor="now", timezone="Invalid/Timezone")
        with pytest.raises(Exception):
            s.generate(_ctx())


class TestRegistryIntegration:
    """通过 Registry 创建测试"""

    def test_registry_with_anchor(self):
        """通过 registry 创建带 anchor 的策略"""
        config = {"type": "datetime", "anchor": "today"}
        s = StrategyRegistry.create(config)
        v = s.generate(_ctx())
        assert re.match(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", v)

    def test_registry_with_date_range(self):
        """通过 registry 创建带 date_range 的策略"""
        config = {"type": "datetime", "date_range": "2024-01-01,2024-01-31"}
        s = StrategyRegistry.create(config)
        v = s.generate(_ctx())
        assert re.match(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", v)

    def test_registry_with_specific_date(self):
        """通过 registry 创建带 specific_date 的策略"""
        config = {"type": "datetime", "specific_date": "2024-05-15"}
        s = StrategyRegistry.create(config)
        v = s.generate(_ctx())
        assert "2024-05-15" in v


class TestBackwardCompatibility:
    """向后兼容性测试"""

    def test_traditional_start_end(self):
        """传统 start/end 参数仍然有效"""
        start = datetime(2020, 1, 1)
        end = datetime(2020, 12, 31)
        s = DateTimeStrategy(start=start, end=end, format="%Y-%m-%d")
        for _ in range(20):
            v = s.generate(_ctx())
            dt = datetime.strptime(v, "%Y-%m-%d")
            assert start <= dt <= end

    def test_default_behavior(self):
        """默认行为（无参数）仍然有效"""
        s = DateTimeStrategy()
        v = s.generate(_ctx())
        assert re.match(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", v)


class TestDataBuilderIntegration:
    """DataBuilder 集成测试 - 验证示例中的完整工作流"""

    def test_basic_integration(self):
        """基础集成测试 - DataBuilder + FieldPolicy + datetime策略"""
        schema = {"type": "object", "properties": {"timestamp": {"type": "string"}}}
        config = BuilderConfig(
            policies=[
                FieldPolicy("timestamp", datetime_strategy(anchor="today")),
            ]
        )
        builder = DataBuilder(schema, config)
        data = builder.build(5)
        
        # 验证生成了数据
        assert len(data) == 5
        for item in data:
            assert "timestamp" in item
            # 验证格式
            assert re.match(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", item["timestamp"])
            # 验证是今天
            today = datetime.now().strftime("%Y-%m-%d")
            assert item["timestamp"].startswith(today)

    def test_multi_field_integration(self):
        """多字段组合测试 - 订单数据场景"""
        schema = {
            "type": "object",
            "properties": {
                "created_at": {"type": "string"},
                "paid_at": {"type": "string"},
                "shipped_at": {"type": "string"},
                "delivered_at": {"type": "string"},
            }
        }
        config = BuilderConfig(
            policies=[
                FieldPolicy("created_at", datetime_strategy(anchor="today")),
                FieldPolicy("paid_at", datetime_strategy(anchor="today", offset="+1h")),
                FieldPolicy("shipped_at", datetime_strategy(anchor="today", offset="+1d")),
                FieldPolicy("delivered_at", datetime_strategy(anchor="today", offset="+3d")),
            ]
        )
        builder = DataBuilder(schema, config)
        data = builder.build(3)
        
        assert len(data) == 3
        for item in data:
            # 验证所有字段存在
            assert "created_at" in item
            assert "paid_at" in item
            assert "shipped_at" in item
            assert "delivered_at" in item
            # 验证格式正确
            assert re.match(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", item["created_at"])
            assert re.match(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", item["paid_at"])
            assert re.match(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", item["shipped_at"])
            assert re.match(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", item["delivered_at"])

    def test_custom_format_integration(self):
        """自定义格式集成测试 - format + anchor + offset"""
        schema = {"type": "object", "properties": {"order_id": {"type": "string"}}}
        config = BuilderConfig(
            policies=[
                FieldPolicy("order_id", datetime_strategy(
                    anchor="now",
                    offset="-1d",
                    format="ORD%Y%m%d%H%M%S"
                )),
            ]
        )
        builder = DataBuilder(schema, config)
        data = builder.build(3)
        
        for item in data:
            # 验证格式前缀
            assert item["order_id"].startswith("ORD")
            # 验证是数字格式 (ORD 后面是 14 位数字)
            assert len(item["order_id"]) == 17  # ORD + 14位数字
            assert item["order_id"][3:].isdigit()

    def test_config_from_dict_integration(self):
        """配置字典加载集成测试 - BuilderConfig.from_dict"""
        config_dict = {
            "policies": [
                {"path": "created_at", "strategy": {"type": "datetime", "anchor": "today"}},
                {"path": "updated_at", "strategy": {"type": "datetime", "anchor": "now"}},
                {"path": "event_date", "strategy": {"type": "datetime", "date_range": "2024-01-01,2024-12-31"}},
            ]
        }
        config = BuilderConfig.from_dict(config_dict)
        schema = {
            "type": "object",
            "properties": {
                "created_at": {"type": "string"},
                "updated_at": {"type": "string"},
                "event_date": {"type": "string"},
            }
        }
        builder = DataBuilder(schema, config)
        data = builder.build(3)
        
        assert len(data) == 3
        for item in data:
            assert "created_at" in item
            assert "updated_at" in item
            assert "event_date" in item
            # 验证格式
            assert re.match(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", item["created_at"])
            assert re.match(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", item["updated_at"])
            # 验证 date_range 生效
            event_dt = datetime.strptime(item["event_date"], "%Y-%m-%d %H:%M:%S")
            assert datetime(2024, 1, 1) <= event_dt <= datetime(2024, 12, 31, 23, 59, 59)
