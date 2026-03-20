"""
ConcatStrategy 集成测试用例
"""
import pytest

from data_builder.strategies.basic.base import StrategyContext
from data_builder.strategies.value.external import FakerStrategy
from data_builder.strategies.value.string import RandomStringStrategy
from data_builder.strategies.value.advanced.concat import ConcatStrategy
from data_builder.strategies.value.registry import StrategyRegistry
from data_builder.exceptions import StrategyError


def _ctx(**kwargs):
    """创建测试用 StrategyContext"""
    defaults = dict(field_path="test", field_schema={}, root_data={}, parent_data={}, index=0)
    defaults.update(kwargs)
    return StrategyContext(**defaults)


class TestConcatStrategyBasic:
    """基本级联测试"""

    def test_basic_concat_faker_and_random_string(self):
        """测试 faker.name + random_string(5位数字) 基本级联"""
        s = ConcatStrategy(
            strategies=[
                FakerStrategy(method='name'),
                RandomStringStrategy(length=5, charset='0123456789')
            ]
        )
        result = s.generate(_ctx())
        # 结果应该是 名字 + 5位数字
        assert isinstance(result, str)
        assert len(result) >= 3  # 名字至少有1个字符 + 5个数字
        # 最后5位应该是数字
        assert result[-5:].isdigit()

    def test_concat_with_separator(self):
        """测试带分隔符配置"""
        s = ConcatStrategy(
            strategies=[
                FakerStrategy(method='first_name'),
                FakerStrategy(method='last_name')
            ],
            separators=['-']
        )
        result = s.generate(_ctx())
        assert isinstance(result, str)
        assert '-' in result

    def test_multiple_strategy_concat(self):
        """测试多策略级联（3个以上）"""
        s = ConcatStrategy(
            strategies=[
                FakerStrategy(method='first_name'),
                FakerStrategy(method='last_name'),
                RandomStringStrategy(length=4, charset='0123456789')
            ],
            separators=['_', '-']
        )
        result = s.generate(_ctx())
        assert isinstance(result, str)
        assert '_' in result
        assert '-' in result

    def test_generate_value_format(self):
        """测试 generate 生成的值的格式"""
        s = ConcatStrategy(
            strategies=[
                RandomStringStrategy(length=3, charset='abc'),
                RandomStringStrategy(length=2, charset='xy')
            ]
        )
        result = s.generate(_ctx())
        assert isinstance(result, str)
        assert len(result) == 5  # 3 + 2


class TestConcatStrategyValues:
    """values() 方法测试"""

    def test_values_returns_cartesian_product(self):
        """测试 values() 方法返回值正确（笛卡尔积）"""
        s = ConcatStrategy(
            strategies=[
                RandomStringStrategy(length=2, charset='ab'),  # 2^2=4
                RandomStringStrategy(length=1, charset='xy')   # 2^1=2
            ]
        )
        values = s.values()
        assert values is not None
        assert len(values) == 8  # 4 * 2 = 8
        # 验证格式
        for v in values:
            assert len(v) == 3  # 2 + 1

    def test_values_with_separator(self):
        """测试带分隔符的 values()"""
        s = ConcatStrategy(
            strategies=[
                RandomStringStrategy(length=1, charset='ab'),
                RandomStringStrategy(length=1, charset='xy')
            ],
            separators=['-']
        )
        values = s.values()
        assert values is not None
        assert len(values) == 4  # 2 * 2 = 4
        for v in values:
            assert '-' in v
            assert v.count('-') == 1

    def test_values_returns_none_when_child_not_enumerable(self):
        """测试当子策略不可枚举时返回 None"""
        s = ConcatStrategy(
            strategies=[
                FakerStrategy(method='name'),  # 不可枚举
                RandomStringStrategy(length=2, charset='ab')
            ]
        )
        values = s.values()
        assert values is None


class TestConcatStrategyEdgeCases:
    """边界情况测试"""

    def test_empty_strategies_raises_error(self):
        """测试空 strategies 抛出异常"""
        with pytest.raises(StrategyError):
            ConcatStrategy(strategies=[])

    def test_single_strategy(self):
        """测试单个策略"""
        s = ConcatStrategy(
            strategies=[
                FakerStrategy(method='name')
            ]
        )
        result = s.generate(_ctx())
        assert isinstance(result, str)
        # values 应该返回 None（子策略不可枚举）
        assert s.values() is None

    def test_separators_mismatch_count(self):
        """测试 separators 数量不匹配"""
        with pytest.raises(StrategyError):
            s = ConcatStrategy(
                strategies=[
                    FakerStrategy(method='first_name'),
                    FakerStrategy(method='last_name'),
                    FakerStrategy(method='name')
                ],
                separators=['-', '_', '/']  # 需要2个分隔符，但提供3个
            )
            # 访问 separators 属性触发验证
            _ = s.separators

    def test_separators_single_reused(self):
        """测试单个 separator 复用于所有连接"""
        s = ConcatStrategy(
            strategies=[
                RandomStringStrategy(length=1, charset='abc'),
                RandomStringStrategy(length=1, charset='xyz'),
                RandomStringStrategy(length=1, charset='123')
            ],
            separators=['-']  # 1个 separator 复用于 2个连接位置
        )
        result = s.generate(_ctx())
        assert result.count('-') == 2


