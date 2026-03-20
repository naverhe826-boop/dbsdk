"""InvalidDataGenerator 测试

测试覆盖：
- 预设模板
- 自定义模板
- 支持的数据类型
- 批量生成
"""

import pytest

from data_builder import InvalidDataGenerator


class TestInvalidDataGenerator:
    """非法数据生成器测试"""
    
    def test_get_all_types(self):
        """测试获取所有支持的数据类型"""
        types = InvalidDataGenerator.get_all_types()
        
        assert types is not None
        assert len(types) > 0
        
        # 验证包含基础数据类型
        assert "email" in types
        assert "password" in types
        assert "ipv4" in types
        assert "string" in types
        
        # 验证包含新增的账户类数据类型
        assert "id_card" in types
        assert "bank_card" in types
        assert "phone" in types
        assert "username" in types
    
    def test_generate_email(self):
        """测试生成邮箱非法值"""
        invalid_list = InvalidDataGenerator.generate("email", count=5)
        
        assert len(invalid_list) == 5
        
        # 验证非法值列表包含典型的邮箱格式错误
        # 合法邮箱格式: local-part@domain.tld
        # 非法值包括：空字符串、缺@符号、多个@、包含空格、域名格式错误等
        # 只要生成的值不符合RFC 5322标准即可（这里做简单验证）
        for value in invalid_list:
            # 检查类型
            assert isinstance(value, (str, type(None)))
            
            # 空字符串或None是合法的非法值
            if not value:
                continue
                
            # 非邮箱格式的值（至少满足以下条件之一）
            is_invalid = (
                value == "" or                     # 空字符串
                "@" not in value or                # 缺少@符号
                value.count("@") != 1 or           # 多个@符号
                value.startswith("@") or           # 缺少本地部分
                value.endswith("@") or             # 缺少域名
                " " in value or                    # 包含空格
                "." not in value.split("@")[-1] or # 域名缺少点（无顶级域名）
                value.split("@")[-1].startswith(".") or # 域名以点开头
                value.split("@")[-1].endswith(".") # 域名以点结尾
            )
            assert is_invalid, f"{value!r} 看起来像合法邮箱"
    
    def test_generate_id_card(self):
        """测试生成身份证号非法值"""
        invalid_list = InvalidDataGenerator.generate("id_card", count=5)
        
        assert len(invalid_list) == 5
        
        # 验证包含不同类型的错误
        has_wrong_length = any(
            isinstance(v, str) and len(v) != 18 
            for v in invalid_list
        )
        has_type_error = any(
            isinstance(v, int) or v is None 
            for v in invalid_list
        )
        
        assert has_wrong_length or has_type_error
    
    def test_generate_bank_card(self):
        """测试生成银行卡号非法值"""
        invalid_list = InvalidDataGenerator.generate("bank_card", count=5)
        
        assert len(invalid_list) == 5
        
        # 验证包含不同类型的错误
        has_wrong_length = any(
            isinstance(v, str) and len(v) != 16 
            for v in invalid_list
        )
        has_type_error = any(
            isinstance(v, int) or v is None 
            for v in invalid_list
        )
        
        assert has_wrong_length or has_type_error
    
    def test_generate_phone(self):
        """测试生成手机号非法值"""
        invalid_list = InvalidDataGenerator.generate("phone", count=5)
        
        assert len(invalid_list) == 5
        
        # 验证包含不同类型的错误
        has_wrong_length = any(
            isinstance(v, str) and len(v) != 11 
            for v in invalid_list
        )
        has_type_error = any(
            isinstance(v, int) or v is None 
            for v in invalid_list
        )
        
        assert has_wrong_length or has_type_error
    
    def test_generate_username(self):
        """测试生成用户名非法值"""
        invalid_list = InvalidDataGenerator.generate("username", count=5)
        
        assert len(invalid_list) == 5
        
        # 验证包含不同类型的错误
        has_wrong_length = any(
            isinstance(v, str) and (len(v) < 6 or len(v) > 20)
            for v in invalid_list
        )
        has_type_error = any(
            isinstance(v, int) or v is None 
            for v in invalid_list
        )
        has_reserved_word = any(
            isinstance(v, str) and v.lower() in ["admin", "root", "system"]
            for v in invalid_list
        )
        
        assert has_wrong_length or has_type_error or has_reserved_word
    
    def test_generate_ipv4(self):
        """测试生成IPv4非法值"""
        invalid_list = InvalidDataGenerator.generate("ipv4", count=5)
        
        assert len(invalid_list) == 5
    
    def test_generate_string(self):
        """测试生成字符串非法值"""
        invalid_list = InvalidDataGenerator.generate("string", count=5)
        
        # string模板只有4个元素，返回值不超过请求数量
        assert len(invalid_list) <= 5
        assert len(invalid_list) > 0
    
    def test_generate_with_count_greater_than_template(self):
        """测试请求数量大于模板数量"""
        # 当请求数量大于模板数量时，应返回全部模板
        invalid_list = InvalidDataGenerator.generate("email", count=100)
        
        assert len(invalid_list) <= 100
    
    def test_get_template(self):
        """测试获取预设模板"""
        template = InvalidDataGenerator.get_template("email")
        
        assert template is not None
        assert len(template) > 0
        
        # 验证模板是不可变的（返回副本）
        template.append("new_invalid_value")
        template2 = InvalidDataGenerator.get_template("email")
        
        assert "new_invalid_value" not in template2
    
    def test_add_template_new_type(self):
        """测试添加新数据类型的模板"""
        # 添加自定义数据类型
        custom_type = "custom_field"
        custom_invalid = ["invalid1", "invalid2", "invalid3"]
        
        InvalidDataGenerator.add_template(custom_type, custom_invalid)
        
        # 验证可以生成
        result = InvalidDataGenerator.generate(custom_type, count=2)
        
        assert len(result) == 2
        assert all(v in custom_invalid for v in result)
    
    def test_add_template_existing_type(self):
        """测试扩展现有数据类型的模板"""
        # 获取原有模板
        original_template = InvalidDataGenerator.get_template("email")
        original_count = len(original_template)
        
        # 添加新模板
        new_invalid = ["new_invalid_email_1", "new_invalid_email_2"]
        InvalidDataGenerator.add_template("email", new_invalid)
        
        # 验证模板已扩展
        updated_template = InvalidDataGenerator.get_template("email")
        
        # 验证新值已添加
        assert len(updated_template) >= original_count
        assert all(v in updated_template for v in new_invalid)
    
    def test_generate_unsupported_type(self):
        """测试生成不支持的数据类型"""
        with pytest.raises(ValueError):
            InvalidDataGenerator.generate("unsupported_type", count=5)
    
    def test_get_template_unsupported_type(self):
        """测试获取不支持的数据类型的模板"""
        with pytest.raises(ValueError):
            InvalidDataGenerator.get_template("unsupported_type")
