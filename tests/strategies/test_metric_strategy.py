import pytest
from data_builder.strategies.value.system import MetricStrategy
from data_builder.strategies.basic import StrategyContext
from data_builder.exceptions import StrategyError


class TestMetricStrategyInit:
    """测试 MetricStrategy 初始化"""
    
    def test_default_parameters(self):
        """测试默认参数初始化"""
        strategy = MetricStrategy()
        
        assert strategy.metric_type == "memory"
        assert strategy.data_mode == "current"
        assert strategy.unit == "mb"
        assert strategy.count == 10
        assert strategy.time_interval == 60
        assert strategy.total_range is None
        assert strategy.rate_range is None
    
    @pytest.mark.parametrize("metric_type", ["memory", "swap", "disk", "cpu", "io"])
    def test_valid_metric_types(self, metric_type):
        """测试有效的指标类型"""
        strategy = MetricStrategy(metric_type=metric_type)
        assert strategy.metric_type == metric_type
    
    @pytest.mark.parametrize("data_mode", ["current", "trend"])
    def test_valid_data_modes(self, data_mode):
        """测试有效的数据模式"""
        strategy = MetricStrategy(data_mode=data_mode)
        assert strategy.data_mode == data_mode
    
    @pytest.mark.parametrize("unit", ["byte", "kb", "mb", "gb"])
    def test_valid_units(self, unit):
        """测试有效的单位"""
        strategy = MetricStrategy(unit=unit)
        assert strategy.unit == unit
    
    def test_invalid_metric_type(self):
        """测试无效的指标类型"""
        with pytest.raises(StrategyError, match="不支持的指标类型"):
            MetricStrategy(metric_type="invalid")
    
    def test_invalid_data_mode(self):
        """测试无效的数据模式"""
        with pytest.raises(StrategyError, match="不支持的数据模式"):
            MetricStrategy(data_mode="invalid")
    
    def test_invalid_unit(self):
        """测试无效的单位"""
        with pytest.raises(StrategyError, match="不支持的单位"):
            MetricStrategy(unit="invalid")
    
    def test_invalid_count(self):
        """测试无效的数据点数量"""
        with pytest.raises(StrategyError, match="count 必须 >= 1"):
            MetricStrategy(count=0)
        
        with pytest.raises(StrategyError, match="count 必须 >= 1"):
            MetricStrategy(count=-1)


