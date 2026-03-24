"""CombinationMode、CombinationSpec、Constraint 数据类测试"""

import pytest
from data_builder.combinations import CombinationMode, CombinationSpec, Constraint


class TestCombinationMode:
    """测试 CombinationMode 枚举"""
    
    def test_mode_values(self):
        """测试枚举值"""
        assert CombinationMode.RANDOM.value == "random"
        assert CombinationMode.CARTESIAN.value == "cartesian"
        assert CombinationMode.PAIRWISE.value == "pairwise"
        assert CombinationMode.ORTHOGONAL.value == "orthogonal"
        assert CombinationMode.EQUIVALENCE.value == "equivalence"
        assert CombinationMode.BOUNDARY.value == "boundary"
        assert CombinationMode.INVALID.value == "invalid"
    
    def test_mode_count(self):
        """测试枚举数量"""
        assert len(CombinationMode) == 7
    
    def test_mode_from_string(self):
        """从字符串创建枚举"""
        assert CombinationMode("random") == CombinationMode.RANDOM
        assert CombinationMode("cartesian") == CombinationMode.CARTESIAN


class TestConstraint:
    """测试 Constraint 数据类"""
    
    def test_constraint_creation(self):
        """创建约束"""
        def predicate(row):
            return row.get("x", 0) > 0
        
        constraint = Constraint(predicate=predicate, description="x must be positive")
        
        assert constraint.predicate == predicate
        assert constraint.description == "x must be positive"
    
    def test_constraint_default_description(self):
        """默认描述"""
        constraint = Constraint(predicate=lambda r: True)
        
        assert constraint.description == ""
    
    def test_constraint_predicate_execution(self):
        """执行约束谓词"""
        constraint = Constraint(
            predicate=lambda row: row.get("status") == "active",
            description="status must be active"
        )
        
        assert constraint.predicate({"status": "active"})
        assert not constraint.predicate({"status": "inactive"})


class TestCombinationSpec:
    """测试 CombinationSpec 数据类"""
    
    def test_spec_default_values(self):
        """测试默认值"""
        spec = CombinationSpec()
        
        assert spec.mode == CombinationMode.RANDOM
        assert spec.fields is None
        assert spec.scope is None
        assert spec.constraints == []
        assert spec.strength == 2
        assert spec.normal_values is None
    
    def test_spec_with_mode(self):
        """指定模式"""
        spec = CombinationSpec(mode=CombinationMode.CARTESIAN)
        
        assert spec.mode == CombinationMode.CARTESIAN
    
    def test_spec_with_fields(self):
        """指定字段"""
        spec = CombinationSpec(
            mode=CombinationMode.PAIRWISE,
            fields=["status", "role", "type"]
        )
        
        assert spec.fields == ["status", "role", "type"]
    
    def test_spec_with_scope(self):
        """指定 scope"""
        spec = CombinationSpec(
            mode=CombinationMode.CARTESIAN,
            scope="user"
        )
        
        assert spec.scope == "user"
    
    def test_spec_with_constraints(self):
        """指定约束"""
        constraint1 = Constraint(
            predicate=lambda r: r.get("x", 0) > 0,
            description="x > 0"
        )
        constraint2 = Constraint(
            predicate=lambda r: r.get("y", 0) < 10,
            description="y < 10"
        )
        
        spec = CombinationSpec(
            mode=CombinationMode.CARTESIAN,
            constraints=[constraint1, constraint2]
        )
        
        assert len(spec.constraints) == 2
        assert spec.constraints[0] == constraint1
        assert spec.constraints[1] == constraint2
    
    def test_spec_with_strength(self):
        """指定强度"""
        spec = CombinationSpec(
            mode=CombinationMode.ORTHOGONAL,
            strength=3
        )
        
        assert spec.strength == 3
    
    def test_spec_with_normal_values(self):
        """指定正常值"""
        spec = CombinationSpec(
            mode=CombinationMode.INVALID,
            normal_values={"status": "active", "role": "user"}
        )
        
        assert spec.normal_values == {"status": "active", "role": "user"}
    
    def test_spec_full_configuration(self):
        """完整配置"""
        constraint = Constraint(
            predicate=lambda r: r.get("x") is not None,
            description="x required"
        )
        
        spec = CombinationSpec(
            mode=CombinationMode.BOUNDARY,
            fields=["age", "score"],
            scope="user",
            constraints=[constraint],
            strength=2,
            normal_values={"age": 25}
        )
        
        assert spec.mode == CombinationMode.BOUNDARY
        assert spec.fields == ["age", "score"]
        assert spec.scope == "user"
        assert len(spec.constraints) == 1
        assert spec.strength == 2
        assert spec.normal_values == {"age": 25}


