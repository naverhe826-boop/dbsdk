import random
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union

from ...basic import Strategy, StrategyContext
from ....exceptions import StrategyError


# 单位常量（字节）
BYTE = 1
KB = 1024
MB = 1024 * KB
GB = 1024 * MB


# 默认指标范围
DEFAULT_RANGES = {
    "memory": (1 * GB, 128 * GB),      # 1GB - 128GB
    "swap": (512 * MB, 32 * GB),       # 512MB - 32GB
    "disk": (10 * GB, 2000 * GB),      # 10GB - 2TB
    "cpu": (1, 128),                    # 1 - 128 核
    "io": {
        "rate_size": (0, 500 * MB),    # 0 - 500MB/s
        "rate_ops": (0, 10000),        # 0 - 10000 IOPS
    }
}

# 单位映射
UNIT_MULTIPLIERS = {
    "byte": BYTE,
    "kb": KB,
    "mb": MB,
    "gb": GB,
}

# 可用字段常量
CAPACITY_FIELDS = {"total", "used", "free", "usage", "timestamp"}
RATE_FIELDS = {"rate_size", "rate_ops", "timestamp"}


class MetricStrategy(Strategy):
    """系统监控指标策略
    
    支持两类指标：
    1. 容量指标（memory/swap/disk/cpu）：输出 total, used, usage
    2. 速率指标（io）：输出 rate_size, rate_ops
    
    支持两种数据模式：
    - current: 单点数据
    - trend: 时间序列数组
    
    趋势模式（trend_mode）：
    - random: 随机波动（默认）
    - increase: 单调递增
    - decrease: 单调递减
    - stable: 保持稳定
    - increase_decrease: 先增后减
    - decrease_increase: 先减后增
    
    注意：CPU 指标的 total 和 used 为核数，不受 unit 参数影响
    """
    
    def __init__(
        self,
        metric_type: str = "memory",
        data_mode: str = "current",
        unit: str = "mb",
        count: int = 10,
        time_interval: int = 60,
        total_range: Optional[Tuple[Union[int, float], Union[int, float]]] = None,
        rate_range: Optional[Dict[str, Tuple[Union[int, float], Union[int, float]]]] = None,
        time_format: str = "%Y-%m-%d %H:%M:%S",
        trend_mode: str = "random",
        trend_field: str = "used",
        trend_range: Optional[Tuple[Union[int, float], Union[int, float]]] = None,
        output_fields: Optional[List[str]] = None,
    ):
        # 参数验证
        if metric_type not in ["memory", "swap", "disk", "cpu", "io"]:
            raise StrategyError(
                f"MetricStrategy: 不支持的指标类型 '{metric_type}'，"
                f"支持的类型: memory, swap, disk, cpu, io"
            )
        
        if data_mode not in ["current", "trend"]:
            raise StrategyError(
                f"MetricStrategy: 不支持的数据模式 '{data_mode}'，"
                f"支持的模式: current, trend"
            )
        
        if unit not in UNIT_MULTIPLIERS:
            raise StrategyError(
                f"MetricStrategy: 不支持的单位 '{unit}'，"
                f"支持的单位: byte, kb, mb, gb"
            )
        
        if count < 1:
            raise StrategyError(
                f"MetricStrategy: count 必须 >= 1，实际为 {count}"
            )
        
        # 趋势模式验证
        valid_trend_modes = ["random", "increase", "decrease", "stable", "increase_decrease", "decrease_increase"]
        if trend_mode not in valid_trend_modes:
            raise StrategyError(
                f"MetricStrategy: 不支持的趋势模式 '{trend_mode}'，"
                f"支持的模式: {', '.join(valid_trend_modes)}"
            )
        
        # 趋势字段验证（仅容量指标有效）
        if metric_type in ["memory", "swap", "disk", "cpu"]:
            if trend_field not in ["used", "usage"]:
                raise StrategyError(
                    f"MetricStrategy: 容量指标不支持趋势字段 '{trend_field}'，"
                    f"支持的字段: used, usage"
                )
        
        # 趋势范围验证
        if trend_range is not None:
            if not isinstance(trend_range, (tuple, list)) or len(trend_range) != 2:
                raise StrategyError(
                    f"MetricStrategy: trend_range 必须是包含 2 个元素的元组或列表"
                )
        
        # output_fields 验证
        if output_fields is not None:
            if not isinstance(output_fields, list):
                raise StrategyError(
                    f"MetricStrategy: output_fields 必须是列表类型"
                )
            if len(output_fields) == 0:
                raise StrategyError(
                    f"MetricStrategy: output_fields 不能为空列表"
                )
            # 根据指标类型检查字段有效性
            valid_fields = CAPACITY_FIELDS if metric_type in ["memory", "swap", "disk", "cpu"] else RATE_FIELDS
            for field in output_fields:
                if field not in valid_fields:
                    raise StrategyError(
                        f"MetricStrategy: 不支持的字段 '{field}'，"
                        f"可用字段: {', '.join(sorted(valid_fields))}"
                    )
        
        self.metric_type = metric_type
        self.data_mode = data_mode
        self.unit = unit
        self.count = count
        self.time_interval = time_interval
        self.total_range = total_range
        self.rate_range = rate_range
        self.time_format = time_format
        self.trend_mode = trend_mode
        self.trend_field = trend_field
        self.trend_range = trend_range
        self.output_fields = output_fields
        
        # 获取单位乘数
        self.unit_multiplier = UNIT_MULTIPLIERS[unit]
        
        # 设置指标范围
        self._setup_ranges()
    
    def _setup_ranges(self):
        """设置指标范围"""
        if self.metric_type in ["memory", "swap", "disk", "cpu"]:
            # 容量指标
            if self.total_range:
                self._total_min, self._total_max = self.total_range
            else:
                self._total_min, self._total_max = DEFAULT_RANGES[self.metric_type]
        else:
            # 速率指标
            if self.rate_range:
                self._rate_size_range = self.rate_range.get(
                    "rate_size", 
                    DEFAULT_RANGES["io"]["rate_size"]
                )
                self._rate_ops_range = self.rate_range.get(
                    "rate_ops", 
                    DEFAULT_RANGES["io"]["rate_ops"]
                )
            else:
                self._rate_size_range = DEFAULT_RANGES["io"]["rate_size"]
                self._rate_ops_range = DEFAULT_RANGES["io"]["rate_ops"]
    
    def _filter_output_fields(self, data: Dict) -> Dict:
        """根据 output_fields 过滤输出字段
        
        Args:
            data: 原始数据字典
            
        Returns:
            过滤后的数据字典
        """
        if self.output_fields is None:
            return data
        
        return {k: v for k, v in data.items() if k in self.output_fields}
    
    def _generate_capacity_metric(self) -> Dict[str, Union[int, float]]:
        """生成容量指标数据（memory/swap/disk/cpu）"""
        # 随机生成 total（总大小）
        total = random.uniform(self._total_min, self._total_max)
        
        # 随机生成 used（使用大小），范围 [0, total]
        used = random.uniform(0, total)
        
        # CPU 指标不需要单位转换（total 和 used 都是核数）
        if self.metric_type == "cpu":
            # CPU 核数通常为整数，但 used（使用核数）可以是浮点数
            total_display = int(round(total))
            used_display = round(used, 2)
        else:
            # 转换为目标单位
            total_display = total / self.unit_multiplier
            used_display = used / self.unit_multiplier
            
            # 根据单位决定是否使用浮点数
            if self.unit == "byte":
                total_display = int(total_display)
                used_display = int(used_display)
            else:
                total_display = round(total_display, 2)
                used_display = round(used_display, 2)
        
        # 计算 free 和 usage（确保一致性）
        free_display = total_display - used_display
        usage = (used_display / total_display * 100) if total_display > 0 else 0.0
        
        # 根据单位格式化 free 值
        if self.metric_type == "cpu" or self.unit != "byte":
            free_display = round(free_display, 2)
        else:
            free_display = int(free_display)
        
        return {
            "total": total_display,
            "used": used_display,
            "free": free_display,
            "usage": round(usage, 2)
        }
    
    def _generate_rate_metric(self) -> Dict[str, Union[int, float]]:
        """生成速率指标数据（io）"""
        # 随机生成 rate_size（字节/秒）
        rate_size = random.uniform(*self._rate_size_range)
        
        # 随机生成 rate_ops（次数/秒）
        rate_ops = random.uniform(*self._rate_ops_range)
        
        # 转换为目标单位
        rate_size_display = rate_size / self.unit_multiplier
        
        # 根据单位决定是否使用浮点数
        if self.unit == "byte":
            rate_size_display = int(rate_size_display)
            rate_ops_display = int(rate_ops)
        else:
            rate_size_display = round(rate_size_display, 2)
            rate_ops_display = round(rate_ops, 2)
        
        return {
            "rate_size": rate_size_display,
            "rate_ops": rate_ops_display
        }
    
    def _generate_timestamps(self, count: int) -> List[str]:
        """生成时间戳序列
        
        Args:
            count: 数据点数量
            
        Returns:
            时间戳字符串列表，按时间倒序（最新在前）
        """
        timestamps = []
        now = datetime.now()
        
        for i in range(count):
            # 从当前时间向前推算
            dt = now - timedelta(seconds=self.time_interval * i)
            timestamps.append(dt.strftime(self.time_format))
        
        # 反转使时间正序（从旧到新）
        return list(reversed(timestamps))
    
    def _generate_trend_values(self, count: int, min_val: float, max_val: float) -> List[float]:
        """按趋势模式生成值序列
        
        Args:
            count: 数据点数量
            min_val: 最小值
            max_val: 最大值
            
        Returns:
            值序列列表
        """
        if self.trend_mode == "random":
            # 随机生成
            return [random.uniform(min_val, max_val) for _ in range(count)]
        
        elif self.trend_mode == "stable":
            # 保持稳定（中间值）
            stable_val = (min_val + max_val) / 2
            return [stable_val] * count
        
        elif self.trend_mode == "increase":
            # 单调递增
            if count == 1:
                return [min_val]
            step = (max_val - min_val) / (count - 1)
            return [min_val + i * step for i in range(count)]
        
        elif self.trend_mode == "decrease":
            # 单调递减
            if count == 1:
                return [max_val]
            step = (max_val - min_val) / (count - 1)
            return [max_val - i * step for i in range(count)]
        
        elif self.trend_mode == "increase_decrease":
            # 先增后减
            if count == 1:
                return [min_val]
            mid_idx = count // 2
            # 前半段递增
            inc_step = (max_val - min_val) / max(mid_idx, 1) if mid_idx > 0 else 0
            inc_values = [min_val + i * inc_step for i in range(mid_idx + 1)]
            # 后半段递减
            dec_count = count - mid_idx - 1
            dec_step = (max_val - min_val) / max(dec_count, 1) if dec_count > 0 else 0
            dec_values = [max_val - i * dec_step for i in range(1, dec_count + 1)]
            return inc_values + dec_values
        
        elif self.trend_mode == "decrease_increase":
            # 先减后增
            if count == 1:
                return [max_val]
            mid_idx = count // 2
            # 前半段递减
            dec_step = (max_val - min_val) / max(mid_idx, 1) if mid_idx > 0 else 0
            dec_values = [max_val - i * dec_step for i in range(mid_idx + 1)]
            # 后半段递增
            inc_count = count - mid_idx - 1
            inc_step = (max_val - min_val) / max(inc_count, 1) if inc_count > 0 else 0
            inc_values = [min_val + i * inc_step for i in range(1, inc_count + 1)]
            return dec_values + inc_values
        
        else:
            # 默认随机
            return [random.uniform(min_val, max_val) for _ in range(count)]
    
    def generate(self, ctx: StrategyContext) -> Union[Dict, List[Dict]]:
        """生成监控指标数据"""
        if self.data_mode == "current":
            # 单点数据
            if self.metric_type in ["memory", "swap", "disk", "cpu"]:
                data = self._generate_capacity_metric()
            else:
                data = self._generate_rate_metric()
            return self._filter_output_fields(data)
        else:
            # 趋势数据
            timestamps = self._generate_timestamps(self.count)
            
            # 如果趋势模式为 random，保持原有逻辑
            if self.trend_mode == "random":
                if self.metric_type in ["memory", "swap", "disk", "cpu"]:
                    # 容量指标趋势
                    data_list = [
                        {**self._generate_capacity_metric(), "timestamp": ts}
                        for ts in timestamps
                    ]
                else:
                    # 速率指标趋势
                    data_list = [
                        {**self._generate_rate_metric(), "timestamp": ts}
                        for ts in timestamps
                    ]
                return [self._filter_output_fields(item) for item in data_list]
            
            # 非随机模式：按趋势生成序列
            if self.metric_type in ["memory", "swap", "disk", "cpu"]:
                # 容量指标趋势
                data_list = self._generate_capacity_trend(timestamps)
            else:
                # 速率指标趋势
                data_list = self._generate_rate_trend(timestamps)
            return [self._filter_output_fields(item) for item in data_list]
    
    def _generate_capacity_trend(self, timestamps: List[str]) -> List[Dict]:
        """生成容量指标的趋势数据
        
        Args:
            timestamps: 时间戳列表
            
        Returns:
            趋势数据列表
        """
        count = len(timestamps)
        
        # 固定 total 值
        if self.metric_type == "cpu":
            # CPU 指标不需要单位转换
            if self.total_range:
                total = random.randint(int(self.total_range[0]), int(self.total_range[1]))
            else:
                total = random.randint(int(self._total_min), int(self._total_max))
            total_display = total
        else:
            # 其他容量指标需要单位转换
            if self.total_range:
                total = random.uniform(self.total_range[0], self.total_range[1])
            else:
                total = random.uniform(self._total_min, self._total_max)
            total_display = total / self.unit_multiplier
            if self.unit == "byte":
                total_display = int(total_display)
            else:
                total_display = round(total_display, 2)
        
        # 确定趋势范围
        if self.trend_range:
            min_val, max_val = self.trend_range
        else:
            if self.trend_field == "used":
                min_val = 0
                max_val = total_display
            else:  # usage
                min_val = 0.0
                max_val = 100.0
        
        # 生成趋势序列
        if self.trend_field == "used":
            used_values = self._generate_trend_values(count, min_val, max_val)
            # 格式化 used 值
            if self.metric_type == "cpu":
                used_display_values = [round(v, 2) for v in used_values]
            elif self.unit == "byte":
                used_display_values = [int(round(v)) for v in used_values]
            else:
                used_display_values = [round(v, 2) for v in used_values]
            
            # 计算 usage
            usage_values = [
                round((used / total_display * 100), 2) if total_display > 0 else 0.0
                for used in used_display_values
            ]
        else:  # usage
            usage_values = self._generate_trend_values(count, min_val, max_val)
            usage_values = [round(v, 2) for v in usage_values]
            
            # 计算 used
            used_display_values = [
                round(total_display * usage / 100, 2) if self.metric_type != "cpu" else round(total_display * usage / 100, 2)
                for usage in usage_values
            ]
        
        # 组装结果
        result = []
        for i, ts in enumerate(timestamps):
            used_val = used_display_values[i]
            usage_val = usage_values[i]
            # 计算 free
            free_val = total_display - used_val
            if self.metric_type == "cpu" or self.unit != "byte":
                free_val = round(free_val, 2)
            else:
                free_val = int(free_val)
            
            data_point = {
                "total": total_display,
                "used": used_val,
                "free": free_val,
                "usage": usage_val,
                "timestamp": ts
            }
            result.append(data_point)
        
        return result
    
    def _generate_rate_trend(self, timestamps: List[str]) -> List[Dict]:
        """生成速率指标的趋势数据
        
        Args:
            timestamps: 时间戳列表
            
        Returns:
            趋势数据列表
        """
        count = len(timestamps)
        
        # 速率指标暂时不支持趋势模式，保持随机生成
        # TODO: 未来可以扩展支持 rate_size 和 rate_ops 的趋势控制
        return [
            {**self._generate_rate_metric(), "timestamp": ts}
            for ts in timestamps
        ]
    
    def values(self) -> Optional[List[Dict]]:
        """容量指标不可枚举，速率指标也不可枚举"""
        return None
    
    def boundary_values(self) -> Optional[List[Dict]]:
        """生成边界值"""
        if self.metric_type in ["memory", "swap", "disk", "cpu"]:
            # 容量指标边界值
            # 边界1: total 最小值, used = 0
            # 边界2: total 最大值, used = total
            # 边界3: total 中间值, used = total/2
            
            # CPU 指标不需要单位转换
            if self.metric_type == "cpu":
                min_total = self._total_min
                max_total = self._total_max
                mid_total = (min_total + max_total) / 2
            else:
                min_total = self._total_min / self.unit_multiplier
                max_total = self._total_max / self.unit_multiplier
                mid_total = (min_total + max_total) / 2
            
            if self.metric_type == "cpu":
                min_total = int(min_total)
                max_total = int(max_total)
                mid_total = int(mid_total)
                used_min = 0
                used_max = max_total
                used_mid = round(mid_total / 2, 2)
            elif self.unit == "byte":
                min_total = int(min_total)
                max_total = int(max_total)
                mid_total = int(mid_total)
                used_min = 0
                used_max = max_total
                used_mid = mid_total // 2
            else:
                used_min = 0
                used_max = round(max_total, 2)
                used_mid = round(mid_total / 2, 2)
            
            return [
                {"total": min_total, "used": used_min, "free": min_total - used_min, "usage": 0.0},
                {"total": max_total, "used": used_max, "free": max_total - used_max, "usage": 100.0},
                {"total": mid_total, "used": used_mid, "free": mid_total - used_mid, "usage": 50.0},
            ]
        else:
            # 速率指标边界值
            min_size = self._rate_size_range[0] / self.unit_multiplier
            max_size = self._rate_size_range[1] / self.unit_multiplier
            min_ops = self._rate_ops_range[0]
            max_ops = self._rate_ops_range[1]
            
            if self.unit == "byte":
                min_size = int(min_size)
                max_size = int(max_size)
                min_ops = int(min_ops)
                max_ops = int(max_ops)
            
            return [
                {"rate_size": min_size, "rate_ops": min_ops},
                {"rate_size": max_size, "rate_ops": max_ops},
            ]
    
    def equivalence_classes(self) -> Optional[List[List[Dict]]]:
        """生成等价类"""
        if self.metric_type in ["memory", "swap", "disk", "cpu"]:
            # 容量指标等价类：低/中/高使用率
            # CPU 指标不需要单位转换
            if self.metric_type == "cpu":
                total = int((self._total_min + self._total_max) / 2)
            else:
                total = (self._total_min + self._total_max) / 2 / self.unit_multiplier
                if self.unit == "byte":
                    total = int(total)
            
            # 计算 used 值
            if self.metric_type == "cpu":
                used_low = round(total * 0.2, 2)
                used_mid = round(total * 0.5, 2)
                used_high = round(total * 0.8, 2)
            else:
                used_low = round(total * 0.2, 2)
                used_mid = round(total * 0.5, 2)
                used_high = round(total * 0.8, 2)
            
            return [
                # 低使用率 (0-33%)
                [{"total": total, "used": used_low, "free": total - used_low, "usage": 20.0}],
                # 中使用率 (33-66%)
                [{"total": total, "used": used_mid, "free": total - used_mid, "usage": 50.0}],
                # 高使用率 (66-100%)
                [{"total": total, "used": used_high, "free": total - used_high, "usage": 80.0}],
            ]
        else:
            # 速率指标等价类：低/中/高速率
            mid_size = sum(self._rate_size_range) / 2 / self.unit_multiplier
            mid_ops = sum(self._rate_ops_range) / 2
            
            if self.unit == "byte":
                mid_size = int(mid_size)
                mid_ops = int(mid_ops)
            
            return [
                # 低速率
                [{"rate_size": round(mid_size * 0.2, 2), "rate_ops": int(mid_ops * 0.2)}],
                # 中速率
                [{"rate_size": round(mid_size, 2), "rate_ops": int(mid_ops)}],
                # 高速率
                [{"rate_size": round(mid_size * 1.8, 2), "rate_ops": int(mid_ops * 1.8)}],
            ]
    
    def invalid_values(self) -> Optional[List[Dict]]:
        """生成非法值"""
        if self.metric_type in ["memory", "swap", "disk", "cpu"]:
            # 容量指标非法值
            return [
                # used > total
                {"total": 100, "used": 200, "free": -100, "usage": 50.0},
                # usage > 100%
                {"total": 100, "used": 50, "free": 50, "usage": 150.0},
                # usage 与 used/total 不匹配
                {"total": 100, "used": 50, "free": 50, "usage": 30.0},
                # free 与 total/used 不匹配
                {"total": 100, "used": 50, "free": 100, "usage": 50.0},
                # 负值
                {"total": -100, "used": 50, "free": -150, "usage": 50.0},
                {"total": 100, "used": -50, "free": 150, "usage": -50.0},
                # 类型错误
                {"total": "invalid", "used": 50, "free": 50, "usage": 50.0},
                {"total": 100, "used": None, "free": None, "usage": 50.0},
                # 缺少字段
                {"total": 100, "used": 50},  # 缺少 free 和 usage
            ]
        else:
            # 速率指标非法值
            return [
                # 负值
                {"rate_size": -100, "rate_ops": 1000},
                {"rate_size": 100, "rate_ops": -50},
                # 类型错误
                {"rate_size": "invalid", "rate_ops": 1000},
                {"rate_size": 100, "rate_ops": None},
                # 缺少字段
                {"rate_size": 100},  # 缺少 rate_ops
            ]