class TestMetricStrategyGenerate:
    """测试 MetricStrategy 数据生成"""
    
    def setup_method(self):
        """设置测试上下文"""
        self.ctx = StrategyContext(
            field_path="test",
            field_schema={},
            root_data={},
            parent_data={}
        )
    
    def test_memory_current(self):
        """测试内存指标 - 当前值"""
        strategy = MetricStrategy(metric_type="memory", data_mode="current", unit="gb")
        result = strategy.generate(self.ctx)
        
        # 验证结构
        assert isinstance(result, dict)
        assert "total" in result
        assert "used" in result
        assert "usage" in result
        
        # 验证约束
        assert result["total"] > 0
        assert 0 <= result["used"] <= result["total"]
        assert 0 <= result["usage"] <= 100
        
        # 验证计算精度
        expected_usage = round(result["used"] / result["total"] * 100, 2)
        assert abs(result["usage"] - expected_usage) <= 0.01
    
    def test_memory_trend(self):
        """测试内存指标 - 趋势数据"""
        strategy = MetricStrategy(
            metric_type="memory",
            data_mode="trend",
            unit="mb",
            count=5,
            time_interval=60
        )
        result = strategy.generate(self.ctx)
        
        # 验证结构
        assert isinstance(result, list)
        assert len(result) == 5
        
        # 验证每个数据点
        for point in result:
            assert "total" in point
            assert "used" in point
            assert "usage" in point
            assert "timestamp" in point
            
            # 验证约束
            assert 0 <= point["used"] <= point["total"]
            assert 0 <= point["usage"] <= 100
    
    def test_swap_current(self):
        """测试 Swap 指标 - 当前值"""
        strategy = MetricStrategy(metric_type="swap", data_mode="current", unit="mb")
        result = strategy.generate(self.ctx)
        
        assert isinstance(result, dict)
        assert "total" in result
        assert "used" in result
        assert "usage" in result
        assert 0 <= result["used"] <= result["total"]
    
    def test_disk_current_with_custom_range(self):
        """测试磁盘指标 - 自定义容量范围"""
        # 自定义范围：1GB - 10GB（字节）
        total_range = (1024 * 1024 * 1024, 10 * 1024 * 1024 * 1024)
        strategy = MetricStrategy(
            metric_type="disk",
            data_mode="current",
            unit="gb",
            total_range=total_range
        )
        result = strategy.generate(self.ctx)
        
        # 验证范围（允许一定误差）
        assert 1 <= result["total"] <= 10
    
    def test_cpu_current(self):
        """测试 CPU 指标 - 当前值"""
        strategy = MetricStrategy(metric_type="cpu", data_mode="current")
        result = strategy.generate(self.ctx)
        
        # 验证结构
        assert isinstance(result, dict)
        assert "total" in result
        assert "used" in result
        assert "usage" in result
        
        # 验证约束
        assert isinstance(result["total"], int)  # CPU 核数为整数
        assert result["total"] > 0
        assert 0 <= result["used"] <= result["total"]
        assert 0 <= result["usage"] <= 100
        
        # 验证计算精度
        expected_usage = round(result["used"] / result["total"] * 100, 2)
        assert abs(result["usage"] - expected_usage) <= 0.01
    
    def test_cpu_trend(self):
        """测试 CPU 指标 - 趋势数据"""
        strategy = MetricStrategy(
            metric_type="cpu",
            data_mode="trend",
            count=5,
            time_interval=60
        )
        result = strategy.generate(self.ctx)
        
        # 验证结构
        assert isinstance(result, list)
        assert len(result) == 5
        
        # 验证每个数据点
        for point in result:
            assert "total" in point
            assert "used" in point
            assert "usage" in point
            assert "timestamp" in point
            
            # 验证约束
            assert isinstance(point["total"], int)  # CPU 核数为整数
            assert 0 <= point["used"] <= point["total"]
            assert 0 <= point["usage"] <= 100
    
    def test_cpu_unit_ignored(self):
        """测试 CPU 指标 - unit 参数不影响结果"""
        # CPU 的 total 和 used 是核数，不受 unit 参数影响
        strategy_mb = MetricStrategy(metric_type="cpu", unit="mb")
        strategy_gb = MetricStrategy(metric_type="cpu", unit="gb")
        
        result_mb = strategy_mb.generate(self.ctx)
        result_gb = strategy_gb.generate(self.ctx)
        
        # unit 参数对 CPU 指标无影响
        assert isinstance(result_mb["total"], int)
        assert isinstance(result_gb["total"], int)
        
        # 核数范围应在默认范围内（1-128）
        assert 1 <= result_mb["total"] <= 128
        assert 1 <= result_gb["total"] <= 128
    
    def test_cpu_with_custom_range(self):
        """测试 CPU 指标 - 自定义核数范围"""
        # 自定义范围：4-16 核
        strategy = MetricStrategy(
            metric_type="cpu",
            data_mode="current",
            total_range=(4, 16)
        )
        result = strategy.generate(self.ctx)
        
        # 验证范围
        assert 4 <= result["total"] <= 16
        assert isinstance(result["total"], int)
    
    def test_io_current(self):
        """测试 IO 指标 - 当前值"""
        strategy = MetricStrategy(metric_type="io", data_mode="current", unit="mb")
        result = strategy.generate(self.ctx)
        
        # 验证结构
        assert isinstance(result, dict)
        assert "rate_size" in result
        assert "rate_ops" in result
        
        # 验证非负
        assert result["rate_size"] >= 0
        assert result["rate_ops"] >= 0
    
    def test_io_trend_with_custom_range(self):
        """测试 IO 指标 - 自定义速率范围"""
        # 自定义速率范围
        rate_range = {
            "rate_size": (0, 100 * 1024 * 1024),  # 0-100 MB/s
            "rate_ops": (0, 5000)  # 0-5000 IOPS
        }
        strategy = MetricStrategy(
            metric_type="io",
            data_mode="trend",
            unit="mb",
            count=3,
            rate_range=rate_range
        )
        result = strategy.generate(self.ctx)
        
        assert isinstance(result, list)
        assert len(result) == 3
        
        for point in result:
            assert "rate_size" in point
            assert "rate_ops" in point
            assert "timestamp" in point
    
    @pytest.mark.parametrize("unit", ["byte", "kb", "mb", "gb"])
    def test_different_units(self, unit):
        """测试不同单位"""
        strategy = MetricStrategy(metric_type="memory", unit=unit)
        result = strategy.generate(self.ctx)
        
        # byte 单位应为整数，其他为浮点数
        if unit == "byte":
            assert isinstance(result["total"], int)
            assert isinstance(result["used"], int)
        else:
            assert isinstance(result["total"], (int, float))
            assert isinstance(result["used"], (int, float))