class TestCombinationSpecUsage:
    """测试 CombinationSpec 的实际使用"""
    
    def test_pairwise_with_strength(self):
        """成对组合与强度"""
        # PAIRWISE 固定 strength=2
        spec = CombinationSpec(mode=CombinationMode.PAIRWISE)
        
        assert spec.strength == 2
    
    def test_orthogonal_with_custom_strength(self):
        """正交组合与自定义强度"""
        spec = CombinationSpec(
            mode=CombinationMode.ORTHOGONAL,
            strength=3
        )
        
        assert spec.strength == 3
    
    def test_invalid_mode_with_normal_values(self):
        """非法值模式与正常值"""
        spec = CombinationSpec(
            mode=CombinationMode.INVALID,
            fields=["status", "age"],
            normal_values={"status": "active", "age": 30}
        )
        
        assert spec.mode == CombinationMode.INVALID
        assert spec.normal_values is not None
        assert spec.normal_values["status"] == "active"
        assert spec.normal_values["age"] == 30
    
    def test_constraint_filtering(self):
        """约束过滤示例"""
        constraint = Constraint(
            predicate=lambda row: row.get("status") != "inactive",
            description="exclude inactive status"
        )
        
        rows = [
            {"status": "active", "role": "admin"},
            {"status": "inactive", "role": "user"},
            {"status": "active", "role": "user"}
        ]
        
        filtered = [r for r in rows if constraint.predicate(r)]
        
        assert len(filtered) == 2
        assert all(r["status"] != "inactive" for r in filtered)
    
    def test_multiple_constraints(self):
        """多个约束"""
        constraint1 = Constraint(
            predicate=lambda r: r.get("x", 0) > 0
        )
        constraint2 = Constraint(
            predicate=lambda r: r.get("y", 0) < 10
        )
        
        rows = [
            {"x": 5, "y": 5},
            {"x": -1, "y": 5},
            {"x": 5, "y": 15},
            {"x": -1, "y": 15}
        ]
        
        filtered = [
            r for r in rows
            if all(c.predicate(r) for c in [constraint1, constraint2])
        ]
        
        # 只有第一个同时满足两个约束
        assert len(filtered) == 1
        assert filtered[0] == {"x": 5, "y": 5}


class TestCombinationSpecEdgeCases:
    """测试 CombinationSpec 边界情况"""
    
    def test_empty_fields_list(self):
        """空字段列表"""
        spec = CombinationSpec(
            mode=CombinationMode.CARTESIAN,
            fields=[]
        )
        
        assert spec.fields == []
    
    def test_empty_constraints_list(self):
        """空约束列表"""
        spec = CombinationSpec(
            mode=CombinationMode.CARTESIAN,
            constraints=[]
        )
        
        assert spec.constraints == []
    
    def test_empty_normal_values(self):
        """空正常值字典"""
        spec = CombinationSpec(
            mode=CombinationMode.INVALID,
            normal_values={}
        )
        
        assert spec.normal_values == {}
    
    def test_none_values_explicitly_set(self):
        """显式设置为 None"""
        spec = CombinationSpec(
            mode=CombinationMode.RANDOM,
            fields=None,
            scope=None,
            normal_values=None
        )
        
        assert spec.fields is None
        assert spec.scope is None
        assert spec.normal_values is None
    
    def test_large_fields_list(self):
        """大量字段"""
        fields = [f"field_{i}" for i in range(100)]
        spec = CombinationSpec(
            mode=CombinationMode.PAIRWISE,
            fields=fields
        )
        
        assert len(spec.fields) == 100
        assert spec.fields[0] == "field_0"
        assert spec.fields[-1] == "field_99"
    
    def test_large_constraints_list(self):
        """大量约束"""
        constraints = [
            Constraint(predicate=lambda r, i=i: r.get(f"field_{i}") is not None)
            for i in range(10)
        ]
        
        spec = CombinationSpec(
            mode=CombinationMode.CARTESIAN,
            constraints=constraints
        )
        
        assert len(spec.constraints) == 10
    
    def test_nested_scope(self):
        """嵌套 scope"""
        spec = CombinationSpec(
            mode=CombinationMode.CARTESIAN,
            scope="user.profile.settings"
        )
        
        assert spec.scope == "user.profile.settings"
