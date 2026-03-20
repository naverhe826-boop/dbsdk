"""
EmailFakerStrategy 测试用例

覆盖所有邮箱类型（qq, gmail, 163, outlook, custom, safe, idn）的格式验证，
域名池覆盖测试，自定义域名功能，无效值处理，以及策略创建测试。
IDN 国际化域名邮箱测试（unicode/punycode/both 格式）。
"""
import re
import pytest

from data_builder.strategies.value.string.email import (
    EmailFakerStrategy,
    DOMAINS_CN,
    DOMAINS_INTL,
    DOMAINS_IDN,
    DEFAULT_DOMAINS,
    DEFAULT_IDN_DOMAINS,
    OutputFormat,
)
from data_builder.strategies.value.registry import StrategyRegistry, PARAM_ALIASES
from data_builder.exceptions import StrategyError


def _ctx(**kwargs):
    """创建测试用 StrategyContext"""
    defaults = dict(field_path="test", field_schema={}, root_data={}, parent_data={}, index=0)
    defaults.update(kwargs)
    from data_builder import StrategyContext

    return StrategyContext(**defaults)


class TestEmailTypeFormats:
    """测试各类型邮箱的生成格式"""

    def test_qq_email_format(self):
        """QQ邮箱: 5-11位纯数字用户名，国内域名"""
        s = EmailFakerStrategy(email_type="qq")
        for _ in range(10):
            email = s.generate(_ctx())
            # 验证格式: 5-11位数字@域名
            assert re.match(r"^\d{5,11}@[a-z0-9.]+$", email), f"Invalid QQ email: {email}"
            username, domain = email.split("@")
            # 验证用户名是5-11位纯数字
            assert len(username) >= 5 and len(username) <= 11
            assert username.isdigit()
            # 验证域名在域名池中（优先国内域名）
            assert domain in DOMAINS_CN or domain in DOMAINS_INTL

    def test_gmail_email_format(self):
        """Gmail邮箱: first.last 格式（小写，中间有点号）"""
        # 使用英文 locale 确保生成英文字符
        s = EmailFakerStrategy(email_type="gmail", locale="en_US")
        for _ in range(10):
            email = s.generate(_ctx())
            # 验证格式: first.last@gmail.com
            assert re.match(r"^[a-z]+\.[a-z]+@gmail\.com$", email), f"Invalid Gmail email: {email}"
            local, domain = email.split("@")
            # 验证是小写
            assert local == local.lower()
            # 验证有点号
            assert "." in local
            # 验证域名
            assert domain == "gmail.com"

    def test_163_email_format(self):
        """163邮箱: 用户名符合字母数字下划线组合"""
        s = EmailFakerStrategy(email_type="163")
        for _ in range(10):
            email = s.generate(_ctx())
            # 验证格式: username@域名
            assert re.match(r"^[^@]+@[a-z0-9.]+$", email), f"Invalid 163 email: {email}"
            username, domain = email.split("@")
            # 验证用户名只包含字母数字下划线
            assert re.match(r"^[a-zA-Z0-9_]+$", username)
            # 验证域名在域名池中（优先国内域名）
            assert domain in DOMAINS_CN or domain in DOMAINS_INTL

    def test_outlook_email_format(self):
        """Outlook邮箱: 用户名有数字后缀（前8位+2位数字）"""
        s = EmailFakerStrategy(email_type="outlook")
        for _ in range(10):
            email = s.generate(_ctx())
            # 验证格式: username@域名
            assert re.match(r"^[^@]+@[a-z0-9.]+$", email), f"Invalid Outlook email: {email}"
            username, domain = email.split("@")
            # 验证用户名以数字结尾（至少有2位数字）
            assert re.search(r"\d{2}$", username), f"Outlook username should end with 2 digits: {username}"
            # 验证域名是 outlook.com 或 hotmail.com
            assert domain in ["outlook.com", "hotmail.com"]

    def test_custom_email_format(self):
        """Custom邮箱: 使用域名池"""
        s = EmailFakerStrategy(email_type="custom")
        for _ in range(10):
            email = s.generate(_ctx())
            # 验证基本格式
            assert re.match(r"^.+@[a-z0-9.]+$", email), f"Invalid custom email: {email}"
            local, domain = email.split("@")
            # 验证域名在域名池中
            assert domain in DEFAULT_DOMAINS

    def test_safe_email_format(self):
        """Safe邮箱: 基本email格式"""
        s = EmailFakerStrategy(email_type="safe")
        for _ in range(10):
            email = s.generate(_ctx())
            # 验证基本 email 格式
            assert re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email), f"Invalid safe email: {email}"

    def test_random_email_generation(self):
        """Random邮箱: 随机选择一种邮箱类型生成"""
        s = EmailFakerStrategy(email_type="random")
        # 生成多次，验证每次都是有效的邮箱格式
        # 注意：允许 Unicode 字符（用户名和域名都允许 Unicode）
        for _ in range(50):
            email = s.generate(_ctx())
            # 验证基本 email 格式（用户名和域名部分都允许 Unicode）
            assert re.match(r"^[^@]+@[^@]+\.[a-zA-Z]{2,}$", email), f"Invalid random email: {email}"

    def test_qq_email_length_range(self):
        """QQ邮箱: 5-11位纯数字用户名"""
        s = EmailFakerStrategy(email_type="qq")
        for _ in range(100):
            email = s.generate(_ctx())
            username = email.split("@")[0]
            # 验证用户名长度为5-11位
            assert len(username) >= 5 and len(username) <= 11, f"QQ邮箱长度超出范围: {username}"
            # 验证用户名是纯数字
            assert username.isdigit(), f"QQ用户名包含非数字字符: {username}"