class TestMetricStrategyBoundaryValues:
    """测试 MetricStrategy 边界值"""
    
    def test_memory_boundary_values(self):
        """测试内存指标边界值"""
        strategy = MetricStrategy(metric_type="memory", unit="gb")
        boundary = strategy.boundary_values()
        
        assert isinstance(boundary, list)
        assert len(boundary) == 3
        
        # 验证边界情况
        # 边界1: 最小 total, used=0
        assert boundary[0]["used"] == 0
        assert boundary[0]["usage"] == 0.0
        
        # 边界2: 最大 total, used=total
        assert boundary[1]["used"] == boundary[1]["total"]
        assert boundary[1]["usage"] == 100.0
        
        # 边界3: 中间值, used=total/2
        assert boundary[2]["usage"] == 50.0
    
    def test_cpu_boundary_values(self):
        """测试 CPU 指标边界值"""
        strategy = MetricStrategy(metric_type="cpu")
        boundary = strategy.boundary_values()
        
        assert isinstance(boundary, list)
        assert len(boundary) == 3
        
        # 验证边界情况
        # 边界1: 最小核数, used=0
        assert boundary[0]["used"] == 0
        assert boundary[0]["usage"] == 0.0
        assert isinstance(boundary[0]["total"], int)  # 核数为整数
        
        # 边界2: 最大核数, used=total
        assert boundary[1]["used"] == boundary[1]["total"]
        assert boundary[1]["usage"] == 100.0
        assert isinstance(boundary[1]["total"], int)
        
        # 边界3: 中间值, used=total/2
        assert boundary[2]["usage"] == 50.0
        assert isinstance(boundary[2]["total"], int)
    
    def test_io_boundary_values(self):
        """测试 IO 指标边界值"""
        strategy = MetricStrategy(metric_type="io", unit="mb")
        boundary = strategy.boundary_values()
        
        assert isinstance(boundary, list)
        assert len(boundary) == 2
        
        # 验证边界值非负
        for val in boundary:
            assert val["rate_size"] >= 0
            assert val["rate_ops"] >= 0


class TestMetricStrategyEquivalenceClasses:
    """测试 MetricStrategy 等价类"""
    
    def test_memory_equivalence_classes(self):
        """测试内存指标等价类"""
        strategy = MetricStrategy(metric_type="memory", unit="gb")
        classes = strategy.equivalence_classes()
        
        assert isinstance(classes, list)
        assert len(classes) == 3
        
        # 低使用率、中使用率、高使用率
        for cls in classes:
            assert isinstance(cls, list)
            assert len(cls) == 1
            assert "total" in cls[0]
            assert "used" in cls[0]
            assert "usage" in cls[0]
    
    def test_cpu_equivalence_classes(self):
        """测试 CPU 指标等价类"""
        strategy = MetricStrategy(metric_type="cpu")
        classes = strategy.equivalence_classes()
        
        assert isinstance(classes, list)
        assert len(classes) == 3
        
        # 低使用率、中使用率、高使用率
        for cls in classes:
            assert isinstance(cls, list)
            assert len(cls) == 1
            assert "total" in cls[0]
            assert "used" in cls[0]
            assert "usage" in cls[0]
            # CPU 核数为整数
            assert isinstance(cls[0]["total"], int)
    
    def test_io_equivalence_classes(self):
        """测试 IO 指标等价类"""
        strategy = MetricStrategy(metric_type="io", unit="mb")
        classes = strategy.equivalence_classes()
        
        assert isinstance(classes, list)
        assert len(classes) == 3
        
        # 低速率、中速率、高速率
        for cls in classes:
            assert isinstance(cls, list)
            assert "rate_size" in cls[0]
            assert "rate_ops" in cls[0]


