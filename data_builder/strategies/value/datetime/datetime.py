import random
import re
from datetime import datetime, timedelta
from typing import Any, List, Optional

from ...basic import Strategy, StrategyContext
from ....exceptions import StrategyError

# 用于解析日期字符串的正则
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
# 用于解析时间字符串的正则
TIME_PATTERN = re.compile(r"^(\d{2}):(\d{2}):(\d{2})$")
# 用于解析日期时间字符串的正则
DATETIME_PATTERN = re.compile(r"^(\d{4})-(\d{2})-(\d{2})\s+(\d{2}):(\d{2}):(\d{2})$")


class DateTimeStrategy(Strategy):
    """日期时间策略

    支持以下参数：
    - start/end: 日期时间范围
    - format: 输出格式
    - timezone: 时区 (IANA 名称或 UTC 偏移)
    - anchor: 预定义关键字 (now/today/yesterday/week/month/year)
    - offset: 基于 anchor 的偏移量
    - date_range: 日期范围 "YYYY-MM-DD,YYYY-MM-DD"
    - time_range: 时间范围 "HH:MM:SS,HH:MM:SS"
    - specific_date: 指定日期 "YYYY-MM-DD"
    - specific_time: 指定时间 "HH:MM:SS"

    参数优先级：
    1. anchor + offset
    2. specific_date + specific_time
    3. date_range + time_range
    4. start/end (兜底)
    """

    def __init__(
        self,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        format: str = "%Y-%m-%d %H:%M:%S",
        timezone: Optional[str] = None,
        anchor: Optional[str] = None,
        offset: Optional[str] = None,
        date_range: Optional[str] = None,
        time_range: Optional[str] = None,
        specific_date: Optional[str] = None,
        specific_time: Optional[str] = None,
    ):
        self.format = format
        self.timezone = timezone
        self.anchor = anchor
        self.offset = offset
        self.date_range = date_range
        self.time_range = time_range
        self.specific_date = specific_date
        self.specific_time = specific_time

        # 解析并设置 start/end（如果提供）
        # 对于 anchor 模式，start/end 由 generate 方法计算
        if anchor is None:
            # 非 anchor 模式，使用传统的 start/end
            # 解析字符串输入为 datetime 对象
            self.start = self._parse_datetime_string(start) if start else datetime.now() - timedelta(days=365)
            self.end = self._parse_datetime_string(end) if end else datetime.now()
        else:
            # anchor 模式，start/end 将在 generate 时计算
            self.start = None
            self.end = None

    def _parse_datetime_string(self, value) -> datetime:
        """将字符串解析为 datetime 对象
        
        支持的格式：
        - "YYYY-MM-DD"
        - "YYYY-MM-DD HH:MM:SS"
        - "YYYY-MM-DDTHH:MM:SS"
        - datetime 对象（直接返回）
        """
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            # 尝试多种格式
            formats = [
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%d",
            ]
            for fmt in formats:
                try:
                    return datetime.strptime(value, fmt)
                except ValueError:
                    continue
            raise ValueError(f"无法解析日期时间字符串: {value}")
        return value

    def _get_timezone_offset(self, tz_str: str) -> Optional[timedelta]:
        """解析 UTC 偏移字符串，返回 timedelta"""
        pattern = re.compile(r"^([+-])(\d{2}):(\d{2})$")
        match = pattern.match(tz_str)
        if match:
            sign = 1 if match.group(1) == "+" else -1
            hours = int(match.group(2))
            minutes = int(match.group(3))
            return sign * timedelta(hours=hours, minutes=minutes)
        return None

    def _get_tzinfo(self) -> Optional[Any]:
        """获取时区信息"""
        if not self.timezone:
            return None

        # 尝试解析 UTC 偏移
        tz_offset = self._get_timezone_offset(self.timezone)
        if tz_offset is not None:
            # 返回一个简单的固定偏移时区
            from datetime import timezone
            return timezone(tz_offset)

        # 尝试使用 IANA 时区名称
        try:
            from zoneinfo import ZoneInfo
            return ZoneInfo(self.timezone)
        except Exception:
            raise StrategyError(
                f"DateTimeStrategy: 无效的时区 '{self.timezone}'，请使用 IANA 时区名称或 UTC 偏移格式"
            )

    def _get_anchor_range(self) -> tuple:
        """根据 anchor 计算日期时间范围

        Returns:
            tuple: (start, end) datetime tuple
        """
        now = datetime.now()
        tz = self._get_tzinfo()

        # 如果有时区，将 now 转换为对应时区
        if tz:
            now = now.replace(tzinfo=tz)

        # 计算当前时区的时间（可能需要调整）
        if tz:
            # 获取当前时区的"本地"时间
            now = datetime.now(tz)
            # 转换为 naive datetime 用于计算
            now_naive = now.replace(tzinfo=None)
        else:
            now_naive = now.replace(tzinfo=None)

        anchor_lower = self.anchor.lower()

        if anchor_lower == "now":
            # now = 当前时刻
            return (now_naive, now_naive)

        elif anchor_lower == "today":
            # today = 今天 00:00:00 ~ 23:59:59
            start = now_naive.replace(hour=0, minute=0, second=0, microsecond=0)
            end = now_naive.replace(hour=23, minute=59, second=59, microsecond=999999)
            return (start, end)

        elif anchor_lower == "yesterday":
            # yesterday = 昨天 00:00:00 ~ 23:59:59
            yesterday = now_naive - timedelta(days=1)
            start = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
            end = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)
            return (start, end)

        elif anchor_lower == "week":
            # week = 本周（周一 00:00 ~ 周日 23:59:59）
            # 获取本周 Monday
            weekday = now_naive.weekday()
            monday = now_naive - timedelta(days=weekday)
            start = monday.replace(hour=0, minute=0, second=0, microsecond=0)
            # 周日
            sunday = monday + timedelta(days=6)
            end = sunday.replace(hour=23, minute=59, second=59, microsecond=999999)
            return (start, end)

        elif anchor_lower == "month":
            # month = 本月第一天 00:00 ~ 本月最后一天 23:59:59
            # 本月第一天
            start = now_naive.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            # 计算本月最后一天
            if now_naive.month == 12:
                next_month = now_naive.replace(year=now_naive.year + 1, month=1, day=1)
            else:
                next_month = now_naive.replace(month=now_naive.month + 1, day=1)
            last_day = (next_month - timedelta(days=1)).day
            end = now_naive.replace(
                day=last_day, hour=23, minute=59, second=59, microsecond=999999
            )
            return (start, end)

        elif anchor_lower == "year":
            # year = 今年1月1日 00:00 ~ 今年12月31日 23:59:59
            start = now_naive.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            end = now_naive.replace(month=12, day=31, hour=23, minute=59, second=59, microsecond=999999)
            return (start, end)

        else:
            raise StrategyError(
                f"DateTimeStrategy: 无效的 anchor '{self.anchor}'，"
                f"支持的关键字: now, today, yesterday, week, month, year"
            )

    def _parse_offset(self) -> timedelta:
        """解析 offset 字符串为 timedelta

        格式支持：
        - "+1d" (1天)
        - "-2h" (2小时)
        - "+1d 2h 30m"
        - "-1M" (1月)
        - "-1w" (1周)

        单位：d(天), h(小时), m(分钟), s(秒), w(周), M(月)
        """
        if not self.offset:
            return timedelta(0)

        offset_str = self.offset.strip()
        total_delta = timedelta(0)

        # 正则匹配多个偏移量片段
        # 例如: "+1d 2h 30m" 或 "-1w"
        pattern = re.compile(r"([+-]?)(\d+)([dhmswM])")

        matches = pattern.findall(offset_str)
        if not matches:
            raise StrategyError(
                f"DateTimeStrategy: 无效的 offset 格式 '{self.offset}'，"
                f"支持的格式: +1d, -2h, +1d 2h 30m, -1M, -1w"
            )

        for sign_str, value_str, unit in matches:
            value = int(value_str)
            sign = 1 if sign_str == "+" or sign_str == "" else -1

            if unit == "d":
                delta = timedelta(days=value)
            elif unit == "h":
                delta = timedelta(hours=value)
            elif unit == "m":
                delta = timedelta(minutes=value)
            elif unit == "s":
                delta = timedelta(seconds=value)
            elif unit == "w":
                delta = timedelta(weeks=value)
            elif unit == "M":
                # 月的情况特殊处理，按30天计算
                delta = timedelta(days=value * 30)
            else:
                raise StrategyError(
                    f"DateTimeStrategy: 无效的 offset 单位 '{unit}'，"
                    f"支持的单位: d, h, m, s, w, M"
                )

            total_delta += sign * delta

        return total_delta

    def _parse_date_range(self) -> tuple:
        """解析 date_range 字符串

        格式: "YYYY-MM-DD,YYYY-MM-DD"
        """
        if not self.date_range:
            return None

        parts = self.date_range.split(",")
        if len(parts) != 2:
            raise StrategyError(
                f"DateTimeStrategy: 无效的 date_range 格式 '{self.date_range}'，"
                f"正确格式: YYYY-MM-DD,YYYY-MM-DD"
            )

        start_str = parts[0].strip()
        end_str = parts[1].strip()

        if not DATE_PATTERN.match(start_str) or not DATE_PATTERN.match(end_str):
            raise StrategyError(
                f"DateTimeStrategy: date_range 中的日期格式不正确，应为 YYYY-MM-DD"
            )

        start = datetime.strptime(start_str, "%Y-%m-%d")
        end = datetime.strptime(end_str, "%Y-%m-%d")

        # 设置为当天的开始和结束
        start = start.replace(hour=0, minute=0, second=0)
        end = end.replace(hour=23, minute=59, second=59)

        return (start, end)

    def _parse_time_range(self) -> tuple:
        """解析 time_range 字符串

        格式: "HH:MM:SS,HH:MM:SS"
        """
        if not self.time_range:
            return None

        parts = self.time_range.split(",")
        if len(parts) != 2:
            raise StrategyError(
                f"DateTimeStrategy: 无效的 time_range 格式 '{self.time_range}'，"
                f"正确格式: HH:MM:SS,HH:MM:SS"
            )

        start_str = parts[0].strip()
        end_str = parts[1].strip()

        start_match = TIME_PATTERN.match(start_str)
        end_match = TIME_PATTERN.match(end_str)

        if not start_match or not end_match:
            raise StrategyError(
                f"DateTimeStrategy: time_range 中的时间格式不正确，应为 HH:MM:SS"
            )

        start = datetime.strptime(start_str, "%H:%M:%S")
        end = datetime.strptime(end_str, "%H:%M:%S")

        return (start, end)

    def _parse_specific_date(self) -> datetime:
        """解析 specific_date 字符串为 datetime"""
        if not self.specific_date:
            return None

        if not DATE_PATTERN.match(self.specific_date):
            raise StrategyError(
                f"DateTimeStrategy: 无效的 specific_date 格式 '{self.specific_date}'，"
                f"正确格式: YYYY-MM-DD"
            )

        return datetime.strptime(self.specific_date, "%Y-%m-%d")

    def _parse_specific_time(self) -> datetime:
        """解析 specific_time 字符串为 datetime"""
        if not self.specific_time:
            return None

        if not TIME_PATTERN.match(self.specific_time):
            raise StrategyError(
                f"DateTimeStrategy: 无效的 specific_time 格式 '{self.specific_time}'，"
                f"正确格式: HH:MM:SS"
            )

        return datetime.strptime(self.specific_time, "%H:%M:%S")

    def _resolve_datetime_params(self) -> tuple:
        """根据参数优先级解析并返回 start 和 end

        参数优先级：
        1. anchor + offset
        2. specific_date + specific_time
        3. date_range + time_range
        4. start/end (兜底)
        """
        # 优先级1: anchor + offset
        if self.anchor:
            start, end = self._get_anchor_range()
            # 应用 offset
            offset_delta = self._parse_offset()
            start = start + offset_delta
            end = end + offset_delta
            return (start, end)

        # 优先级2: specific_date + specific_time
        if self.specific_date:
            base_date = self._parse_specific_date()
            if self.specific_time:
                time = self._parse_specific_time()
                start = base_date.replace(
                    hour=time.hour, minute=time.minute, second=time.second
                )
                end = start
            else:
                # 只有 specific_date，没有 specific_time
                start = base_date.replace(hour=0, minute=0, second=0)
                end = base_date.replace(hour=23, minute=59, second=59)
            return (start, end)

        # 仅有 specific_time（无 specific_date）
        if self.specific_time:
            time = self._parse_specific_time()
            # 使用今天作为基准日期，时间固定为指定时间
            today = datetime.now().replace(
                hour=time.hour, minute=time.minute, second=time.second
            )
            return (today, today)

        # 优先级3: date_range + time_range
        if self.date_range:
            start, end = self._parse_date_range()

            if self.time_range:
                time_start, time_end = self._parse_time_range()
                # 将 time_range 应用到 date_range
                start = start.replace(
                    hour=time_start.hour,
                    minute=time_start.minute,
                    second=time_start.second
                )
                end = end.replace(
                    hour=time_end.hour,
                    minute=time_end.minute,
                    second=time_end.second
                )

            return (start, end)

        # 优先级4: 兜底 - 使用 start/end
        # 如果 start/end 没有提供，使用默认值
        start = self.start or datetime.now() - timedelta(days=365)
        end = self.end or datetime.now()
        return (start, end)

    def generate(self, ctx: StrategyContext) -> str:
        # 根据参数优先级解析 start 和 end
        start, end = self._resolve_datetime_params()

        # 验证范围
        delta = end - start
        total_seconds = int(delta.total_seconds())
        if total_seconds < 0:
            raise StrategyError(
                f"DateTimeStrategy: start ({start}) 不能晚于 end ({end})"
            )

        # 随机生成一个时间点
        if total_seconds == 0:
            dt = start
        else:
            random_seconds = random.randint(0, total_seconds)
            dt = start + timedelta(seconds=random_seconds)

        return dt.strftime(self.format)

    def boundary_values(self) -> Optional[List[str]]:
        start, end = self._resolve_datetime_params()
        total_seconds = int((end - start).total_seconds())
        candidates = [start]
        if total_seconds >= 1:
            candidates.append(start + timedelta(seconds=1))
        if total_seconds >= 2:
            candidates.append(end - timedelta(seconds=1))
        candidates.append(end)
        # 去重保序
        seen = set()
        result = []
        for dt in candidates:
            s = dt.strftime(self.format)
            if s not in seen:
                seen.add(s)
                result.append(s)
        return result

    def equivalence_classes(self) -> Optional[List[List[str]]]:
        start, end = self._resolve_datetime_params()
        mid = start + (end - start) / 2
        return [
            [start.strftime(self.format)],
            [mid.strftime(self.format)],
            [end.strftime(self.format)],
        ]

    def invalid_values(self) -> Optional[List[Any]]:
        start, end = self._resolve_datetime_params()
        before = start - timedelta(days=1)
        after = end + timedelta(days=1)
        return [
            before.strftime(self.format),
            after.strftime(self.format),
            "not-a-date",
            12345,
            None,
        ]