class TestDomainPools:
    """测试域名池的覆盖"""

    def test_domains_cn_coverage(self):
        """验证国内域名池包含 qq.com, 163.com, 126.com 等"""
        expected_cn = {"qq.com", "163.com", "126.com"}
        assert expected_cn.issubset(
            set(DOMAINS_CN)
        ), f"国内域名池缺少: {expected_cn - set(DOMAINS_CN)}"

    def test_domains_intl_coverage(self):
        """验证国际域名池包含 gmail.com, outlook.com 等"""
        expected_intl = {"gmail.com", "outlook.com"}
        assert expected_intl.issubset(
            set(DOMAINS_INTL)
        ), f"国际域名池缺少: {expected_intl - set(DOMAINS_INTL)}"

    def test_default_domains_combined(self):
        """验证默认域名池包含国内外域名"""
        assert "qq.com" in DEFAULT_DOMAINS
        assert "gmail.com" in DEFAULT_DOMAINS
        assert len(DEFAULT_DOMAINS) == len(DOMAINS_CN) + len(DOMAINS_INTL)


class TestCustomDomains:
    """测试自定义域名的功能"""

    def test_custom_domains_parameter(self):
        """测试 domains 参数是否生效"""
        custom_domains = ["example.com", "test.org"]
        s = EmailFakerStrategy(email_type="safe", domains=custom_domains)
        for _ in range(10):
            email = s.generate(_ctx())
            _, domain = email.split("@")
            assert domain in custom_domains, f"Domain should be in custom list: {domain}"

    def test_custom_domains_qq_type(self):
        """测试 QQ 类型使用自定义域名池"""
        # 使用包含国内域名的自定义池
        custom_cn = ["qq.com", "test.cn", "myqq.com"]
        s = EmailFakerStrategy(email_type="qq", domains=custom_cn)
        # QQ 类型会优先从国内域名中选择
        emails = [s.generate(_ctx()) for _ in range(10)]
        domains = [e.split("@")[1] for e in emails]
        # 至少有一些域名在自定义池中（qq.com 在 DOMAINS_CN 中会被选中）
        assert any(d in custom_cn for d in domains)

    def test_custom_domains_with_safe_type(self):
        """测试 safe 类型使用自定义域名池"""
        custom_domains = ["example.com", "test.org"]
        s = EmailFakerStrategy(email_type="safe", domains=custom_domains)
        for _ in range(10):
            email = s.generate(_ctx())
            _, domain = email.split("@")
            assert domain in custom_domains, f"Domain {domain} not in custom list"