class TestMetricStrategyInvalidValues:
    """测试 MetricStrategy 非法值"""
    
    def test_capacity_metric_invalid_values(self):
        """测试容量指标非法值"""
        strategy = MetricStrategy(metric_type="memory")
        invalid = strategy.invalid_values()
        
        assert isinstance(invalid, list)
        assert len(invalid) > 0
        
        # 验证包含典型非法场景
        # used > total
        assert any(v["used"] > v["total"] for v in invalid)
        
        # usage > 100%
        assert any(v["usage"] > 100 for v in invalid)
        
        # 负值
        assert any(v["total"] < 0 or v["used"] < 0 for v in invalid)
        
        # 类型错误
        assert any(not isinstance(v["total"], (int, float)) for v in invalid)
    
    def test_rate_metric_invalid_values(self):
        """测试速率指标非法值"""
        strategy = MetricStrategy(metric_type="io")
        invalid = strategy.invalid_values()
        
        assert isinstance(invalid, list)
        assert len(invalid) > 0
        
        # 验证包含典型非法场景
        # 负值
        assert any(v["rate_size"] < 0 or v["rate_ops"] < 0 for v in invalid)
        
        # 类型错误
        assert any(
            not isinstance(v.get("rate_size"), (int, float)) or
            not isinstance(v.get("rate_ops"), (int, float))
            for v in invalid
        )


class TestMetricStrategyTimestamps:
    """测试时间戳生成"""
    
    def setup_method(self):
        """设置测试上下文"""
        self.ctx = StrategyContext(
            field_path="test",
            field_schema={},
            root_data={},
            parent_data={}
        )
    
    def test_trend_timestamps_order(self):
        """测试趋势数据时间戳顺序（从旧到新）"""
        strategy = MetricStrategy(
            metric_type="memory",
            data_mode="trend",
            count=5,
            time_interval=60
        )
        result = strategy.generate(self.ctx)
        
        # 提取时间戳
        from datetime import datetime
        timestamps = [datetime.strptime(p["timestamp"], "%Y-%m-%d %H:%M:%S") for p in result]
        
        # 验证时间戳递增
        for i in range(len(timestamps) - 1):
            assert timestamps[i] < timestamps[i + 1]
    
    def test_trend_timestamps_interval(self):
        """测试趋势数据时间间隔"""
        strategy = MetricStrategy(
            metric_type="memory",
            data_mode="trend",
            count=5,
            time_interval=60
        )
        result = strategy.generate(self.ctx)
        
        from datetime import datetime
        timestamps = [datetime.strptime(p["timestamp"], "%Y-%m-%d %H:%M:%S") for p in result]
        
        # 验证时间间隔
        for i in range(len(timestamps) - 1):
            delta = (timestamps[i + 1] - timestamps[i]).total_seconds()
            assert delta == 60


class TestMetricStrategyValues:
    """测试 values() 方法"""
    
    def test_values_returns_none(self):
        """测试 values() 返回 None（不可枚举）"""
        strategy = MetricStrategy()
        assert strategy.values() is None


class TestMetricStrategyRegistry:
    """测试策略注册"""
    
    def test_registry_has_metric(self):
        """测试策略已注册"""
        from data_builder.strategies.value.registry import StrategyRegistry
        
        assert StrategyRegistry.has("metric")
    
    def test_create_from_registry(self):
        """测试从注册表创建策略"""
        from data_builder.strategies.value.registry import StrategyRegistry
        
        config = {
            "type": "metric",
            "metric_type": "memory",
            "data_mode": "current",
            "unit": "gb"
        }
        
        strategy = StrategyRegistry.create(config)
        assert isinstance(strategy, MetricStrategy)
        assert strategy.metric_type == "memory"
        assert strategy.data_mode == "current"
        assert strategy.unit == "gb"
    
    def test_param_aliases(self):
        """测试参数别名映射"""
        from data_builder.strategies.value.registry import StrategyRegistry
        
        # 使用别名
        config = {
            "type": "metric",
            "metric_type": "memory",  # 映射到 metric_type
            "mode": "current",  # 映射到 data_mode
            "interval": 120  # 映射到 time_interval
        }
        
        strategy = StrategyRegistry.create(config)
        assert strategy.metric_type == "memory"
        assert strategy.data_mode == "current"
        assert strategy.time_interval == 120


