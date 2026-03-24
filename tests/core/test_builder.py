"""DataBuilder 核心类测试"""

import pytest
from data_builder import DataBuilder, BuilderConfig, FieldPolicy, enum, seq, fixed
from data_builder.combinations import CombinationMode, CombinationSpec


class TestDataBuilderInit:
    """测试 DataBuilder 初始化"""
    
    def test_init_with_schema_only(self):
        """仅使用 schema 初始化"""
        schema = {"type": "object", "properties": {"name": {"type": "string"}}}
        builder = DataBuilder(schema)
        
        assert builder.schema == schema
        assert builder.config == BuilderConfig()
        assert builder._policy_map == {}
    
    def test_init_with_config(self):
        """使用 schema 和 config 初始化"""
        schema = {"type": "object", "properties": {"status": {"type": "string"}}}
        config = BuilderConfig(
            policies=[FieldPolicy("status", enum(["active", "inactive"]))]
        )
        builder = DataBuilder(schema, config)
        
        assert builder.schema == schema
        assert len(builder._policy_map) == 1
        assert "status" in builder._policy_map
    
    def test_config_from_dict(self):
        """测试从字典创建配置"""
        config_dict = {
            "policies": [
                {"path": "id", "strategy": {"type": "sequence", "start": 1}},
                {"path": "status", "strategy": {"type": "enum", "values": ["a", "b"]}}
            ]
        }
        
        config = DataBuilder.config_from_dict(config_dict)
        
        assert len(config.policies) == 2
        assert config.policies[0].path == "id"
        assert config.policies[1].path == "status"


class TestDataBuilderBuild:
    """测试 build() 方法"""
    
    def test_build_single_object(self):
        """生成单个对象"""
        schema = {"type": "object", "properties": {"name": {"type": "string"}}}
        builder = DataBuilder(schema)
        
        result = builder.build()
        
        assert isinstance(result, dict)
        assert "name" in result
    
    def test_build_multiple_objects(self):
        """生成多个对象"""
        schema = {"type": "object", "properties": {"id": {"type": "integer"}}}
        builder = DataBuilder(schema, BuilderConfig(count=5))
        
        results = builder.build()
        
        assert isinstance(results, list)
        assert len(results) == 5
    
    def test_build_with_count_override(self):
        """测试 count 参数覆盖配置"""
        schema = {"type": "object", "properties": {"x": {"type": "integer"}}}
        builder = DataBuilder(schema, BuilderConfig(count=3))
        
        results = builder.build(count=10)
        
        assert len(results) == 10
    
    def test_build_with_field_policy(self):
        """测试字段策略应用"""
        schema = {
            "type": "object",
            "properties": {
                "status": {"type": "string"},
                "order": {"type": "integer"}
            }
        }
        config = BuilderConfig(
            policies=[
                FieldPolicy("status", enum(["active", "inactive"])),
                FieldPolicy("order", seq(start=1))
            ]
        )
        builder = DataBuilder(schema, config)
        
        results = builder.build(count=5)
        
        for i, result in enumerate(results):
            assert result["status"] in ["active", "inactive"]
            assert result["order"] == i + 1
    
    def test_build_with_combination_mode(self):
        """测试组合模式生成"""
        schema = {
            "type": "object",
            "properties": {
                "status": {"type": "string"},
                "role": {"type": "string"}
            }
        }
        config = BuilderConfig(
            policies=[
                FieldPolicy("status", enum(["active", "inactive"])),
                FieldPolicy("role", enum(["admin", "user"]))
            ],
            combinations=[
                CombinationSpec(mode=CombinationMode.CARTESIAN, fields=["status", "role"])
            ]
        )
        builder = DataBuilder(schema, config)
        
        results = builder.build()
        
        # 笛卡尔积：2 × 2 = 4 种组合
        assert len(results) == 4
        
        pairs = {(r["status"], r["role"]) for r in results}
        expected = {
            ("active", "admin"), ("active", "user"),
            ("inactive", "admin"), ("inactive", "user")
        }
        assert pairs == expected