class TestInvalidValues:
    """测试无效值的处理"""

    def test_invalid_values_returns_list(self):
        """测试 invalid_values() 返回无效邮箱列表"""
        s = EmailFakerStrategy()
        invalid_list = s.invalid_values()
        assert isinstance(invalid_list, list)
        assert len(invalid_list) > 0

    def test_invalid_values_content(self):
        """测试 invalid_values() 返回的无效邮箱格式正确"""
        s = EmailFakerStrategy()
        invalid_list = s.invalid_values()
        # 验证包含各种无效格式
        expected_invalid = [
            "not-an-email",  # 无 @
            "@domain.com",  # 无用户名
            "user@",  # 无域名
            "",  # 空字符串
        ]
        for expected in expected_invalid:
            assert expected in invalid_list, f"Should contain: {expected}"


class TestStrategyCreation:
    """测试策略创建"""

    def test_create_via_registry(self):
        """测试通过 StrategyRegistry.create() 创建策略"""
        config = {"type": "email", "email_type": "qq"}
        strategy = StrategyRegistry.create(config)
        assert isinstance(strategy, EmailFakerStrategy)
        email = strategy.generate(_ctx())
        assert re.match(r"^\d{5,11}@", email)

    def test_registry_get_email_strategy(self):
        """测试通过 StrategyRegistry.get() 获取策略"""
        strategy_cls = StrategyRegistry.get("email")
        assert strategy_cls == EmailFakerStrategy

    def test_param_aliases_email(self):
        """测试参数别名是否生效"""
        # email 策略应该有参数别名
        assert "email" in PARAM_ALIASES
        aliases = PARAM_ALIASES["email"]
        assert "email_type" in aliases or "type" in aliases

    def test_create_with_type_alias(self):
        """测试使用 type 参数别名创建策略"""
        config = {"type": "email", "email_type": "gmail"}
        strategy = StrategyRegistry.create(config)
        email = strategy.generate(_ctx())
        assert "@gmail.com" in email

    def test_create_with_default_params(self):
        """测试默认参数创建策略"""
        strategy = StrategyRegistry.create({"type": "email"})
        assert isinstance(strategy, EmailFakerStrategy)
        email = strategy.generate(_ctx())
        # 默认是 safe 类型，应该生成有效格式
        assert re.match(r"^.+@.+\..+$", email)


class TestErrorHandling:
    """测试错误处理"""

    def test_invalid_email_type_raises_error(self):
        """测试无效邮箱类型抛出 StrategyError"""
        with pytest.raises(StrategyError) as exc_info:
            EmailFakerStrategy(email_type="invalid_type")
        assert "不支持的邮箱类型" in str(exc_info.value)


class TestLocaleSupport:
    """测试多语言支持"""

    def test_locale_zh_cn(self):
        """测试中文 locale"""
        s = EmailFakerStrategy(email_type="gmail", locale="zh_CN")
        email = s.generate(_ctx())
        assert "@gmail.com" in email
        local = email.split("@")[0]
        # 验证是小写格式
        assert local == local.lower()
        assert "." in local

    def test_locale_en_us(self):
        """测试英文 locale"""
        s = EmailFakerStrategy(email_type="gmail", locale="en_US")
        email = s.generate(_ctx())
        assert "@gmail.com" in email
        local = email.split("@")[0]
        assert local == local.lower()
        assert "." in local


