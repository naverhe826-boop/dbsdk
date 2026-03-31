import pytest
from unittest.mock import Mock

from data_builder.strategies.value.advanced.ref import RefStrategy
from data_builder.strategies.basic import StrategyContext
from data_builder.exceptions import FieldPathError


class TestRefStrategy:
    """测试 RefStrategy 引用策略"""

    def test_init_with_ref_path_only(self):
        """测试仅使用引用路径初始化"""
        strategy = RefStrategy("user.name")
        assert strategy.ref_path == "user.name"
        assert strategy.transform is None

    def test_init_with_transform(self):
        """测试带转换函数初始化"""
        transform = lambda x: x.upper()
        strategy = RefStrategy("user.name", transform=transform)
        assert strategy.ref_path == "user.name"
        assert strategy.transform == transform

    def test_generate_simple_reference(self):
        """测试简单字段引用"""
        root_data = {"user": {"name": "Alice"}}
        ctx = Mock(spec=StrategyContext)
        ctx.root_data = root_data

        strategy = RefStrategy("user.name")
        result = strategy.generate(ctx)

        assert result == "Alice"

    def test_generate_nested_reference(self):
        """测试嵌套字段引用"""
        root_data = {"a": {"b": {"c": {"d": "deep_value"}}}}
        ctx = Mock(spec=StrategyContext)
        ctx.root_data = root_data

        strategy = RefStrategy("a.b.c.d")
        result = strategy.generate(ctx)

        assert result == "deep_value"

    def test_generate_array_index_reference(self):
        """测试数组索引引用"""
        root_data = {"users": [{"name": "Alice"}, {"name": "Bob"}]}
        ctx = Mock(spec=StrategyContext)
        ctx.root_data = root_data

        strategy = RefStrategy("users[1].name")
        result = strategy.generate(ctx)

        assert result == "Bob"

    def test_generate_single_array_index(self):
        """测试单个数组索引引用"""
        root_data = {"matrix": [[1, 2, 3], [4, 5, 6]]}
        ctx = Mock(spec=StrategyContext)
        ctx.root_data = root_data

        # 当前实现不支持连续索引 [0][2]，只支持 key[index] 格式
        strategy = RefStrategy("matrix[1]")
        result = strategy.generate(ctx)

        assert result == [4, 5, 6]

    def test_generate_with_transform(self):
        """测试使用转换函数"""
        root_data = {"value": 10}
        ctx = Mock(spec=StrategyContext)
        ctx.root_data = root_data

        strategy = RefStrategy("value", transform=lambda x: x * 2)
        result = strategy.generate(ctx)

        assert result == 20

    def test_generate_transform_string(self):
        """测试字符串转换函数"""
        root_data = {"text": "hello"}
        ctx = Mock(spec=StrategyContext)
        ctx.root_data = root_data

        strategy = RefStrategy("text", transform=str.upper)
        result = strategy.generate(ctx)

        assert result == "HELLO"

    def test_generate_reference_to_none(self):
        """测试引用字段值为 None"""
        root_data = {"value": None}
        ctx = Mock(spec=StrategyContext)
        ctx.root_data = root_data

        strategy = RefStrategy("value")
        result = strategy.generate(ctx)

        assert result is None

    def test_generate_reference_to_list(self):
        """测试引用列表类型字段"""
        root_data = {"items": [1, 2, 3]}
        ctx = Mock(spec=StrategyContext)
        ctx.root_data = root_data

        strategy = RefStrategy("items")
        result = strategy.generate(ctx)

        assert result == [1, 2, 3]

    def test_generate_reference_to_dict(self):
        """测试引用字典类型字段"""
        root_data = {"config": {"key": "value"}}
        ctx = Mock(spec=StrategyContext)
        ctx.root_data = root_data

        strategy = RefStrategy("config")
        result = strategy.generate(ctx)

        assert result == {"key": "value"}

    def test_field_path_error_nonexistent_key(self):
        """测试引用不存在的键抛出 FieldPathError"""
        root_data = {"user": {"name": "Alice"}}
        ctx = Mock(spec=StrategyContext)
        ctx.root_data = root_data

        strategy = RefStrategy("user.age")

        with pytest.raises(FieldPathError) as exc_info:
            strategy.generate(ctx)

        assert "找不到节点 'age'" in str(exc_info.value)

    def test_field_path_error_nonexistent_path(self):
        """测试引用不存在的路径抛出 FieldPathError"""
        root_data = {}
        ctx = Mock(spec=StrategyContext)
        ctx.root_data = root_data

        strategy = RefStrategy("nonexistent.path")

        with pytest.raises(FieldPathError) as exc_info:
            strategy.generate(ctx)

        assert "找不到节点 'nonexistent'" in str(exc_info.value)

    def test_field_path_error_invalid_array_index(self):
        """测试数组索引越界抛出 FieldPathError"""
        root_data = {"items": [1, 2, 3]}
        ctx = Mock(spec=StrategyContext)
        ctx.root_data = root_data

        strategy = RefStrategy("items[10]")

        with pytest.raises(FieldPathError) as exc_info:
            strategy.generate(ctx)

        assert "找不到节点 'items[10]'" in str(exc_info.value)

    def test_generate_string_index_access(self):
        """测试字符串索引访问（Python 字符串支持索引）"""
        root_data = {"value": "string"}
        ctx = Mock(spec=StrategyContext)
        ctx.root_data = root_data

        # Python 字符串支持索引访问，不会抛出异常
        strategy = RefStrategy("value[0]")
        result = strategy.generate(ctx)

        assert result == "s"

    def test_field_path_error_non_dict_key_access(self):
        """测试对非字典使用键访问抛出 FieldPathError"""
        root_data = {"value": 123}
        ctx = Mock(spec=StrategyContext)
        ctx.root_data = root_data

        strategy = RefStrategy("value.key")

        with pytest.raises(FieldPathError):
            strategy.generate(ctx)

    def test_values_returns_none(self):
        """测试 values() 方法返回 None"""
        strategy = RefStrategy("user.name")
        assert strategy.values() is None

    def test_boundary_values_returns_none(self):
        """测试 boundary_values() 方法返回 None"""
        strategy = RefStrategy("user.name")
        assert strategy.boundary_values() is None

    def test_equivalence_classes_returns_none(self):
        """测试 equivalence_classes() 方法返回 None"""
        strategy = RefStrategy("user.name")
        assert strategy.equivalence_classes() is None

    def test_invalid_values_returns_list(self):
        """测试 invalid_values() 返回无效引用场景列表"""
        strategy = RefStrategy("user.name")
        invalid = strategy.invalid_values()

        assert isinstance(invalid, list)
        assert None in invalid
        assert "" in invalid
        assert "nonexistent.path" in invalid

    def test_invalid_values_contains_invalid_formats(self):
        """测试 invalid_values() 包含格式错误的路径"""
        strategy = RefStrategy("user.name")
        invalid = strategy.invalid_values()

        assert ".." in invalid
        assert "." in invalid
        assert "a[b" in invalid
        assert "a]b" in invalid

    def test_get_value_by_path_simple(self):
        """测试 _get_value_by_path 简单路径"""
        strategy = RefStrategy("dummy")
        data = {"name": "Alice"}

        result = strategy._get_value_by_path(data, "name")
        assert result == "Alice"

    def test_get_value_by_path_nested(self):
        """测试 _get_value_by_path 嵌套路径"""
        strategy = RefStrategy("dummy")
        data = {"a": {"b": {"c": "value"}}}

        result = strategy._get_value_by_path(data, "a.b.c")
        assert result == "value"

    def test_get_value_by_path_array(self):
        """测试 _get_value_by_path 数组索引"""
        strategy = RefStrategy("dummy")
        data = {"items": [10, 20, 30]}

        result = strategy._get_value_by_path(data, "items[1]")
        assert result == 20

    def test_get_value_by_path_array_nested(self):
        """测试 _get_value_by_path 数组内嵌套对象"""
        strategy = RefStrategy("dummy")
        data = {"users": [{"name": "Alice", "age": 25}, {"name": "Bob", "age": 30}]}

        result = strategy._get_value_by_path(data, "users[0].name")
        assert result == "Alice"

    def test_get_value_by_path_complex_nested(self):
        """测试 _get_value_by_path 复杂嵌套结构"""
        strategy = RefStrategy("dummy")
        data = {
            "level1": {
                "level2": [
                    {"level3": {"target": "found"}}
                ]
            }
        }

        result = strategy._get_value_by_path(data, "level1.level2[0].level3.target")
        assert result == "found"

    def test_get_value_by_path_empty_dict(self):
        """测试 _get_value_by_path 空字典"""
        strategy = RefStrategy("dummy")

        with pytest.raises(FieldPathError):
            strategy._get_value_by_path({}, "key")

    def test_get_value_by_path_key_error(self):
        """测试 _get_value_by_path KeyError 异常"""
        strategy = RefStrategy("dummy")
        data = {"a": "value"}

        with pytest.raises(FieldPathError) as exc_info:
            strategy._get_value_by_path(data, "nonexistent")

        assert "找不到节点 'nonexistent'" in str(exc_info.value)

    def test_get_value_by_path_index_error(self):
        """测试 _get_value_by_path IndexError 异常"""
        strategy = RefStrategy("dummy")
        data = {"items": []}

        with pytest.raises(FieldPathError) as exc_info:
            strategy._get_value_by_path(data, "items[0]")

        assert "找不到节点 'items[0]'" in str(exc_info.value)

    def test_get_value_by_path_type_error(self):
        """测试 _get_value_by_path TypeError 异常"""
        strategy = RefStrategy("dummy")
        data = {"value": 123}

        with pytest.raises(FieldPathError) as exc_info:
            strategy._get_value_by_path(data, "value.key")

        assert "找不到节点 'key'" in str(exc_info.value)