class TestConcatStrategyRegistry:
    """通过 registry.create() 创建测试"""

    def test_create_from_config(self):
        """测试通过 registry.create() 从配置创建 ConcatStrategy"""
        config = {
            "type": "concat",
            "strategies": [
                {"type": "faker", "method": "name"},
                {"type": "random_string", "length": 5, "charset": "0123456789"}
            ],
            "separators": [""]
        }
        s = StrategyRegistry.create(config)
        assert isinstance(s, ConcatStrategy)
        result = s.generate(_ctx())
        assert isinstance(result, str)
        assert result[-5:].isdigit()

    def test_create_with_separator_from_config(self):
        """测试从配置创建带分隔符的 ConcatStrategy"""
        config = {
            "type": "concat",
            "strategies": [
                {"type": "fixed", "value": "user"},
                {"type": "fixed", "value": "id"}
            ],
            "separators": ["_"]
        }
        s = StrategyRegistry.create(config)
        assert isinstance(s, ConcatStrategy)
        result = s.generate(_ctx())
        assert result == "user_id"


class TestConcatStrategyOtherMethods:
    """其他方法测试"""

    def test_boundary_values(self):
        """测试 boundary_values 方法"""
        s = ConcatStrategy(
            strategies=[
                RandomStringStrategy(length=2, charset='ab'),
                RandomStringStrategy(length=1, charset='xy')
            ]
        )
        bv = s.boundary_values()
        assert bv is not None
        assert isinstance(bv, list)

    def test_equivalence_classes(self):
        """测试 equivalence_classes 方法"""
        s = ConcatStrategy(
            strategies=[
                RandomStringStrategy(length=2, charset='ab'),
                RandomStringStrategy(length=1, charset='xy')
            ]
        )
        ec = s.equivalence_classes()
        assert ec is not None
        assert isinstance(ec, list)

    def test_invalid_values(self):
        """测试 invalid_values 方法"""
        s = ConcatStrategy(
            strategies=[
                RandomStringStrategy(length=2, charset='ab'),
                RandomStringStrategy(length=1, charset='xy')
            ]
        )
        iv = s.invalid_values()
        assert iv is not None
        assert isinstance(iv, list)


class TestConcatStrategyFieldType:
    """字段类型校验测试"""

    def test_string_type_allowed(self):
        """测试 string 类型允许使用 concat 策略"""
        s = ConcatStrategy(
            strategies=[
                FakerStrategy(method='name'),
                RandomStringStrategy(length=5, charset='0123456789')
            ]
        )
        # string 类型应该正常通过
        result = s.generate(_ctx(field_schema={"type": "string"}))
        assert isinstance(result, str)

    def test_no_field_schema_allowed(self):
        """测试无 field_schema 时允许使用 concat 策略"""
        s = ConcatStrategy(
            strategies=[
                FakerStrategy(method='name'),
                RandomStringStrategy(length=5, charset='0123456789')
            ]
        )
        # 无 field_schema 时应该正常通过
        result = s.generate(_ctx(field_schema={}))
        assert isinstance(result, str)

    def test_integer_type_not_allowed(self):
        """测试 integer 类型不允许使用 concat 策略"""
        s = ConcatStrategy(
            strategies=[
                FakerStrategy(method='name'),
                RandomStringStrategy(length=5, charset='0123456789')
            ]
        )
        # integer 类型应该抛出异常
        with pytest.raises(StrategyError) as exc_info:
            s.generate(_ctx(field_schema={"type": "integer"}))
        assert "必须是 string" in str(exc_info.value)

    def test_number_type_not_allowed(self):
        """测试 number 类型不允许使用 concat 策略"""
        s = ConcatStrategy(
            strategies=[
                FakerStrategy(method='name'),
                RandomStringStrategy(length=5, charset='0123456789')
            ]
        )
        # number 类型应该抛出异常
        with pytest.raises(StrategyError) as exc_info:
            s.generate(_ctx(field_schema={"type": "number"}))
        assert "必须是 string" in str(exc_info.value)

    def test_boolean_type_not_allowed(self):
        """测试 boolean 类型不允许使用 concat 策略"""
        s = ConcatStrategy(
            strategies=[
                FakerStrategy(method='name'),
                RandomStringStrategy(length=5, charset='0123456789')
            ]
        )
        # boolean 类型应该抛出异常
        with pytest.raises(StrategyError) as exc_info:
            s.generate(_ctx(field_schema={"type": "boolean"}))
        assert "必须是 string" in str(exc_info.value)
