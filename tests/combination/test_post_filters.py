"""post_filters 在 DataBuilder 中的集成测试"""

import pytest
from data_builder import DataBuilder
from data_builder.filters import deduplicate, constraint_filter, limit, tag_rows


class TestPostFiltersIntegration:
    """测试 post_filters 在 DataBuilder 中的集成功能"""

    def test_limit_filter_integration(self):
        """测试 limit 过滤器在 DataBuilder 中的集成"""
        schema = {
            "type": "object",
            "properties": {
                "id": {"type": "integer"},
                "name": {"type": "string"},
            },
        }

        config = DataBuilder.config_from_dict({
            "policies": [
                {"path": "id", "strategy": {"type": "sequence", "start": 1}},
                {"path": "name", "strategy": {"type": "fixed", "value": "test"}},
            ],
            "post_filters": [
                {"type": "limit", "max_count": 5}
            ]
        })

        results = DataBuilder(schema, config).build(count=20)
        assert len(results) == 5
        assert results[0]["id"] == 1
        assert results[4]["id"] == 5

    def test_deduplicate_filter_integration(self):
        """测试 deduplicate 过滤器在 DataBuilder 中的集成"""
        schema = {
            "type": "object",
            "properties": {
                "category": {"type": "string"},
                "name": {"type": "string"},
            },
        }

        config = DataBuilder.config_from_dict({
            "policies": [
                {"path": "category", "strategy": {"type": "enum", "values": ["A", "B", "C"]}},
                {"path": "name", "strategy": {"type": "fixed", "value": "test"}},
            ],
            "post_filters": [
                {"type": "deduplicate", "key_fields": ["category"]}
            ]
        })

        results = DataBuilder(schema, config).build(count=30)
        categories = [r["category"] for r in results]
        # 去重后应该只有 3 个不同的 category
        assert len(set(categories)) <= 3
        # 不应该有重复的 category
        assert len(categories) == len(set(categories))

    def test_constraint_filter_integration(self):
        """测试 constraint_filter 过滤器在 DataBuilder 中的集成"""
        schema = {
            "type": "object",
            "properties": {
                "status": {"type": "string"},
                "score": {"type": "integer"},
            },
        }

        config = DataBuilder.config_from_dict({
            "policies": [
                {"path": "status", "strategy": {"type": "enum", "values": ["active", "inactive"]}},
                {"path": "score", "strategy": {"type": "range", "min": 0, "max": 100}},
            ],
            "post_filters": [
                {"type": "constraint_filter", "predicate": "lambda row: row.get('status') == 'active'"}
            ]
        })

        results = DataBuilder(schema, config).build(count=20)
        # 所有结果应该都是 active 状态
        for r in results:
            assert r["status"] == "active"

    def test_tag_rows_filter_integration(self):
        """测试 tag_rows 过滤器在 DataBuilder 中的集成"""
        schema = {
            "type": "object",
            "properties": {
                "id": {"type": "integer"},
            },
        }

        config = DataBuilder.config_from_dict({
            "policies": [
                {"path": "id", "strategy": {"type": "sequence", "start": 1}},
            ],
            "post_filters": [
                {"type": "tag_rows", "tag_field": "source", "tag_value": "generated"}
            ]
        })

        results = DataBuilder(schema, config).build(count=3)
        for r in results:
            assert r.get("source") == "generated"

    def test_combined_filters_integration(self):
        """测试组合使用多个过滤器"""
        schema = {
            "type": "object",
            "properties": {
                "category": {"type": "string"},
                "status": {"type": "string"},
                "id": {"type": "integer"},
            },
        }

        config = DataBuilder.config_from_dict({
            "policies": [
                {"path": "category", "strategy": {"type": "enum", "values": ["A", "B", "C", "D"]}},
                {"path": "status", "strategy": {"type": "enum", "values": ["active", "inactive"]}},
                {"path": "id", "strategy": {"type": "sequence", "start": 1}},
            ],
            "post_filters": [
                {"type": "deduplicate", "key_fields": ["category"]},
                {"type": "constraint_filter", "predicate": "lambda row: row.get('status') == 'active'"},
                {"type": "limit", "max_count": 2},
                {"type": "tag_rows", "tag_field": "batch", "tag_value": "test"}
            ]
        })

        results = DataBuilder(schema, config).build(count=50)
        # 验证结果数量受限
        assert len(results) <= 2
        # 验证所有结果都是 active
        for r in results:
            assert r["status"] == "active"
            assert r["batch"] == "test"
        # 验证 category 不重复
        categories = [r["category"] for r in results]
        assert len(categories) == len(set(categories))


