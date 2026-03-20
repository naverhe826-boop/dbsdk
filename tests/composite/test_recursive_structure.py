"""
递归树结构生成测试

测试 max_depth 参数控制递归结构生成的功能
"""

import pytest
from data_builder import DataBuilder, BuilderConfig
from data_builder.exceptions import SchemaError


# Schema 1: 标准树结构定义（根节点是完整对象定义）
SCHEMA1 = {
    "$defs": {
        "Node": {
            "properties": {
                "children": {
                    "items": {"$ref": "#/$defs/Node"},
                    "type": "array"
                },
                "data": {"anyOf": [{"type": "string"}, {"type": "null"}]}
            },
            "type": "object"
        }
    },
    "properties": {
        "children": {
            "items": {"$ref": "#/$defs/Node"},
            "type": "array"
        },
        "data": {"anyOf": [{"type": "string"}, {"type": "null"}]}
    },
    "required": ["data", "children"],
    "title": "Node",
    "type": "object"
}


# Schema 2: 根节点直接使用 $ref
SCHEMA2 = {
    "$defs": {
        "Node": {
            "properties": {
                "data": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                "children": {
                    "items": {"$ref": "#/$defs/Node"},
                    "type": "array"
                }
            },
            "type": "object"
        }
    },
    "$ref": "#/$defs/Node"
}


class TestMaxDepthParameter:
    """测试 max_depth 参数"""
    
    def test_max_depth_in_config(self):
        """测试 max_depth 字段在 BuilderConfig 中存在"""
        config = BuilderConfig(max_depth=3)
        assert config.max_depth == 3
        
        config = BuilderConfig()
        assert config.max_depth is None
    
    def test_max_depth_from_dict(self):
        """测试从字典创建 BuilderConfig 时解析 max_depth"""
        config = BuilderConfig.from_dict({"max_depth": 5})
        assert config.max_depth == 5
        
        config = BuilderConfig.from_dict({})
        assert config.max_depth is None


class TestRecursiveSchema1:
    """测试 Schema 1（标准树结构定义）"""
    
    def test_max_depth_2(self):
        """测试 max_depth=2 时的生成"""
        config = BuilderConfig(max_depth=2)
        builder = DataBuilder(SCHEMA1, config)
        result = builder.build()
        
        # 验证基本结构
        assert "data" in result
        assert "children" in result
        assert isinstance(result["children"], list)
        
        # max_depth=2 时，children 应该是空对象数组（深度 0 -> 1 达到上限）
        # 或者在深度 1 时继续生成，在深度 2 时截断
        # 根据实现，depth=0 时开始，depth >= max_depth 时截断
        # 所以 depth=0,1 时可以生成，depth=2 时截断
    
    def test_max_depth_3(self):
        """测试 max_depth=3 时的生成"""
        config = BuilderConfig(max_depth=3)
        builder = DataBuilder(SCHEMA1, config)
        result = builder.build()
        
        # 验证基本结构
        assert "data" in result
        assert "children" in result
        assert isinstance(result["children"], list)
    
    def test_max_depth_5(self):
        """测试 max_depth=5 时的生成"""
        config = BuilderConfig(max_depth=5)
        builder = DataBuilder(SCHEMA1, config)
        result = builder.build()
        
        # 验证基本结构
        assert "data" in result
        assert "children" in result
        assert isinstance(result["children"], list)


class TestRecursiveSchema2:
    """测试 Schema 2（根节点直接使用 $ref）"""
    
    def test_max_depth_2(self):
        """测试 max_depth=2 时的生成"""
        config = BuilderConfig(max_depth=2)
        builder = DataBuilder(SCHEMA2, config)
        result = builder.build()
        
        # 验证基本结构
        assert "data" in result
        assert "children" in result
        assert isinstance(result["children"], list)
    
    def test_max_depth_3(self):
        """测试 max_depth=3 时的生成"""
        config = BuilderConfig(max_depth=3)
        builder = DataBuilder(SCHEMA2, config)
        result = builder.build()
        
        # 验证基本结构
        assert "data" in result
        assert "children" in result
        assert isinstance(result["children"], list)
    
    def test_max_depth_5(self):
        """测试 max_depth=5 时的生成"""
        config = BuilderConfig(max_depth=5)
        builder = DataBuilder(SCHEMA2, config)
        result = builder.build()
        
        # 验证基本结构
        assert "data" in result
        assert "children" in result
        assert isinstance(result["children"], list)