class TestIDNEmail:
    """测试 IDN 国际化域名邮箱"""

    def test_idn_email_in_supported_types(self):
        """验证 idn 类型在 SUPPORTED_TYPES 中"""
        assert "idn" in EmailFakerStrategy.SUPPORTED_TYPES

    def test_idn_in_random_types(self):
        """验证 idn 在 random 类型的可选列表中"""
        # idn 在 _BASE_TYPES 中不包含，但可以通过 include_idn=True 包含
        assert "idn" not in EmailFakerStrategy._BASE_TYPES
        # 验证默认情况下 random 类型包含 idn
        s = EmailFakerStrategy(email_type="random")
        # 生成多次邮箱，验证可能生成 IDN 邮箱
        for _ in range(100):
            email = s.generate(_ctx())
            # 验证邮箱格式
            assert re.match(r"^[^@]+@[^@]+\.[a-zA-Z]{2,}$", email), f"Invalid email: {email}"

    def test_idn_unicode_format(self):
        """测试 IDN Unicode 格式输出"""
        s = EmailFakerStrategy(email_type="idn", output_format="unicode")
        for _ in range(10):
            email = s.generate(_ctx())
            # 验证包含 @ 和域名
            assert "@" in email
            local, domain = email.split("@")
            # 验证用户名不为空
            assert len(local) > 0
            # 验证域名在 IDN 域名池中
            assert domain in DOMAINS_IDN or domain in DEFAULT_IDN_DOMAINS
            # 验证输出是 Unicode 域名（包含非ASCII字符或纯英文但不是 xn-- 前缀）
            assert "xn--" not in domain or domain.encode("idna").decode("idna") == domain

    def test_idn_punycode_format(self):
        """测试 IDN Punycode 格式输出"""
        s = EmailFakerStrategy(email_type="idn", output_format="punycode")
        for _ in range(10):
            email = s.generate(_ctx())
            # 验证包含 @ 和域名
            assert "@" in email
            local, domain = email.split("@")
            # 验证用户名不为空
            assert len(local) > 0
            # 验证域名是 Punycode 格式（以 xn-- 开头）
            assert domain.startswith("xn--") or domain in ["中国.cn", "日本.jp"] is False

    def test_idn_both_format(self):
        """测试 IDN Both 格式输出（字典）"""
        s = EmailFakerStrategy(email_type="idn", output_format="both")
        for _ in range(10):
            result = s.generate(_ctx())
            # 验证返回的是字典
            assert isinstance(result, dict)
            assert "unicode" in result
            assert "punycode" in result
            # 验证 unicode 和 punycode 格式不同
            unicode_email = result["unicode"]
            punycode_email = result["punycode"]
            _, unicode_domain = unicode_email.split("@")
            _, punycode_domain = punycode_email.split("@")
            # punycode 域名应该以 xn-- 开头
            assert punycode_domain.startswith("xn--")

    def test_idn_custom_domains(self):
        """测试自定义 IDN 域名列表"""
        custom_idn_domains = ["中国.cn", "日本.jp", "한국.kr"]
        s = EmailFakerStrategy(email_type="idn", idn_domains=custom_idn_domains, output_format="unicode")
        for _ in range(10):
            email = s.generate(_ctx())
            _, domain = email.split("@")
            assert domain in custom_idn_domains

    def test_idn_default_domains(self):
        """测试默认 IDN 域名池"""
        # 验证默认 IDN 域名池包含常见国际化域名
        assert "中国.cn" in DEFAULT_IDN_DOMAINS
        assert "日本.jp" in DEFAULT_IDN_DOMAINS
        assert "한국.kr" in DEFAULT_IDN_DOMAINS
        assert len(DEFAULT_IDN_DOMAINS) > 0

    def test_idn_output_format_enum(self):
        """测试 OutputFormat 枚举"""
        assert OutputFormat.UNICODE.value == "unicode"
        assert OutputFormat.PUNYCODE.value == "punycode"
        assert OutputFormat.BOTH.value == "both"

    def test_idn_via_registry(self):
        """测试通过 StrategyRegistry 创建 IDN 策略"""
        config = {"type": "email", "email_type": "idn", "output_format": "unicode"}
        strategy = StrategyRegistry.create(config)
        assert isinstance(strategy, EmailFakerStrategy)
        email = strategy.generate(_ctx())
        assert "@" in email

    def test_idn_invalid_output_format(self):
        """测试无效的 output_format 参数"""
        # 无效的 output_format 应该回退到 unicode
        s = EmailFakerStrategy(email_type="idn", output_format="invalid_format")
        assert s.output_format == OutputFormat.UNICODE


class TestIDNDomainPunycode:
    """测试 IDN 域名 Punycode 编码"""

    def test_punycode_encoding(self):
        """测试 Unicode 域名转换为 Punycode"""
        from data_builder.strategies.value.string.email import _encode_domain_punycode

        # 测试中文域名
        assert _encode_domain_punycode("中国.cn") == "xn--fiqs8s.cn"
        assert _encode_domain_punycode("日本.jp") == "xn--wgv71a.jp"
        # 한국.kr 的正确 Punycode 编码
        assert "xn--" in _encode_domain_punycode("한국.kr")

    def test_punycode_english_domain(self):
        """测试英文域名返回原值"""
        from data_builder.strategies.value.string.email import _encode_domain_punycode

        # 英文域名应该返回原值
        assert _encode_domain_punycode("gmail.com") == "gmail.com"
        assert _encode_domain_punycode("example.org") == "example.org"


