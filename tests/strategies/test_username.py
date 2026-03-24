"""用户名策略测试

测试覆盖：
- 合法值生成
- 长度范围
- 字符集
- 保留字过滤
- 边界值
- 等价类
- 非法值
- 参数校验
"""

import pytest

from data_builder import UsernameStrategy, StrategyContext
from data_builder.exceptions import StrategyError


class TestUsernameStrategy:
    """用户名策略测试"""
    
    def test_basic_generation(self):
        """测试基本生成功能"""
        strategy = UsernameStrategy()
        
        for _ in range(10):
            username = strategy.generate(StrategyContext(field_path="", field_schema={}))
            
            # 验证长度
            assert 6 <= len(username) <= 20
            
            # 验证不以特殊字符开头
            assert username[0].isalnum()
    
    def test_length_range(self):
        """测试长度范围"""
        min_length = 8
        max_length = 12
        strategy = UsernameStrategy(min_length=min_length, max_length=max_length)
        
        for _ in range(20):
            username = strategy.generate(StrategyContext(field_path="", field_schema={}))
            
            assert min_length <= len(username) <= max_length
    
    def test_charset_alphanumeric(self):
        """测试纯字母数字字符集"""
        strategy = UsernameStrategy(charset="alphanumeric")
        
        for _ in range(10):
            username = strategy.generate(StrategyContext(field_path="", field_schema={}))
            
            # 验证只包含字母和数字
            assert username.isalnum()
    
    def test_charset_underscore(self):
        """测试字母数字+下划线字符集"""
        strategy = UsernameStrategy(charset="alphanumeric_underscore")
        
        for _ in range(10):
            username = strategy.generate(StrategyContext(field_path="", field_schema={}))
            
            # 验证只包含字母、数字和下划线
            for char in username:
                assert char.isalnum() or char == "_"
    
    def test_charset_dot(self):
        """测试字母数字+点号字符集"""
        strategy = UsernameStrategy(charset="alphanumeric_dot")
        
        for _ in range(10):
            username = strategy.generate(StrategyContext(field_path="", field_schema={}))
            
            # 验证只包含字母、数字和点号
            for char in username:
                assert char.isalnum() or char == "."
    
    def test_charset_dash(self):
        """测试字母数字+连字符字符集"""
        strategy = UsernameStrategy(charset="alphanumeric_dash")
        
        for _ in range(10):
            username = strategy.generate(StrategyContext(field_path="", field_schema={}))
            
            # 验证只包含字母、数字和连字符
            for char in username:
                assert char.isalnum() or char == "-"
    
    def test_no_uppercase(self):
        """测试禁用大写字母"""
        strategy = UsernameStrategy(allow_uppercase=False)
        
        for _ in range(10):
            username = strategy.generate(StrategyContext(field_path="", field_schema={}))
            
            # 验证不包含大写字母
            assert username == username.lower()
    
    def test_reserved_words_filter(self):
        """测试保留字过滤"""
        strategy = UsernameStrategy()
        reserved_words = strategy.reserved_words
        
        # 默认保留字应包含常见的系统用户名
        assert "admin" in reserved_words
        assert "root" in reserved_words
        
        # 生成的用户名不应是保留字
        for _ in range(100):
            username = strategy.generate(StrategyContext(field_path="", field_schema={}))
            
            assert username.lower() not in {w.lower() for w in reserved_words}
    
    def test_custom_reserved_words(self):
        """测试自定义保留字"""
        custom_words = ["test", "demo", "example"]
        strategy = UsernameStrategy(reserved_words=custom_words)
        
        # 生成的用户名不应是自定义保留字
        for _ in range(50):
            username = strategy.generate(StrategyContext(field_path="", field_schema={}))
            
            assert username.lower() not in {w.lower() for w in custom_words}
    
    def test_boundary_values(self):
        """测试边界值"""
        strategy = UsernameStrategy()
        boundaries = strategy.boundary_values()
        
        assert boundaries is not None
        assert len(boundaries) >= 2
        
        # 验证边界值符合长度要求
        for username in boundaries:
            assert 6 <= len(username) <= 20
    
    def test_equivalence_classes(self):
        """测试等价类"""
        strategy = UsernameStrategy()
        classes = strategy.equivalence_classes()
        
        assert classes is not None
        assert len(classes) >= 3
        
        # 验证每个等价类都有样本
        for cls in classes:
            assert len(cls) >= 1
    
    def test_invalid_values(self):
        """测试非法值"""
        strategy = UsernameStrategy()
        invalid = strategy.invalid_values()
        
        assert invalid is not None
        assert len(invalid) >= 5
        
        # 验证非法值列表包含不同类型的错误
        error_types = {
            "空字符串": False,
            "过短": False,
            "过长": False,
            "非法字符": False,
            "保留字": False,
            "类型错误": False,
        }
        
        for value in invalid:
            if isinstance(value, int) or value is None:
                error_types["类型错误"] = True
            elif isinstance(value, str):
                if value == "":
                    error_types["空字符串"] = True
                elif len(value) < 6:
                    error_types["过短"] = True
                elif len(value) > 20:
                    error_types["过长"] = True
                elif not value.isalnum() and not any(c in value for c in "._-"):
                    error_types["非法字符"] = True
                elif value.lower() in ["admin", "root", "system"]:
                    error_types["保留字"] = True
        
        # 至少包含4种错误类型
        assert sum(error_types.values()) >= 4
    
    def test_invalid_length_range(self):
        """测试无效长度范围"""
        # 长度超出范围
        with pytest.raises(StrategyError):
            UsernameStrategy(min_length=0)
        
        with pytest.raises(StrategyError):
            UsernameStrategy(max_length=100)
        
        # min_length > max_length
        with pytest.raises(StrategyError):
            UsernameStrategy(min_length=20, max_length=10)
    
    def test_invalid_charset(self):
        """测试无效字符集参数"""
        with pytest.raises(StrategyError):
            UsernameStrategy(charset="unknown_charset")
    
    def test_first_char_not_special(self):
        """测试首字符不是特殊字符"""
        for charset in ["alphanumeric_underscore", "alphanumeric_dot", "alphanumeric_dash"]:
            strategy = UsernameStrategy(charset=charset)

            for _ in range(10):
                username = strategy.generate(StrategyContext(field_path="", field_schema={}))

                # 首字符应该是字母或数字
                assert username[0].isalnum()

    # ========== 新增：姓名和昵称生成测试 ==========

    def test_chinese_name_generation(self):
        """测试中文姓名生成"""
        strategy = UsernameStrategy(style="chinese_name")

        for _ in range(20):
            name = strategy.generate(StrategyContext(field_path="", field_schema={}))

            # 验证是中文字符（常见姓名长度2-4字）
            assert 2 <= len(name) <= 4
            # 验证包含中文字符
            assert any('\u4e00' <= c <= '\u9fff' for c in name)

    def test_chinese_name_with_gender(self):
        """测试中文姓名性别过滤"""
        # 男性姓名
        strategy_male = UsernameStrategy(style="chinese_name", gender="male")
        for _ in range(10):
            name = strategy_male.generate(StrategyContext(field_path="", field_schema={}))
            assert 2 <= len(name) <= 4

        # 女性姓名
        strategy_female = UsernameStrategy(style="chinese_name", gender="female")
        for _ in range(10):
            name = strategy_female.generate(StrategyContext(field_path="", field_schema={}))
            assert 2 <= len(name) <= 4

    def test_english_name_generation(self):
        """测试英文姓名生成"""
        strategy = UsernameStrategy(style="english_name")

        for _ in range(20):
            name = strategy.generate(StrategyContext(field_path="", field_schema={}))

            # 验证包含空格（名 姓格式）
            assert " " in name
            # 验证首字母大写
            parts = name.split()
            assert all(part[0].isupper() for part in parts)

    def test_english_name_with_gender(self):
        """测试英文姓名性别过滤"""
        # 男性姓名
        strategy_male = UsernameStrategy(style="english_name", gender="male")
        for _ in range(10):
            name = strategy_male.generate(StrategyContext(field_path="", field_schema={}))
            assert " " in name

        # 女性姓名
        strategy_female = UsernameStrategy(style="english_name", gender="female")
        for _ in range(10):
            name = strategy_female.generate(StrategyContext(field_path="", field_schema={}))
            assert " " in name

    def test_nickname_generation(self):
        """测试昵称生成（无后缀）"""
        strategy = UsernameStrategy(style="nickname", suffix_type="none")

        for _ in range(20):
            name = strategy.generate(StrategyContext(field_path="", field_schema={}))

            # 验证包含中文（小/老/阿前缀）
            assert any('\u4e00' <= c <= '\u9fff' for c in name)

    def test_nickname_with_number_suffix(self):
        """测试昵称数字后缀"""
        strategy = UsernameStrategy(style="nickname", suffix_type="number")

        for _ in range(10):
            name = strategy.generate(StrategyContext(field_path="", field_schema={}))
            # 应包含中文和可选数字后缀
            assert any('\u4e00' <= c <= '\u9fff' for c in name)

    def test_nickname_with_char_suffix(self):
        """测试昵称字母后缀"""
        strategy = UsernameStrategy(style="nickname", suffix_type="char")

        for _ in range(10):
            name = strategy.generate(StrategyContext(field_path="", field_schema={}))
            # 应包含中文和可选字母后缀
            assert any('\u4e00' <= c <= '\u9fff' for c in name)

    def test_invalid_style_parameter(self):
        """测试无效 style 参数"""
        with pytest.raises(StrategyError):
            UsernameStrategy(style="invalid_style")

    def test_invalid_gender_parameter(self):
        """测试无效 gender 参数"""
        with pytest.raises(StrategyError):
            UsernameStrategy(style="chinese_name", gender="unknown")

    def test_invalid_suffix_type_parameter(self):
        """测试无效 suffix_type 参数"""
        with pytest.raises(StrategyError):
            UsernameStrategy(style="nickname", suffix_type="invalid")
