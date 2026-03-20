"""测试从字典加载配置"""
import pytest
from data_builder import DataBuilder, BuilderConfig


class TestConfigFromDict:
    """测试 BuilderConfig.from_dict() 方法"""

    def test_load_policies_basic(self):
        """测试加载基本策略配置"""
        config_dict = {
            "policies": [
                {
                    "path": "id",
                    "strategy": {
                        "type": "sequence",
                        "start": 1001,
                        "prefix": "ID-"
                    }
                },
                {
                    "path": "name",
                    "strategy": {
                        "type": "faker",
                        "method": "name"
                    }
                }
            ],
            "count": 2
        }

        config = BuilderConfig.from_dict(config_dict)

        assert len(config.policies) == 2
        assert config.count == 2
        assert config.policies[0].path == "id"
        assert config.policies[1].path == "name"

    def test_load_policies_with_params_nested(self):
        """测试加载使用 params 嵌套格式的配置"""
        config_dict = {
            "policies": [
                {
                    "path": "id",
                    "strategy": {
                        "type": "sequence",
                        "params": {
                            "start": 1001,
                            "prefix": "ORD-"
                        }
                    }
                }
            ]
        }

        config = BuilderConfig.from_dict(config_dict)
        assert len(config.policies) == 1

    def test_load_enum_strategy(self):
        """测试加载枚举策略"""
        config_dict = {
            "policies": [
                {
                    "path": "status",
                    "strategy": {
                        "type": "enum",
                        "values": ["active", "inactive", "pending"]
                    }
                }
            ]
        }

        config = BuilderConfig.from_dict(config_dict)
        assert len(config.policies) == 1
        assert config.policies[0].path == "status"

    def test_load_range_strategy(self):
        """测试加载范围策略"""
        config_dict = {
            "policies": [
                {
                    "path": "amount",
                    "strategy": {
                        "type": "range",
                        "min": 100,
                        "max": 1000
                    }
                }
            ]
        }

        config = BuilderConfig.from_dict(config_dict)
        assert len(config.policies) == 1

    def test_load_global_config(self):
        """测试加载全局配置"""
        config_dict = {
            "strict_mode": True,
            "null_probability": 0.1,
            "count": 5,
            "policies": []
        }

        config = BuilderConfig.from_dict(config_dict)
        assert config.strict_mode is True
        assert config.null_probability == 0.1
        assert config.count == 5

    def test_load_empty_policies(self):
        """测试加载空策略配置"""
        config_dict = {
            "policies": []
        }

        config = BuilderConfig.from_dict(config_dict)
        assert len(config.policies) == 0

    def test_load_with_wildcard_path(self):
        """测试加载通配符路径"""
        config_dict = {
            "policies": [
                {
                    "path": "items[*].id",
                    "strategy": {
                        "type": "sequence",
                        "start": 1
                    }
                }
            ]
        }

        config = BuilderConfig.from_dict(config_dict)
        assert config.policies[0].path == "items[*].id"

    def test_simplified_strategy_format(self):
        """测试简化格式（strategy 直接是字符串）"""
        config_dict = {
            "policies": [
                {
                    "path": "id",
                    "strategy": "sequence",
                    "start": 100
                }
            ]
        }

        config = BuilderConfig.from_dict(config_dict)
        assert len(config.policies) == 1