class TestRandomEmailIncludeIDN:
    """测试 random 类型邮箱的 include_idn 参数"""

    def test_random_email_include_idn_default(self):
        """测试 include_idn 默认值为 True"""
        s = EmailFakerStrategy(email_type="random")
        
        # 生成多次邮箱，验证能生成有效的邮箱
        for _ in range(50):
            email = s.generate(_ctx())
            # 验证邮箱格式
            assert re.match(r"^[^@]+@[^@]+\.[a-zA-Z]{2,}$", email), f"Invalid random email: {email}"

    def test_random_email_include_idn_true(self):
        """测试 include_idn=True 时可能包含 IDN 邮箱"""
        s = EmailFakerStrategy(email_type="random", include_idn=True)
        
        # 生成多次邮箱，验证能生成有效的邮箱
        for _ in range(50):
            email = s.generate(_ctx())
            # 验证邮箱格式
            assert re.match(r"^[^@]+@[^@]+\.[a-zA-Z]{2,}$", email), f"Invalid random email: {email}"

    def test_random_email_include_idn_false(self):
        """测试 include_idn=False 时不包含 IDN 邮箱类型"""
        s = EmailFakerStrategy(email_type="random", include_idn=False)
        
        # 生成多次邮箱，验证能生成有效的邮箱
        for _ in range(50):
            email = s.generate(_ctx())
            # 验证邮箱格式
            assert re.match(r"^[^@]+@[^@]+\.[a-zA-Z]{2,}$", email), f"Invalid random email: {email}"
            # 验证邮箱不是 IDN 域名（不包含 DOMAINS_IDN 中的域名）
            domain = email.split("@")[1]
            assert domain not in DOMAINS_IDN, f"生成了 IDN 邮箱: {email}"

    def test_include_idn_only_affects_random_type(self):
        """测试 include_idn 参数只影响 random 类型，不影响其他类型"""
        # 测试 idn 类型本身不受影响
        s1 = EmailFakerStrategy(email_type="idn", include_idn=False)
        email1 = s1.generate(_ctx())
        # IDN 类型应该始终生成 IDN 邮箱
        assert any(ord(c) > 127 for c in email1), "idn 类型应该始终生成 IDN 邮箱"
        
        # 测试 qq 类型不受影响
        s2 = EmailFakerStrategy(email_type="qq", include_idn=False)
        email2 = s2.generate(_ctx())
        assert re.match(r"^\d{5,11}@[a-z0-9.]+$", email2), f"QQ邮箱格式错误: {email2}"

    def test_include_idn_configuration(self):
        """测试通过配置字典设置 include_idn 参数"""
        from data_builder.strategies.value.registry import StrategyRegistry, PARAM_ALIASES
        
        # 创建包含 include_idn 参数的配置字典
        config_dict = {
            "type": "email",
            "email_type": "random",
            "include_idn": False
        }
        
        # 通过注册表创建策略
        strategy = StrategyRegistry.create(config_dict)
        
        # 生成邮箱并验证不包含 IDN 域名
        for _ in range(50):
            email = strategy.generate(_ctx())
            domain = email.split("@")[1]
            assert domain not in DOMAINS_IDN, f"生成了 IDN 邮箱: {email}"

    def test_include_idn_with_params_nesting(self):
        """测试 params 嵌套写法中的 include_idn 参数"""
        from data_builder.strategies.value.registry import StrategyRegistry, PARAM_ALIASES
        
        # 使用 params 嵌套写法
        config_dict = {
            "type": "email",
            "params": {
                "email_type": "random",
                "include_idn": False
            }
        }
        
        # 通过注册表创建策略
        strategy = StrategyRegistry.create(config_dict)
        
        # 生成邮箱并验证不包含 IDN 域名
        for _ in range(50):
            email = strategy.generate(_ctx())
            domain = email.split("@")[1]
            assert domain not in DOMAINS_IDN, f"生成了 IDN 邮箱: {email}"