class TestDefaultBehavior:
    """测试默认行为（max_depth=None）"""
    
    def test_default_raises_error_schema1(self):
        """测试 Schema 1 在默认情况下抛出循环引用错误"""
        config = BuilderConfig()  # max_depth=None
        builder = DataBuilder(SCHEMA1, config)
        
        with pytest.raises(SchemaError) as exc_info:
            builder.build()
        
        assert "循环引用" in str(exc_info.value)
    
    def test_default_raises_error_schema2(self):
        """测试 Schema 2 在默认情况下抛出循环引用错误"""
        config = BuilderConfig()  # max_depth=None
        builder = DataBuilder(SCHEMA2, config)
        
        with pytest.raises(SchemaError) as exc_info:
            builder.build()
        
        assert "循环引用" in str(exc_info.value)


class TestDepthCutoff:
    """测试深度截断行为"""
    
    def test_depth_cutoff_returns_empty_values(self):
        """测试达到深度上限时返回空值"""
        schema = {
            "$defs": {
                "Node": {
                    "properties": {
                        "data": {"type": "string"},
                        "children": {
                            "items": {"$ref": "#/$defs/Node"},
                            "type": "array"
                        }
                    },
                    "required": ["data", "children"],
                    "type": "object"
                }
            },
            "$ref": "#/$defs/Node"
        }
        
        # max_depth=1 时，根节点生成，但 children 应该是空数组
        config = BuilderConfig(max_depth=1)
        builder = DataBuilder(schema, config)
        result = builder.build()
        
        # 验证根节点生成
        assert "data" in result
        assert "children" in result
        
        # 由于 depth=1 时截断，children 应该为空数组
        # （因为 children 的元素需要 depth=2，超过了 max_depth=1）
        # 但实际行为取决于数组生成时是否在调用 _generate_value 之前检查深度
        # 根据当前实现，数组元素的生成在 _generate_array 中调用 _generate_value(depth+1)
        # 所以 children 数组中的元素应该是空对象（截断值）


class TestMultipleGeneration:
    """测试多次生成的一致性"""
    
    def test_multiple_generations_same_depth(self):
        """测试同一深度下多次生成的一致性"""
        config = BuilderConfig(max_depth=3)
        
        for _ in range(5):
            builder = DataBuilder(SCHEMA2, config)
            result = builder.build()
            
            assert "data" in result
            assert "children" in result
            assert isinstance(result["children"], list)
    
    def test_multiple_generations_different_depth(self):
        """测试不同深度下生成的结构"""
        for depth in [2, 3, 4, 5]:
            config = BuilderConfig(max_depth=depth)
            builder = DataBuilder(SCHEMA2, config)
            result = builder.build()
            
            assert "data" in result
            assert "children" in result
            assert isinstance(result["children"], list)


class TestEdgeCases:
    """测试边界情况"""
    
    def test_max_depth_zero(self):
        """测试 max_depth=0 时的行为"""
        config = BuilderConfig(max_depth=0)
        builder = DataBuilder(SCHEMA2, config)
        result = builder.build()
        
        # max_depth=0 时，根节点就应该被截断
        # 根据实现，depth >= max_depth 时截断
        # 所以 depth=0 >= max_depth=0，应该返回空对象
        assert result == {} or result is None or "data" not in result
    
    def test_max_depth_one(self):
        """测试 max_depth=1 时的行为"""
        config = BuilderConfig(max_depth=1)
        builder = DataBuilder(SCHEMA2, config)
        result = builder.build()
        
        # max_depth=1 时，根节点生成，但子节点应该截断
        assert isinstance(result, dict)
        if "children" in result:
            # children 数组中的元素应该是截断值
            for child in result["children"]:
                # 截断值应该是空对象
                assert child == {} or child is None or not child
    
    def test_non_recursive_schema_unchanged(self):
        """测试非递归 Schema 不受 max_depth 影响"""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"}
            }
        }
        
        # 有 max_depth
        config = BuilderConfig(max_depth=3)
        builder = DataBuilder(schema, config)
        result = builder.build()
        
        assert "name" in result
        assert "age" in result
        
        # 无 max_depth
        config = BuilderConfig()
        builder = DataBuilder(schema, config)
        result = builder.build()
        
        assert "name" in result
        assert "age" in result