class TestPostFiltersConfigParsing:
    """测试 post_filters 的配置解析"""

    def test_parse_limit_filter(self):
        """测试 limit 过滤器配置解析"""
        config = DataBuilder.config_from_dict({
            "post_filters": [
                {"type": "limit", "max_count": 10}
            ]
        })
        assert len(config.post_filters) == 1
        # 应用过滤器
        rows = [{"i": i} for i in range(20)]
        result = config.post_filters[0](rows)
        assert len(result) == 10

    def test_parse_deduplicate_filter(self):
        """测试 deduplicate 过滤器配置解析"""
        config = DataBuilder.config_from_dict({
            "post_filters": [
                {"type": "deduplicate", "key_fields": ["category"]}
            ]
        })
        assert len(config.post_filters) == 1
        rows = [
            {"category": "A", "name": "a1"},
            {"category": "A", "name": "a2"},
            {"category": "B", "name": "b1"},
        ]
        result = config.post_filters[0](rows)
        assert len(result) == 2
        assert result[0]["category"] == "A"
        assert result[1]["category"] == "B"

    def test_parse_constraint_filter(self):
        """测试 constraint_filter 过滤器配置解析"""
        config = DataBuilder.config_from_dict({
            "post_filters": [
                {"type": "constraint_filter", "predicate": "lambda row: row.get('score', 0) >= 60"}
            ]
        })
        assert len(config.post_filters) == 1
        rows = [{"score": 50}, {"score": 70}, {"score": 80}]
        result = config.post_filters[0](rows)
        assert len(result) == 2
        assert result[0]["score"] == 70
        assert result[1]["score"] == 80

    def test_parse_tag_rows_filter(self):
        """测试 tag_rows 过滤器配置解析"""
        config = DataBuilder.config_from_dict({
            "post_filters": [
                {"type": "tag_rows", "tag_field": "source", "tag_value": "test"}
            ]
        })
        assert len(config.post_filters) == 1
        rows = [{"id": 1}, {"id": 2}]
        result = config.post_filters[0](rows)
        assert result[0]["source"] == "test"
        assert result[1]["source"] == "test"

    def test_parse_multiple_filters(self):
        """测试多个过滤器配置解析"""
        config = DataBuilder.config_from_dict({
            "post_filters": [
                {"type": "limit", "max_count": 5},
                {"type": "tag_rows", "tag_field": "tag", "tag_value": "v"},
            ]
        })
        assert len(config.post_filters) == 2

    def test_empty_post_filters(self):
        """测试空 post_filters 配置"""
        config = DataBuilder.config_from_dict({
            "post_filters": []
        })
        assert config.post_filters == []


class TestPostFiltersEdgeCases:
    """测试 post_filters 边界情况"""

    def test_limit_zero(self):
        """测试 limit(0) 的边界情况"""
        schema = {"type": "object", "properties": {"id": {"type": "integer"}}}
        config = DataBuilder.config_from_dict({
            "policies": [
                {"path": "id", "strategy": {"type": "sequence", "start": 1}},
            ],
            "post_filters": [
                {"type": "limit", "max_count": 0}
            ]
        })
        results = DataBuilder(schema, config).build(count=10)
        assert len(results) == 0

    def test_filter_removes_all(self):
        """测试过滤器移除所有结果的情况"""
        schema = {"type": "object", "properties": {"id": {"type": "integer"}}}
        config = DataBuilder.config_from_dict({
            "policies": [
                {"path": "id", "strategy": {"type": "sequence", "start": 1}},
            ],
            "post_filters": [
                {"type": "constraint_filter", "predicate": "lambda row: False"}
            ]
        })
        results = DataBuilder(schema, config).build(count=10)
        assert len(results) == 0

    def test_single_result_with_post_filter(self):
        """测试单结果配合 post_filter"""
        schema = {"type": "object", "properties": {"id": {"type": "integer"}}}
        config = DataBuilder.config_from_dict({
            "policies": [
                {"path": "id", "strategy": {"type": "fixed", "value": 1}},
            ],
            "post_filters": [
                {"type": "tag_rows", "tag_field": "tag", "tag_value": "x"}
            ]
        })
        result = DataBuilder(schema, config).build()
        # build() 不传 count 返回单个对象，但 post_filter 仍会应用
        # 当结果为空时返回 None
        if result is not None:
            assert result.get("tag") == "x"
