"""测试参数别名映射功能"""
import pytest
from data_builder import DataBuilder, BuilderConfig


class TestParamAliases:
    """测试参数别名映射"""

    def test_enum_values_alias(self):
        """测试 enum 的 values -> choices 别名"""
        config_dict = {
            "policies": [
                {
                    "path": "status",
                    "strategy": {
                        "type": "enum",
                        "values": ["active", "inactive"]  # 使用 values 而不是 choices
                    }
                }
            ]
        }

        config = BuilderConfig.from_dict(config_dict)
        assert len(config.policies) == 1

    def test_range_min_max_alias(self):
        """测试 range 的 min/max 别名"""
        config_dict = {
            "policies": [
                {
                    "path": "amount",
                    "strategy": {
                        "type": "range",
                        "min": 100,  # 映射到 min_val
                        "max": 1000  # 映射到 max_val
                    }
                }
            ]
        }

        config = BuilderConfig.from_dict(config_dict)
        assert len(config.policies) == 1

    def test_array_count_alias(self):
        """测试 array_count 的 count 别名"""
        schema = {
            "type": "object",
            "properties": {
                "items": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            }
        }

        config_dict = {
            "policies": [
                {
                    "path": "items",
                    "strategy": {
                        "type": "array_count",
                        "count": 5  # 使用 count 映射到 source
                    }
                }
            ]
        }

        config = BuilderConfig.from_dict(config_dict)
        builder = DataBuilder(schema, config)
        results = builder.build(count=5)
        assert len(results[0]["items"]) == 5

    def test_property_selection_alias(self):
        """测试 property_selection 的 properties 别名"""
        schema = {
            "type": "object",
            "properties": {
                "profile": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "age": {"type": "integer"},
                        "email": {"type": "string"}
                    }
                }
            }
        }

        config_dict = {
            "policies": [
                {
                    "path": "profile",
                    "strategy": {
                        "type": "property_selection",
                        "properties": ["name", "age"]  # 映射到 source
                    }
                },
                {
                    "path": "profile.name",
                    "strategy": {
                        "type": "fixed",
                        "value": "test"
                    }
                }
            ]
        }

        config = BuilderConfig.from_dict(config_dict)
        builder = DataBuilder(schema, config)
        results = builder.build(count=3)
        # 验证属性选择工作正常
        for r in results:
            assert "name" in r["profile"]
            assert "age" in r["profile"]

    def test_property_count_alias(self):
        """测试 property_count 的 count 别名"""
        schema = {
            "type": "object",
            "properties": {
                "profile": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "age": {"type": "integer"},
                        "email": {"type": "string"},
                        "phone": {"type": "string"}
                    }
                }
            }
        }

        config_dict = {
            "policies": [
                {
                    "path": "profile",
                    "strategy": {
                        "type": "property_count",
                        "count": 2  # 使用 count 映射到 source
                    }
                },
                {
                    "path": "profile.name",
                    "strategy": {
                        "type": "fixed",
                        "value": "test"
                    }
                }
            ]
        }

        config = BuilderConfig.from_dict(config_dict)
        builder = DataBuilder(schema, config)
        results = builder.build(count=5)

        # 验证属性数量限制
        for r in results:
            assert len(r["profile"]) <= 3  # name + 随机1-2个

    def test_ref_strategy(self):
        """测试 ref 策略"""
        schema = {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "ref_id": {"type": "string"}
            }
        }

        config_dict = {
            "policies": [
                {
                    "path": "id",
                    "strategy": {
                        "type": "sequence",
                        "start": 1
                    }
                },
                {
                    "path": "ref_id",
                    "strategy": {
                        "type": "ref",
                        "ref_path": "id"
                    }
                }
            ]
        }

        config = BuilderConfig.from_dict(config_dict)
        builder = DataBuilder(schema, config)
        results = builder.build(count=3)

        for r in results:
            assert r["ref_id"] == r["id"]

    def test_datetime_strategy(self):
        """测试 datetime 策略"""
        config_dict = {
            "policies": [
                {
                    "path": "created_at",
                    "strategy": {
                        "type": "datetime",
                        "format": "%Y-%m-%d"
                    }
                }
            ]
        }

        config = BuilderConfig.from_dict(config_dict)
        assert len(config.policies) == 1
