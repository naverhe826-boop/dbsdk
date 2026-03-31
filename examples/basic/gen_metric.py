#!/usr/bin/env python3
"""
Metric 策略示例

展示如何使用 MetricStrategy 生成系统监控指标数据。

支持的指标类型：
- memory: 物理内存指标（total, used, usage）
- swap: 交换分区指标（total, used, usage）
- disk: 磁盘使用指标（total, used, usage）
- cpu: CPU指标（total核数, used使用核数, usage使用率）
- io: 磁盘IO速率指标（rate_size, rate_ops）

支持的数据模式：
- current: 单点数据
- trend: 时间序列数组

支持的趋势模式（trend_mode）：
- random: 随机波动（默认）
- increase: 单调递增
- decrease: 单调递减
- stable: 保持稳定
- increase_decrease: 先增后减
- decrease_increase: 先减后增

注意：CPU 指标的 total 和 used 为核数，不受 unit 参数影响
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from data_builder import DataBuilder, metric, BuilderConfig


def example_memory_current():
    """内存指标 - 当前值"""
    print("\n" + "=" * 70)
    print("内存指标 - 当前值示例")
    print("=" * 70)
    
    schema = {
        "type": "object",
        "properties": {
            "memory": {"type": "object"},
        },
        "required": ["memory"]
    }
    
    config = DataBuilder.config_from_dict({
        "policies": [
            {"path": "memory", "strategy": {"type": "metric", "metric_type": "memory", "data_mode": "current", "unit": "gb"}}
        ]
    })
    builder = DataBuilder(schema, config)
    
    data = builder.build(count=3)
    for i, item in enumerate(data, 1):
        mem = item['memory']
        print(f"{i}. total: {mem['total']} GB, used: {mem['used']} GB, usage: {mem['usage']}%")


def example_memory_trend():
    """内存指标 - 趋势数据"""
    print("\n" + "=" * 70)
    print("内存指标 - 趋势数据示例（5个数据点，间隔60秒）")
    print("=" * 70)
    
    schema = {
        "type": "object",
        "properties": {
            "memory_trend": {"type": "array"},
        },
        "required": ["memory_trend"]
    }
    
    config = DataBuilder.config_from_dict({
        "policies": [
            {"path": "memory_trend", "strategy": {
                "type": "metric",
                "metric_type": "memory",
                "data_mode": "trend",
                "unit": "mb",
                "count": 5,
                "time_interval": 60
            }}
        ]
    })
    builder = DataBuilder(schema, config)
    
    data = builder.build(count=1)
    trend = data[0]['memory_trend']
    
    print(f"共 {len(trend)} 个数据点：")
    for i, point in enumerate(trend, 1):
        print(f"{i}. [{point['timestamp']}] total: {point['total']} MB, "
              f"used: {point['used']} MB, usage: {point['usage']}%")


def example_swap_current():
    """Swap 指标 - 当前值"""
    print("\n" + "=" * 70)
    print("Swap 指标 - 当前值示例")
    print("=" * 70)
    
    schema = {
        "type": "object",
        "properties": {
            "swap": {"type": "object"},
        },
        "required": ["swap"]
    }
    
    config = DataBuilder.config_from_dict({
        "policies": [
            {"path": "swap", "strategy": {"type": "metric", "metric_type": "swap", "data_mode": "current", "unit": "mb"}}
        ]
    })
    builder = DataBuilder(schema, config)
    
    data = builder.build(count=3)
    for i, item in enumerate(data, 1):
        swap = item['swap']
        print(f"{i}. total: {swap['total']} MB, used: {swap['used']} MB, usage: {swap['usage']}%")


def example_disk_current():
    """磁盘指标 - 当前值（自定义容量范围）"""
    print("\n" + "=" * 70)
    print("磁盘指标 - 当前值示例（自定义容量范围 100-500 GB）")
    print("=" * 70)
    
    schema = {
        "type": "object",
        "properties": {
            "disk": {"type": "object"},
        },
        "required": ["disk"]
    }
    
    # 自定义磁盘容量范围：100GB - 500GB
    config = DataBuilder.config_from_dict({
        "policies": [
            {
                "path": "disk",
                "strategy": {
                    "type": "metric",
                    "metric_type": "disk",
                    "data_mode": "current",
                    "unit": "gb",
                    "total_range": [100 * 1024 * 1024 * 1024, 500 * 1024 * 1024 * 1024]  # 字节
                }
            }
        ]
    })
    builder = DataBuilder(schema, config)
    
    data = builder.build(count=3)
    for i, item in enumerate(data, 1):
        disk = item['disk']
        print(f"{i}. total: {disk['total']} GB, used: {disk['used']} GB, usage: {disk['usage']}%")


def example_disk_trend():
    """磁盘指标 - 趋势数据"""
    print("\n" + "=" * 70)
    print("磁盘指标 - 趋势数据示例（10个数据点，间隔300秒）")
    print("=" * 70)
    
    schema = {
        "type": "object",
        "properties": {
            "disk_trend": {"type": "array"},
        },
        "required": ["disk_trend"]
    }
    
    config = DataBuilder.config_from_dict({
        "policies": [
            {
                "path": "disk_trend",
                "strategy": {
                    "type": "metric",
                    "metric_type": "disk",
                    "data_mode": "trend",
                    "unit": "gb",
                    "count": 10,
                    "time_interval": 300  # 5分钟
                }
            }
        ]
    })
    builder = DataBuilder(schema, config)
    
    data = builder.build(count=1)
    trend = data[0]['disk_trend']
    
    print(f"共 {len(trend)} 个数据点（仅显示前3个）:")
    for i, point in enumerate(trend[:3], 1):
        print(f"{i}. [{point['timestamp']}] total: {point['total']} GB, "
              f"used: {point['used']} GB, usage: {point['usage']}%")


def example_cpu_current():
    """CPU 指标 - 当前值"""
    print("\n" + "=" * 70)
    print("CPU 指标 - 当前值示例（核数不受 unit 参数影响）")
    print("=" * 70)
    
    schema = {
        "type": "object",
        "properties": {
            "cpu": {"type": "object"},
        },
        "required": ["cpu"]
    }
    
    config = DataBuilder.config_from_dict({
        "policies": [
            {"path": "cpu", "strategy": {"type": "metric", "metric_type": "cpu", "data_mode": "current"}}
        ]
    })
    builder = DataBuilder(schema, config)
    
    data = builder.build(count=5)
    for i, item in enumerate(data, 1):
        cpu = item['cpu']
        print(f"{i}. total: {cpu['total']} 核, used: {cpu['used']} 核, usage: {cpu['usage']}%")


def example_cpu_trend():
    """CPU 指标 - 趋势数据"""
    print("\n" + "=" * 70)
    print("CPU 指标 - 趋势数据示例（自定义核数范围 4-16 核）")
    print("=" * 70)
    
    schema = {
        "type": "object",
        "properties": {
            "cpu_trend": {"type": "array"},
        },
        "required": ["cpu_trend"]
    }
    
    config = DataBuilder.config_from_dict({
        "policies": [
            {
                "path": "cpu_trend",
                "strategy": {
                    "type": "metric",
                    "metric_type": "cpu",
                    "data_mode": "trend",
                    "count": 5,
                    "time_interval": 60,
                    "total_range": [4, 16]  # 核数范围
                }
            }
        ]
    })
    builder = DataBuilder(schema, config)
    
    data = builder.build(count=1)
    trend = data[0]['cpu_trend']
    
    print(f"共 {len(trend)} 个数据点:")
    for i, point in enumerate(trend, 1):
        print(f"{i}. [{point['timestamp']}] total: {point['total']} 核, "
              f"used: {point['used']} 核, usage: {point['usage']}%")


def example_io_current():
    """IO 指标 - 当前值"""
    print("\n" + "=" * 70)
    print("IO 指标 - 当前值示例（速率指标）")
    print("=" * 70)
    
    schema = {
        "type": "object",
        "properties": {
            "io": {"type": "object"},
        },
        "required": ["io"]
    }
    
    config = DataBuilder.config_from_dict({
        "policies": [
            {"path": "io", "strategy": {"type": "metric", "metric_type": "io", "data_mode": "current", "unit": "mb"}}
        ]
    })
    builder = DataBuilder(schema, config)
    
    data = builder.build(count=5)
    for i, item in enumerate(data, 1):
        io = item['io']
        print(f"{i}. rate_size: {io['rate_size']} MB/s, rate_ops: {io['rate_ops']} IOPS")


def example_io_trend():
    """IO 指标 - 趋势数据"""
    print("\n" + "=" * 70)
    print("IO 指标 - 趋势数据示例（自定义速率范围）")
    print("=" * 70)
    
    schema = {
        "type": "object",
        "properties": {
            "io_trend": {"type": "array"},
        },
        "required": ["io_trend"]
    }
    
    # 自定义速率范围
    config = DataBuilder.config_from_dict({
        "policies": [
            {
                "path": "io_trend",
                "strategy": {
                    "type": "metric",
                    "metric_type": "io",
                    "data_mode": "trend",
                    "unit": "mb",
                    "count": 5,
                    "time_interval": 30,
                    "rate_range": {
                        "rate_size": [0, 100 * 1024 * 1024],  # 0 - 100 MB/s（字节）
                        "rate_ops": [0, 5000]  # 0 - 5000 IOPS
                    }
                }
            }
        ]
    })
    builder = DataBuilder(schema, config)
    
    data = builder.build(count=1)
    trend = data[0]['io_trend']
    
    print(f"共 {len(trend)} 个数据点:")
    for i, point in enumerate(trend, 1):
        print(f"{i}. [{point['timestamp']}] rate_size: {point['rate_size']} MB/s, "
              f"rate_ops: {point['rate_ops']} IOPS")


def example_all_metrics():
    """所有指标 - 单点数据"""
    print("\n" + "=" * 70)
    print("所有指标 - 单点数据示例")
    print("=" * 70)
    
    schema = {
        "type": "object",
        "properties": {
            "memory": {"type": "object"},
            "swap": {"type": "object"},
            "disk": {"type": "object"},
            "cpu": {"type": "object"},
            "io": {"type": "object"},
        },
        "required": ["memory", "swap", "disk", "cpu", "io"]
    }
    
    config = DataBuilder.config_from_dict({
        "policies": [
            {"path": "memory", "strategy": {"type": "metric", "metric_type": "memory", "unit": "gb"}},
            {"path": "swap", "strategy": {"type": "metric", "metric_type": "swap", "unit": "gb"}},
            {"path": "disk", "strategy": {"type": "metric", "metric_type": "disk", "unit": "gb"}},
            {"path": "cpu", "strategy": {"type": "metric", "metric_type": "cpu"}},
            {"path": "io", "strategy": {"type": "metric", "metric_type": "io", "unit": "mb"}},
        ]
    })
    builder = DataBuilder(schema, config)
    
    data = builder.build(count=1)
    item = data[0]
    
    mem = item['memory']
    swap = item['swap']
    disk = item['disk']
    cpu = item['cpu']
    io = item['io']
    
    print(f"Memory: total={mem['total']} GB, used={mem['used']} GB, usage={mem['usage']}%")
    print(f"Swap:   total={swap['total']} GB, used={swap['used']} GB, usage={swap['usage']}%")
    print(f"Disk:   total={disk['total']} GB, used={disk['used']} GB, usage={disk['usage']}%")
    print(f"CPU:    total={cpu['total']} 核, used={cpu['used']} 核, usage={cpu['usage']}%")
    print(f"IO:     rate_size={io['rate_size']} MB/s, rate_ops={io['rate_ops']} IOPS")


def example_byte_unit():
    """字节单位示例"""
    print("\n" + "=" * 70)
    print("字节单位示例（unit=byte）")
    print("=" * 70)
    
    schema = {
        "type": "object",
        "properties": {
            "memory_bytes": {"type": "object"},
        },
        "required": ["memory_bytes"]
    }
    
    config = DataBuilder.config_from_dict({
        "policies": [
            {"path": "memory_bytes", "strategy": {"type": "metric", "metric_type": "memory", "unit": "byte"}}
        ]
    })
    builder = DataBuilder(schema, config)
    
    data = builder.build(count=2)
    for i, item in enumerate(data, 1):
        mem = item['memory_bytes']
        print(f"{i}. total: {mem['total']} bytes, used: {mem['used']} bytes, usage: {mem['usage']}%")


def example_boundary_values():
    """边界值示例"""
    print("\n" + "=" * 70)
    print("边界值示例（使用 boundary_values 方法）")
    print("=" * 70)
    
    from data_builder.strategies.value.system import MetricStrategy
    
    strategy = MetricStrategy(metric_type="memory", unit="gb")
    boundary = strategy.boundary_values()
    
    print(f"内存指标边界值（共 {len(boundary)} 个）:")
    for i, val in enumerate(boundary, 1):
        print(f"{i}. total={val['total']} GB, used={val['used']} GB, usage={val['usage']}%")


def example_invalid_values():
    """非法值示例"""
    print("\n" + "=" * 70)
    print("非法值示例（用于测试验证逻辑）")
    print("=" * 70)
    
    from data_builder.strategies.value.system import MetricStrategy
    
    # 容量指标非法值
    strategy1 = MetricStrategy(metric_type="memory")
    invalid1 = strategy1.invalid_values()
    
    print(f"容量指标非法值（共 {len(invalid1)} 个）:")
    for i, val in enumerate(invalid1[:3], 1):
        print(f"{i}. {val}")
    
    # 速率指标非法值
    strategy2 = MetricStrategy(metric_type="io")
    invalid2 = strategy2.invalid_values()
    
    print(f"\n速率指标非法值（共 {len(invalid2)} 个）:")
    for i, val in enumerate(invalid2[:3], 1):
        print(f"{i}. {val}")


def example_trend_increase():
    """趋势模式 - 单调递增"""
    print("\n" + "=" * 70)
    print("趋势模式示例 - 单调递增（used 从 0 逐步增加）")
    print("=" * 70)
    
    schema = {
        "type": "object",
        "properties": {
            "memory_trend": {"type": "array"},
        },
        "required": ["memory_trend"]
    }
    
    config = DataBuilder.config_from_dict({
        "policies": [
            {
                "path": "memory_trend",
                "strategy": {
                    "type": "metric",
                    "metric_type": "memory",
                    "data_mode": "trend",
                    "unit": "gb",
                    "count": 5,
                    "trend_mode": "increase",  # 单调递增
                    "trend_field": "used"  # used 字段递增
                }
            }
        ]
    })
    builder = DataBuilder(schema, config)
    
    data = builder.build(count=1)
    trend = data[0]['memory_trend']
    
    print(f"共 {len(trend)} 个数据点:")
    for i, point in enumerate(trend, 1):
        print(f"{i}. [{point['timestamp']}] total: {point['total']} GB, "
              f"used: {point['used']:.2f} GB, usage: {point['usage']:.2f}%")


def example_trend_decrease():
    """趋势模式 - 单调递减"""
    print("\n" + "=" * 70)
    print("趋势模式示例 - 单调递减（used 从最大值逐步减少）")
    print("=" * 70)
    
    schema = {
        "type": "object",
        "properties": {
            "memory_trend": {"type": "array"},
        },
        "required": ["memory_trend"]
    }
    
    config = DataBuilder.config_from_dict({
        "policies": [
            {
                "path": "memory_trend",
                "strategy": {
                    "type": "metric",
                    "metric_type": "memory",
                    "data_mode": "trend",
                    "unit": "gb",
                    "count": 5,
                    "trend_mode": "decrease",  # 单调递减
                    "trend_field": "used"
                }
            }
        ]
    })
    builder = DataBuilder(schema, config)
    
    data = builder.build(count=1)
    trend = data[0]['memory_trend']
    
    print(f"共 {len(trend)} 个数据点:")
    for i, point in enumerate(trend, 1):
        print(f"{i}. [{point['timestamp']}] total: {point['total']} GB, "
              f"used: {point['used']:.2f} GB, usage: {point['usage']:.2f}%")


def example_trend_stable():
    """趋势模式 - 保持稳定"""
    print("\n" + "=" * 70)
    print("趋势模式示例 - 保持稳定（所有数据点的 used 值相同）")
    print("=" * 70)
    
    schema = {
        "type": "object",
        "properties": {
            "cpu_trend": {"type": "array"},
        },
        "required": ["cpu_trend"]
    }
    
    config = DataBuilder.config_from_dict({
        "policies": [
            {
                "path": "cpu_trend",
                "strategy": {
                    "type": "metric",
                    "metric_type": "cpu",
                    "data_mode": "trend",
                    "count": 5,
                    "trend_mode": "stable",  # 保持稳定
                    "trend_field": "usage"
                }
            }
        ]
    })
    builder = DataBuilder(schema, config)
    
    data = builder.build(count=1)
    trend = data[0]['cpu_trend']
    
    print(f"共 {len(trend)} 个数据点:")
    for i, point in enumerate(trend, 1):
        print(f"{i}. [{point['timestamp']}] total: {point['total']} 核, "
              f"used: {point['used']:.2f} 核, usage: {point['usage']:.2f}%")


def example_trend_increase_decrease():
    """趋势模式 - 先增后减"""
    print("\n" + "=" * 70)
    print("趋势模式示例 - 先增后减（中间点为峰值）")
    print("=" * 70)
    
    schema = {
        "type": "object",
        "properties": {
            "memory_trend": {"type": "array"},
        },
        "required": ["memory_trend"]
    }
    
    config = DataBuilder.config_from_dict({
        "policies": [
            {
                "path": "memory_trend",
                "strategy": {
                    "type": "metric",
                    "metric_type": "memory",
                    "data_mode": "trend",
                    "unit": "gb",
                    "count": 7,
                    "trend_mode": "increase_decrease",  # 先增后减
                    "trend_field": "usage"
                }
            }
        ]
    })
    builder = DataBuilder(schema, config)
    
    data = builder.build(count=1)
    trend = data[0]['memory_trend']
    
    print(f"共 {len(trend)} 个数据点:")
    for i, point in enumerate(trend, 1):
        print(f"{i}. [{point['timestamp']}] total: {point['total']} GB, "
              f"used: {point['used']:.2f} GB, usage: {point['usage']:.2f}%")


def example_trend_decrease_increase():
    """趋势模式 - 先减后增"""
    print("\n" + "=" * 70)
    print("趋势模式示例 - 先减后增（中间点为谷值）")
    print("=" * 70)
    
    schema = {
        "type": "object",
        "properties": {
            "cpu_trend": {"type": "array"},
        },
        "required": ["cpu_trend"]
    }
    
    config = DataBuilder.config_from_dict({
        "policies": [
            {
                "path": "cpu_trend",
                "strategy": {
                    "type": "metric",
                    "metric_type": "cpu",
                    "data_mode": "trend",
                    "count": 7,
                    "trend_mode": "decrease_increase",  # 先减后增
                    "trend_field": "usage"
                }
            }
        ]
    })
    builder = DataBuilder(schema, config)
    
    data = builder.build(count=1)
    trend = data[0]['cpu_trend']
    
    print(f"共 {len(trend)} 个数据点:")
    for i, point in enumerate(trend, 1):
        print(f"{i}. [{point['timestamp']}] total: {point['total']} 核, "
              f"used: {point['used']:.2f} 核, usage: {point['usage']:.2f}%")


def example_trend_with_custom_range():
    """趋势模式 - 自定义趋势范围"""
    print("\n" + "=" * 70)
    print("趋势模式示例 - 自定义趋势范围（usage 从 20% 增加到 80%）")
    print("=" * 70)
    
    schema = {
        "type": "object",
        "properties": {
            "memory_trend": {"type": "array"},
        },
        "required": ["memory_trend"]
    }
    
    config = DataBuilder.config_from_dict({
        "policies": [
            {
                "path": "memory_trend",
                "strategy": {
                    "type": "metric",
                    "metric_type": "memory",
                    "data_mode": "trend",
                    "unit": "gb",
                    "count": 5,
                    "trend_mode": "increase",
                    "trend_field": "usage",
                    "trend_range": [20.0, 80.0]  # 使用率从 20% 增加到 80%
                }
            }
        ]
    })
    builder = DataBuilder(schema, config)
    
    data = builder.build(count=1)
    trend = data[0]['memory_trend']
    
    print(f"共 {len(trend)} 个数据点:")
    for i, point in enumerate(trend, 1):
        print(f"{i}. [{point['timestamp']}] total: {point['total']} GB, "
              f"used: {point['used']:.2f} GB, usage: {point['usage']:.2f}%")


def example_output_fields_basic():
    """输出字段控制 - 基本示例"""
    print("\n" + "=" * 70)
    print("输出字段控制示例 - 只要 total, used, free")
    print("=" * 70)
    
    schema = {
        "type": "object",
        "properties": {
            "memory": {"type": "object"},
        },
        "required": ["memory"]
    }
    
    config = DataBuilder.config_from_dict({
        "policies": [
            {
                "path": "memory",
                "strategy": {
                    "type": "metric",
                    "metric_type": "memory",
                    "data_mode": "current",
                    "unit": "gb",
                    "output_fields": ["total", "used", "free"]  # 不需要 usage
                }
            }
        ]
    })
    builder = DataBuilder(schema, config)
    
    data = builder.build(count=3)
    for i, item in enumerate(data, 1):
        mem = item['memory']
        print(f"{i}. total: {mem['total']} GB, used: {mem['used']} GB, free: {mem['free']} GB")


def example_output_fields_single():
    """输出字段控制 - 只输出单个字段"""
    print("\n" + "=" * 70)
    print("输出字段控制示例 - 只要 usage 字段")
    print("=" * 70)
    
    schema = {
        "type": "object",
        "properties": {
            "cpu": {"type": "object"},
        },
        "required": ["cpu"]
    }
    
    config = DataBuilder.config_from_dict({
        "policies": [
            {
                "path": "cpu",
                "strategy": {
                    "type": "metric",
                    "metric_type": "cpu",
                    "data_mode": "current",
                    "output_fields": ["usage"]  # 只要使用率
                }
            }
        ]
    })
    builder = DataBuilder(schema, config)
    
    data = builder.build(count=5)
    for i, item in enumerate(data, 1):
        cpu = item['cpu']
        print(f"{i}. CPU usage: {cpu['usage']}%")


def example_output_fields_trend():
    """输出字段控制 - 趋势数据不包含时间戳"""
    print("\n" + "=" * 70)
    print("输出字段控制示例 - 趋势数据不包含时间戳")
    print("=" * 70)
    
    schema = {
        "type": "object",
        "properties": {
            "disk_trend": {"type": "array"},
        },
        "required": ["disk_trend"]
    }
    
    config = DataBuilder.config_from_dict({
        "policies": [
            {
                "path": "disk_trend",
                "strategy": {
                    "type": "metric",
                    "metric_type": "disk",
                    "data_mode": "trend",
                    "unit": "gb",
                    "count": 5,
                    "trend_mode": "increase",
                    "output_fields": ["total", "used", "usage"]  # 不要时间戳
                }
            }
        ]
    })
    builder = DataBuilder(schema, config)
    
    data = builder.build(count=1)
    trend = data[0]['disk_trend']
    
    print(f"共 {len(trend)} 个数据点（无时间戳）:")
    for i, point in enumerate(trend, 1):
        print(f"{i}. total: {point['total']} GB, used: {point['used']:.2f} GB, "
              f"usage: {point['usage']:.2f}%")


def example_output_fields_rate():
    """输出字段控制 - 速率指标"""
    print("\n" + "=" * 70)
    print("输出字段控制示例 - 只要 rate_size")
    print("=" * 70)
    
    schema = {
        "type": "object",
        "properties": {
            "io_rate": {"type": "object"},
        },
        "required": ["io_rate"]
    }
    
    config = DataBuilder.config_from_dict({
        "policies": [
            {
                "path": "io_rate",
                "strategy": {
                    "type": "metric",
                    "metric_type": "io",
                    "data_mode": "current",
                    "unit": "mb",
                    "output_fields": ["rate_size"]  # 只要字节速率
                }
            }
        ]
    })
    builder = DataBuilder(schema, config)
    
    data = builder.build(count=3)
    for i, item in enumerate(data, 1):
        io = item['io_rate']
        print(f"{i}. IO rate: {io['rate_size']} MB/s")


def example_free_field():
    """free 字段示例"""
    print("\n" + "=" * 70)
    print("free 字段示例 - 显示内存空闲容量")
    print("=" * 70)
    
    schema = {
        "type": "object",
        "properties": {
            "memory": {"type": "object"},
        },
        "required": ["memory"]
    }
    
    config = DataBuilder.config_from_dict({
        "policies": [
            {
                "path": "memory",
                "strategy": {
                    "type": "metric",
                    "metric_type": "memory",
                    "data_mode": "current",
                    "unit": "gb"
                }
            }
        ]
    })
    builder = DataBuilder(schema, config)
    
    data = builder.build(count=3)
    for i, item in enumerate(data, 1):
        mem = item['memory']
        print(f"{i}. total: {mem['total']} GB, used: {mem['used']} GB, "
              f"free: {mem['free']} GB, usage: {mem['usage']}%")


if __name__ == "__main__":
    """运行所有示例"""
    example_memory_current()
    example_memory_trend()
    example_swap_current()
    example_disk_current()
    example_disk_trend()
    example_cpu_current()
    example_cpu_trend()
    example_io_current()
    example_io_trend()
    example_all_metrics()
    example_byte_unit()
    example_boundary_values()
    example_invalid_values()
    # 趋势模式示例
    example_trend_increase()
    example_trend_decrease()
    example_trend_stable()
    example_trend_increase_decrease()
    example_trend_decrease_increase()
    example_trend_with_custom_range()
    # 输出字段控制示例
    example_output_fields_basic()
    example_output_fields_single()
    example_output_fields_trend()
    example_output_fields_rate()
    example_free_field()