class TestMetricStrategyTrendInit:
    """测试趋势模式参数初始化"""
    
    def test_default_trend_mode(self):
        """测试默认趋势模式为 random"""
        strategy = MetricStrategy()
        assert strategy.trend_mode == "random"
        assert strategy.trend_field == "used"
        assert strategy.trend_range is None
    
    @pytest.mark.parametrize("trend_mode", ["random", "increase", "decrease", "stable", "increase_decrease", "decrease_increase"])
    def test_valid_trend_modes(self, trend_mode):
        """测试有效的趋势模式"""
        strategy = MetricStrategy(trend_mode=trend_mode)
        assert strategy.trend_mode == trend_mode
    
    @pytest.mark.parametrize("trend_field", ["used", "usage"])
    def test_valid_trend_fields(self, trend_field):
        """测试有效的趋势字段"""
        strategy = MetricStrategy(trend_field=trend_field)
        assert strategy.trend_field == trend_field
    
    def test_invalid_trend_mode(self):
        """测试无效的趋势模式"""
        with pytest.raises(StrategyError, match="不支持的趋势模式"):
            MetricStrategy(trend_mode="invalid")
    
    def test_invalid_trend_field(self):
        """测试无效的趋势字段"""
        with pytest.raises(StrategyError, match="容量指标不支持趋势字段"):
            MetricStrategy(metric_type="memory", trend_field="invalid")
    
    def test_invalid_trend_range_format(self):
        """测试无效的趋势范围格式"""
        with pytest.raises(StrategyError, match="trend_range 必须是包含 2 个元素的元组或列表"):
            MetricStrategy(trend_range=(1, 2, 3))
        
        with pytest.raises(StrategyError, match="trend_range 必须是包含 2 个元素的元组或列表"):
            MetricStrategy(trend_range=[1])