class TestFindStrategy:
    """测试 _find_strategy() 方法"""
    
    def test_exact_match(self):
        """精确匹配"""
        schema = {"type": "object", "properties": {"status": {"type": "string"}}}
        config = BuilderConfig(
            policies=[FieldPolicy("status", fixed("active"))]
        )
        builder = DataBuilder(schema, config)
        
        strategy = builder._find_strategy("status")
        
        assert strategy is not None
    
    def test_wildcard_match_user_star(self):
        """user.* 通配符匹配"""
        schema = {
            "type": "object",
            "properties": {
                "user": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "email": {"type": "string"}
                    }
                }
            }
        }
        config = BuilderConfig(
            policies=[FieldPolicy("user.*", fixed("test"))]
        )
        builder = DataBuilder(schema, config)
        
        # 匹配 user.name 和 user.email
        strategy1 = builder._find_strategy("user.name")
        strategy2 = builder._find_strategy("user.email")
        
        # 两个路径应该返回同一个策略实例
        assert strategy1 is not None
        assert strategy2 is not None
        assert strategy1 is strategy2  # 同一个实例
        
        # 注意：由于 fnmatch 的行为，user.* 会匹配 user.profile.age
        # 这是一个已知的实现细节，fnmatch 的 * 会匹配包括 . 在内的所有字符
    
    def test_wildcard_match_star_field(self):
        """*.field 通配符匹配"""
        schema = {
            "type": "object",
            "properties": {
                "id": {"type": "integer"},
                "user": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"}
                    }
                }
            }
        }
        config = BuilderConfig(
            policies=[FieldPolicy("*.id", seq(start=1))]
        )
        builder = DataBuilder(schema, config)
        
        # 匹配顶层 id
        strategy1 = builder._find_strategy("id")
        # 匹配 user.id
        strategy2 = builder._find_strategy("user.id")
        
        # 两个路径应该返回同一个策略实例
        assert strategy1 is not None
        assert strategy2 is not None
        assert strategy1 is strategy2  # 同一个实例
    
    def test_wildcard_match_array(self):
        """[*] 数组通配符匹配"""
        schema = {
            "type": "object",
            "properties": {
                "items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {"price": {"type": "number"}}
                    }
                }
            }
        }
        config = BuilderConfig(
            policies=[FieldPolicy("items[*].price", fixed(99.99))]
        )
        builder = DataBuilder(schema, config)
        
        # 匹配 items[0].price, items[1].price 等
        strategy0 = builder._find_strategy("items[0].price")
        strategy1 = builder._find_strategy("items[1].price")
        strategy10 = builder._find_strategy("items[10].price")
        
        # 所有索引应该返回同一个策略实例
        assert strategy0 is not None
        assert strategy1 is not None
        assert strategy10 is not None
        assert strategy0 is strategy1 is strategy10  # 同一个实例
    
    def test_no_match(self):
        """无匹配策略"""
        schema = {"type": "object", "properties": {"name": {"type": "string"}}}
        builder = DataBuilder(schema)
        
        assert builder._find_strategy("unknown_field") is None


class TestMatchPath:
    """测试 _match_path() 方法"""
    
    @pytest.fixture
    def builder(self):
        schema = {"type": "object"}
        return DataBuilder(schema)
    
    def test_user_star_pattern(self, builder):
        """测试 user.* 模式"""
        assert builder._match_path("user.name", "user.*")
        assert builder._match_path("user.email", "user.*")
        # 注意：由于 fnmatch 的行为，user.* 会匹配更深层级
        # fnmatch 的 * 会匹配包括 . 在内的所有字符
    
    def test_star_field_pattern(self, builder):
        """测试 *.field 模式"""
        assert builder._match_path("id", "*.id")
        assert builder._match_path("user.id", "*.id")
        assert builder._match_path("order.id", "*.id")
        assert builder._match_path("items[0].id", "*.id")
    
    def test_array_wildcard_pattern(self, builder):
        """测试 [*] 数组通配符"""
        assert builder._match_path("items[0].name", "items[*].name")
        assert builder._match_path("items[1].name", "items[*].name")
        assert builder._match_path("items[10].name", "items[*].name")
        assert not builder._match_path("items.name", "items[*].name")
    
    def test_fnmatch_pattern(self, builder):
        """测试 fnmatch 模式"""
        assert builder._match_path("user_name", "user_*")
        assert builder._match_path("user_email", "user_*")


class TestDataBuilderEdgeCases:
    """测试边界情况"""
    
    def test_empty_schema(self):
        """空 schema"""
        builder = DataBuilder({})
        result = builder.build()
        
        assert isinstance(result, dict)
    
    def test_nested_objects(self):
        """嵌套对象"""
        schema = {
            "type": "object",
            "properties": {
                "user": {
                    "type": "object",
                    "properties": {
                        "profile": {
                            "type": "object",
                            "properties": {
                                "age": {"type": "integer"}
                            }
                        }
                    }
                }
            }
        }
        builder = DataBuilder(schema)
        result = builder.build()
        
        assert "user" in result
        assert "profile" in result["user"]
        assert "age" in result["user"]["profile"]
    
    def test_array_with_items(self):
        """数组类型"""
        schema = {
            "type": "object",
            "properties": {
                "tags": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            }
        }
        builder = DataBuilder(schema)
        result = builder.build()
        
        assert "tags" in result
        assert isinstance(result["tags"], list)
    
    def test_with_post_filters(self):
        """测试后置过滤器"""
        from data_builder import constraint_filter, limit
        
        schema = {"type": "object", "properties": {"x": {"type": "integer"}}}
        config = BuilderConfig(
            count=10,
            post_filters=[
                constraint_filter(lambda r: r.get("x", 0) > 5),
                limit(3)
            ]
        )
        builder = DataBuilder(schema, config)
        
        results = builder.build()
        
        assert len(results) <= 3
        for r in results:
            assert r["x"] > 5
