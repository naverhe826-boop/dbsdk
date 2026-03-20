"""测试环境变量插值功能"""
import os
import pytest
from data_builder import DataBuilder, BuilderConfig


class TestEnvVars:
    """测试环境变量插值"""

    def test_env_var_simple(self):
        """测试简单环境变量替换"""
        os.environ["TEST_START"] = "999"

        config_dict = {
            "policies": [
                {
                    "path": "id",
                    "strategy": {
                        "type": "sequence",
                        "start": "${TEST_START}",
                        "prefix": "T-"
                    }
                }
            ]
        }

        try:
            config = BuilderConfig.from_dict(config_dict)
            assert len(config.policies) == 1
        finally:
            os.environ.pop("TEST_START", None)

    def test_env_var_with_default(self):
        """测试带默认值的环境变量"""
        # 确保环境变量不存在
        os.environ.pop("NONEXISTENT_VAR", None)

        config_dict = {
            "policies": [
                {
                    "path": "id",
                    "strategy": {
                        "type": "sequence",
                        "start": "${NONEXISTENT_VAR:-1000}",
                        "prefix": "D-"
                    }
                }
            ]
        }

        config = BuilderConfig.from_dict(config_dict)
        assert len(config.policies) == 1

    def test_env_var_in_nested_params(self):
        """测试嵌套参数中的环境变量"""
        os.environ["TEST_PREFIX"] = "PREF-"

        config_dict = {
            "policies": [
                {
                    "path": "id",
                    "strategy": {
                        "type": "sequence",
                        "params": {
                            "start": 1,
                            "prefix": "${TEST_PREFIX}"
                        }
                    }
                }
            ]
        }

        try:
            config = BuilderConfig.from_dict(config_dict)
            assert len(config.policies) == 1
        finally:
            os.environ.pop("TEST_PREFIX", None)

    def test_multiple_env_vars(self):
        """测试多个环境变量"""
        os.environ["VAR_A"] = "100"
        os.environ["VAR_B"] = "B-"

        config_dict = {
            "policies": [
                {
                    "path": "id",
                    "strategy": {
                        "type": "sequence",
                        "start": "${VAR_A}",
                        "prefix": "${VAR_B}"
                    }
                }
            ]
        }

        try:
            config = BuilderConfig.from_dict(config_dict)
            assert len(config.policies) == 1
        finally:
            os.environ.pop("VAR_A", None)
            os.environ.pop("VAR_B", None)

    def test_env_var_empty_default(self):
        """测试空默认值"""
        os.environ.pop("EMPTY_VAR", None)

        config_dict = {
            "policies": [
                {
                    "path": "id",
                    "strategy": {
                        "type": "sequence",
                        "start": "${EMPTY_VAR:-}",
                        "prefix": "E-"
                    }
                }
            ]
        }

        config = BuilderConfig.from_dict(config_dict)
        assert len(config.policies) == 1

    def test_env_var_not_replaced_in_non_string(self):
        """测试非字符串值不进行环境变量替换"""
        os.environ["TEST_NUM"] = "999"

        config_dict = {
            "policies": [
                {
                    "path": "id",
                    "strategy": {
                        "type": "sequence",
                        "start": 100,  # 整数不应该被替换
                        "prefix": "T-"
                    }
                }
            ]
        }

        try:
            config = BuilderConfig.from_dict(config_dict)
            assert len(config.policies) == 1
        finally:
            os.environ.pop("TEST_NUM", None)