class TestMetricStrategyTrendModes:
    """测试趋势模式数据生成"""
    
    def setup_method(self):
        """设置测试上下文"""
        self.ctx = StrategyContext(
            field_path="test",
            field_schema={},
            root_data={},
            parent_data={}
        )
    
    def test_increase_trend(self):
        """测试单调递增趋势"""
        strategy = MetricStrategy(
            metric_type="memory",
            data_mode="trend",
            trend_mode="increase",
            count=5
        )
        result = strategy.generate(self.ctx)
        
        # 提取 used 值
        used_values = [p["used"] for p in result]
        
        # 验证单调递增
        for i in range(len(used_values) - 1):
            assert used_values[i] <= used_values[i + 1]
    
    def test_decrease_trend(self):
        """测试单调递减趋势"""
        strategy = MetricStrategy(
            metric_type="memory",
            data_mode="trend",
            trend_mode="decrease",
            count=5
        )
        result = strategy.generate(self.ctx)
        
        # 提取 used 值
        used_values = [p["used"] for p in result]
        
        # 验证单调递减
        for i in range(len(used_values) - 1):
            assert used_values[i] >= used_values[i + 1]
    
    def test_stable_trend(self):
        """测试持平趋势"""
        strategy = MetricStrategy(
            metric_type="memory",
            data_mode="trend",
            trend_mode="stable",
            count=5
        )
        result = strategy.generate(self.ctx)
        
        # 提取 used 值
        used_values = [p["used"] for p in result]
        
        # 验证所有值相同
        assert len(set(used_values)) == 1
    
    def test_increase_decrease_trend(self):
        """测试先增后减趋势"""
        strategy = MetricStrategy(
            metric_type="memory",
            data_mode="trend",
            trend_mode="increase_decrease",
            count=7
        )
        result = strategy.generate(self.ctx)
        
        # 提取 used 值
        used_values = [p["used"] for p in result]
        
        # 找到峰值位置（中间附近）
        mid_idx = len(used_values) // 2
        
        # 验证前半段递增
        for i in range(mid_idx):
            assert used_values[i] <= used_values[i + 1]
        
        # 验证后半段递减
        for i in range(mid_idx, len(used_values) - 1):
            assert used_values[i] >= used_values[i + 1]
    
    def test_decrease_increase_trend(self):
        """测试先减后增趋势"""
        strategy = MetricStrategy(
            metric_type="memory",
            data_mode="trend",
            trend_mode="decrease_increase",
            count=7
        )
        result = strategy.generate(self.ctx)
        
        # 提取 used 值
        used_values = [p["used"] for p in result]
        
        # 找到谷值位置（中间附近）
        mid_idx = len(used_values) // 2
        
        # 验证前半段递减
        for i in range(mid_idx):
            assert used_values[i] >= used_values[i + 1]
        
        # 验证后半段递增
        for i in range(mid_idx, len(used_values) - 1):
            assert used_values[i] <= used_values[i + 1]
    
    def test_trend_with_usage_field(self):
        """测试以 usage 字段为趋势"""
        strategy = MetricStrategy(
            metric_type="memory",
            data_mode="trend",
            trend_mode="increase",
            trend_field="usage",
            count=5
        )
        result = strategy.generate(self.ctx)
        
        # 提取 usage 值
        usage_values = [p["usage"] for p in result]
        
        # 验证单调递增
        for i in range(len(usage_values) - 1):
            assert usage_values[i] <= usage_values[i + 1]
    
    def test_trend_with_custom_range(self):
        """测试自定义趋势范围"""
        strategy = MetricStrategy(
            metric_type="memory",
            data_mode="trend",
            trend_mode="increase",
            trend_field="usage",
            trend_range=(20.0, 80.0),  # 使用率从 20% 增加到 80%
            count=5
        )
        result = strategy.generate(self.ctx)
        
        # 提取 usage 值
        usage_values = [p["usage"] for p in result]
        
        # 验证范围
        assert abs(usage_values[0] - 20.0) < 1.0
        assert abs(usage_values[-1] - 80.0) < 1.0
    
    def test_cpu_increase_trend(self):
        """测试 CPU 指标单调递增趋势"""
        strategy = MetricStrategy(
            metric_type="cpu",
            data_mode="trend",
            trend_mode="increase",
            count=5
        )
        result = strategy.generate(self.ctx)
        
        # 提取 used 值
        used_values = [p["used"] for p in result]
        
        # 验证单调递增
        for i in range(len(used_values) - 1):
            assert used_values[i] <= used_values[i + 1]
        
        # 验证所有数据点的 total 相同
        total_values = [p["total"] for p in result]
        assert len(set(total_values)) == 1
    
    def test_random_trend_unchanged(self):
        """测试 random 模式保持原有随机行为"""
        strategy = MetricStrategy(
            metric_type="memory",
            data_mode="trend",
            trend_mode="random",
            count=5
        )
        result = strategy.generate(self.ctx)
        
        # 随机模式下，各数据点独立生成
        # 验证基本结构
        assert len(result) == 5
        for point in result:
            assert "total" in point
            assert "used" in point
            assert "usage" in point
            assert "timestamp" in point


