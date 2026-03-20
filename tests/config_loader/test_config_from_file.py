"""测试从文件加载配置"""
import os
import json
import pytest
import tempfile
from data_builder import DataBuilder, BuilderConfig


class TestConfigFromFile:
    """测试 BuilderConfig.from_file() 方法"""

    def test_load_json_file(self):
        """测试从 JSON 文件加载"""
        config_json = {
            "policies": [
                {
                    "path": "id",
                    "strategy": {
                        "type": "sequence",
                        "start": 1001
                    }
                }
            ],
            "count": 2
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_json, f)
            temp_path = f.name

        try:
            config = BuilderConfig.from_file(temp_path)
            assert len(config.policies) == 1
            assert config.count == 2
        finally:
            os.unlink(temp_path)

    def test_load_yaml_file(self):
        """测试从 YAML 文件加载（如果 pyyaml 已安装）"""
        pytest.importorskip("yaml")

        config_yaml = """
policies:
  - path: "id"
    strategy:
      type: sequence
      start: 1001

count: 3
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_yaml)
            temp_path = f.name

        try:
            config = BuilderConfig.from_file(temp_path)
            assert len(config.policies) == 1
            assert config.count == 3
        finally:
            os.unlink(temp_path)

    def test_load_yml_file(self):
        """测试从 yml 文件加载"""
        pytest.importorskip("yaml")

        config_yaml = """
policies:
  - path: "name"
    strategy:
      type: faker
      method: name
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            f.write(config_yaml)
            temp_path = f.name

        try:
            config = BuilderConfig.from_file(temp_path)
            assert len(config.policies) == 1
            assert config.policies[0].path == "name"
        finally:
            os.unlink(temp_path)

    def test_file_not_found(self):
        """测试文件不存在时抛出异常"""
        with pytest.raises(FileNotFoundError):
            BuilderConfig.from_file("/nonexistent/path/config.json")

    def test_with_combinations(self):
        """测试加载包含 combinations 的配置"""
        config_json = {
            "policies": [
                {"path": "status", "strategy": {"type": "enum", "values": ["a", "b"]}},
                {"path": "type", "strategy": {"type": "enum", "values": ["x", "y"]}}
            ],
            "combinations": [
                {"mode": "cartesian", "fields": ["status", "type"]}
            ]
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_json, f)
            temp_path = f.name

        try:
            config = BuilderConfig.from_file(temp_path)
            assert len(config.combinations) == 1
            assert config.combinations[0].mode.value == "cartesian"
        finally:
            os.unlink(temp_path)

    def test_with_post_filters(self):
        """测试加载包含 post_filters 的配置"""
        config_json = {
            "policies": [
                {"path": "id", "strategy": {"type": "sequence", "start": 1}}
            ],
            "post_filters": [
                {"type": "limit", "max_count": 10}
            ]
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_json, f)
            temp_path = f.name

        try:
            config = BuilderConfig.from_file(temp_path)
            assert len(config.post_filters) >= 1
        finally:
            os.unlink(temp_path)
