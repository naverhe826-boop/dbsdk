"""测试 combinations 和 post_filters 配置加载"""
import pytest
from data_builder import DataBuilder, BuilderConfig


class TestCombinationsFromConfig:
    """测试从配置加载 combinations"""

    def test_cartesian_combination(self):
        """测试笛卡尔积组合"""
        schema = {
            "type": "object",
            "properties": {
                "status": {"type": "string"},
                "type": {"type": "string"},
                "id": {"type": "string"}
            }
        }

        config_dict = {
            "policies": [
                {"path": "id", "strategy": {"type": "fixed", "value": "1"}},
                {
                    "path": "status",
                    "strategy": {"type": "enum", "values": ["a", "b"]}
                },
                {
                    "path": "type",
                    "strategy": {"type": "enum", "values": ["x", "y"]}
                }
            ],
            "combinations": [
                {"mode": "cartesian", "fields": ["status", "type"]}
            ]
        }

        config = BuilderConfig.from_dict(config_dict)
        builder = DataBuilder(schema, config)
        results = builder.build()

        # 笛卡尔积：2 × 2 = 4 条
        assert len(results) == 4

    def test_combinations_mode_strings(self):
        """测试各种组合模式"""
        modes = ["cartesian", "pairwise", "random"]

        for mode in modes:
            config_dict = {
                "policies": [
                    {"path": "id", "strategy": {"type": "fixed", "value": "1"}},
                    {
                        "path": "status",
                        "strategy": {"type": "enum", "values": ["a", "b", "c"]}
                    }
                ],
                "combinations": [
                    {"mode": mode, "fields": ["status"]}
                ]
            }

            config = BuilderConfig.from_dict(config_dict)
            assert len(config.combinations) == 1
            assert config.combinations[0].mode.value == mode

    def test_combinations_with_scope(self):
        """测试带 scope 的组合"""
        config_dict = {
            "policies": [
                {"path": "id", "strategy": {"type": "fixed", "value": "1"}},
                {"path": "status", "strategy": {"type": "enum", "values": ["a", "b"]}}
            ],
            "combinations": [
                {"mode": "cartesian", "fields": ["status"], "scope": None}
            ]
        }

        config = BuilderConfig.from_dict(config_dict)
        assert config.combinations[0].scope is None


class TestPostFiltersFromConfig:
    """测试从配置加载 post_filters"""

    def test_limit_filter(self):
        """测试 limit 过滤器"""
        schema = {
            "type": "object",
            "properties": {
                "id": {"type": "string"}
            }
        }

        config_dict = {
            "policies": [
                {"path": "id", "strategy": {"type": "sequence", "start": 1}}
            ],
            "post_filters": [
                {"type": "limit", "max_count": 5}
            ]
        }

        config = BuilderConfig.from_dict(config_dict)
        builder = DataBuilder(schema, config)
        results = builder.build(count=100)

        assert len(results) <= 5

    def test_tag_rows_filter(self):
        """测试 tag_rows 过滤器"""
        schema = {
            "type": "object",
            "properties": {
                "id": {"type": "string"}
            }
        }

        config_dict = {
            "policies": [
                {"path": "id", "strategy": {"type": "fixed", "value": "1"}}
            ],
            "post_filters": [
                {
                    "type": "tag_rows",
                    "tag_field": "_tag",
                    "tag_value": "test_tag"
                }
            ]
        }

        config = BuilderConfig.from_dict(config_dict)
        builder = DataBuilder(schema, config)
        results = builder.build(count=3)

        for r in results:
            assert r.get("_tag") == "test_tag"

    def test_deduplicate_filter(self):
        """测试 deduplicate 过滤器"""
        schema = {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "name": {"type": "string"}
            }
        }

        config_dict = {
            "policies": [
                {"path": "id", "strategy": {"type": "fixed", "value": "1"}},
                {"path": "name", "strategy": {"type": "enum", "values": ["a", "b", "a"]}}
            ],
            "post_filters": [
                {"type": "deduplicate", "key_fields": ["name"]}
            ]
        }

        config = BuilderConfig.from_dict(config_dict)
        builder = DataBuilder(schema, config)
        results = builder.build(count=10)

    def test_multiple_filters(self):
        """测试多个过滤器组合"""
        schema = {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "name": {"type": "string"}
            }
        }

        config_dict = {
            "policies": [
                {"path": "id", "strategy": {"type": "sequence", "start": 1}},
                {"path": "name", "strategy": {"type": "fixed", "value": "test"}}
            ],
            "post_filters": [
                {"type": "limit", "max_count": 3},
                {"type": "tag_rows", "tag_field": "source", "tag_value": "config"}
            ]
        }

        config = BuilderConfig.from_dict(config_dict)
        builder = DataBuilder(schema, config)
        results = builder.build(count=100)

        assert len(results) <= 3
        for r in results:
            assert r.get("source") == "config"


class TestFullConfigIntegration:
    """完整配置集成测试"""

    def test_full_config(self):
        """测试完整配置加载"""
        schema = {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "status": {"type": "string"},
                "amount": {"type": "integer"},
                "created_at": {"type": "string"}
            }
        }

        config_dict = {
            "strict_mode": False,
            "null_probability": 0.0,
            "count": 5,
            "policies": [
                {
                    "path": "id",
                    "strategy": {"type": "sequence", "start": 1001, "prefix": "ORD-"}
                },
                {
                    "path": "status",
                    "strategy": {"type": "enum", "values": ["pending", "paid"]}
                },
                {
                    "path": "amount",
                    "strategy": {"type": "range", "min": 100, "max": 1000}
                },
                {
                    "path": "created_at",
                    "strategy": {"type": "datetime", "format": "%Y-%m-%d"}
                }
            ],
            "combinations": [
                {"mode": "cartesian", "fields": ["status"]}
            ],
            "post_filters": [
                {"type": "limit", "max_count": 10}
            ]
        }

        config = BuilderConfig.from_dict(config_dict)

        # 验证配置正确加载
        assert config.strict_mode is False
        assert config.null_probability == 0.0
        assert config.count == 5
        assert len(config.policies) == 4
        assert len(config.combinations) == 1
        assert len(config.post_filters) >= 1

        # 验证实际生成
        builder = DataBuilder(schema, config)
        results = builder.build()
        assert len(results) <= 10

        for r in results:
            assert "id" in r
            assert "status" in r
            assert "amount" in r
            assert "created_at" in r