class TestMetricStrategyOutputFields:
    """测试 MetricStrategy 输出字段控制"""
    
    def setup_method(self):
        """设置测试上下文"""
        self.ctx = StrategyContext(
            field_path="test",
            field_schema={},
            root_data={},
            parent_data={}
        )
    
    def test_default_output_fields_capacity(self):
        """测试容量指标默认输出字段（包含 free）"""
        strategy = MetricStrategy(metric_type="memory", data_mode="current")
        result = strategy.generate(self.ctx)
        
        # 默认输出所有字段
        assert "total" in result
        assert "used" in result
        assert "free" in result
        assert "usage" in result
    
    def test_default_output_fields_rate(self):
        """测试速率指标默认输出字段"""
        strategy = MetricStrategy(metric_type="io", data_mode="current")
        result = strategy.generate(self.ctx)
        
        # 默认输出所有字段
        assert "rate_size" in result
        assert "rate_ops" in result
    
    def test_select_output_fields(self):
        """测试选择性输出字段"""
        strategy = MetricStrategy(
            metric_type="memory",
            data_mode="current",
            output_fields=["total", "used", "free"]
        )
        result = strategy.generate(self.ctx)
        
        # 只包含指定字段
        assert "total" in result
        assert "used" in result
        assert "free" in result
        assert "usage" not in result
    
    def test_output_fields_with_timestamp(self):
        """测试趋势数据包含时间戳"""
        strategy = MetricStrategy(
            metric_type="memory",
            data_mode="trend",
            output_fields=["total", "used", "timestamp"],
            count=3
        )
        result = strategy.generate(self.ctx)
        
        # 每个数据点只包含指定字段
        for point in result:
            assert "total" in point
            assert "used" in point
            assert "timestamp" in point
            assert "free" not in point
            assert "usage" not in point
    
    def test_output_fields_without_timestamp(self):
        """测试趋势数据不包含时间戳"""
        strategy = MetricStrategy(
            metric_type="memory",
            data_mode="trend",
            output_fields=["total", "used"],
            count=3
        )
        result = strategy.generate(self.ctx)
        
        # 每个数据点不包含时间戳
        for point in result:
            assert "total" in point
            assert "used" in point
            assert "timestamp" not in point
    
    def test_output_fields_single_field(self):
        """测试只输出单个字段"""
        strategy = MetricStrategy(
            metric_type="memory",
            data_mode="current",
            output_fields=["usage"]
        )
        result = strategy.generate(self.ctx)
        
        # 只包含 usage 字段
        assert "usage" in result
        assert "total" not in result
        assert "used" not in result
        assert "free" not in result
    
    def test_rate_metric_output_fields(self):
        """测试速率指标输出字段"""
        strategy = MetricStrategy(
            metric_type="io",
            data_mode="current",
            output_fields=["rate_size"]
        )
        result = strategy.generate(self.ctx)
        
        # 只包含 rate_size 字段
        assert "rate_size" in result
        assert "rate_ops" not in result
    
    def test_invalid_output_fields_type(self):
        """测试无效的 output_fields 类型"""
        with pytest.raises(StrategyError, match="output_fields 必须是列表类型"):
            MetricStrategy(output_fields="total")
    
    def test_empty_output_fields(self):
        """测试空列表 output_fields"""
        with pytest.raises(StrategyError, match="output_fields 不能为空列表"):
            MetricStrategy(output_fields=[])
    
    def test_invalid_field_name(self):
        """测试无效的字段名"""
        with pytest.raises(StrategyError, match="不支持的字段 'invalid_field'"):
            MetricStrategy(metric_type="memory", output_fields=["invalid_field"])
    
    def test_capacity_field_in_rate_metric(self):
        """测试速率指标中使用容量指标字段"""
        with pytest.raises(StrategyError, match="不支持的字段 'total'"):
            MetricStrategy(metric_type="io", output_fields=["total"])
    
    def test_free_field_calculation(self):
        """测试 free 字段计算正确性"""
        strategy = MetricStrategy(
            metric_type="memory",
            data_mode="current",
            unit="gb"
        )
        result = strategy.generate(self.ctx)
        
        # 验证 free = total - used
        assert abs(result["free"] - (result["total"] - result["used"])) < 0.01
    
    def test_free_field_in_trend(self):
        """测试趋势数据中 free 字段计算"""
        strategy = MetricStrategy(
            metric_type="memory",
            data_mode="trend",
            unit="gb",
            count=5
        )
        result = strategy.generate(self.ctx)
        
        # 验证每个数据点的 free 字段
        for point in result:
            expected_free = point["total"] - point["used"]
            assert abs(point["free"] - expected_free) < 0.01
    
    def test_cpu_free_field(self):
        """测试 CPU 指标的 free 字段"""
        strategy = MetricStrategy(
            metric_type="cpu",
            data_mode="current"
        )
        result = strategy.generate(self.ctx)
        
        # CPU 指标也应有 free 字段
        assert "free" in result
        assert abs(result["free"] - (result["total"] - result["used"])) < 0.01
    
    def test_output_fields_with_trend_mode(self):
        """测试趋势模式下输出字段过滤"""
        strategy = MetricStrategy(
            metric_type="memory",
            data_mode="trend",
            trend_mode="increase",
            output_fields=["total", "usage"],
            count=3
        )
        result = strategy.generate(self.ctx)
        
        # 每个数据点只包含指定字段
        for point in result:
            assert "total" in point
            assert "usage" in point
            assert "used" not in point
            assert "free" not in point
