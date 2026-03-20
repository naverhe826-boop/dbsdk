"""网络策略单元测试"""

import pytest
import ipaddress
from data_builder.strategies.value.network import (
    IPv4Strategy, IPv6Strategy, DomainStrategy, HostnameStrategy,
    URLStrategy, MACStrategy, CIDRStrategy, IPRangeStrategy
)
from data_builder.strategies.basic import StrategyContext


class TestIPv4Strategy:
    """IPv4Strategy 测试"""

    def test_generate_any(self):
        """测试生成任意 IPv4 地址"""
        strategy = IPv4Strategy(ip_class="any")
        ctx = StrategyContext(field_path="test", field_schema={})
        
        for _ in range(10):
            result = strategy.generate(ctx)
            # 验证是有效的 IPv4 地址
            ip = ipaddress.IPv4Address(result)
            assert ip.version == 4

    def test_generate_private(self):
        """测试生成私有地址"""
        strategy = IPv4Strategy(ip_class="private")
        ctx = StrategyContext(field_path="test", field_schema={})
        
        for _ in range(10):
            result = strategy.generate(ctx)
            ip = ipaddress.IPv4Address(result)
            # 验证是私有地址
            assert ip.is_private

    def test_generate_loopback(self):
        """测试生成回环地址"""
        strategy = IPv4Strategy(ip_class="loopback")
        ctx = StrategyContext(field_path="test", field_schema={})
        
        for _ in range(10):
            result = strategy.generate(ctx)
            ip = ipaddress.IPv4Address(result)
            assert ip.is_loopback

    def test_generate_multicast(self):
        """测试生成组播地址"""
        strategy = IPv4Strategy(ip_class="multicast")
        ctx = StrategyContext(field_path="test", field_schema={})
        
        for _ in range(10):
            result = strategy.generate(ctx)
            ip = ipaddress.IPv4Address(result)
            assert ip.is_multicast

    def test_generate_in_subnet(self):
        """测试在指定网段内生成"""
        strategy = IPv4Strategy(subnet="192.168.1.0/24")
        ctx = StrategyContext(field_path="test", field_schema={})
        
        network = ipaddress.IPv4Network("192.168.1.0/24")
        
        for _ in range(10):
            result = strategy.generate(ctx)
            ip = ipaddress.IPv4Address(result)
            assert ip in network

    def test_format_binary(self):
        """测试二进制格式输出"""
        strategy = IPv4Strategy(format="binary")
        ctx = StrategyContext(field_path="test", field_schema={})
        
        result = strategy.generate(ctx)
        # 验证格式
        parts = result.split(".")
        assert len(parts) == 4
        for part in parts:
            assert len(part) == 8
            assert all(c in "01" for c in part)

    def test_format_cidr(self):
        """测试 CIDR 格式输出"""
        strategy = IPv4Strategy(format="cidr", prefix_length=24)
        ctx = StrategyContext(field_path="test", field_schema={})
        
        result = strategy.generate(ctx)
        assert "/24" in result

    def test_boundary_values(self):
        """测试边界值"""
        strategy = IPv4Strategy()
        boundaries = strategy.boundary_values()
        
        assert "0.0.0.0" in boundaries
        assert "127.0.0.1" in boundaries
        assert "255.255.255.255" in boundaries

    def test_invalid_values(self):
        """测试非法值"""
        strategy = IPv4Strategy()
        invalid = strategy.invalid_values()
        
        assert "256.0.0.0" in invalid
        assert "abc.def.ghi.jkl" in invalid
        assert "" in invalid
        assert None in invalid

    def test_invalid_ip_class(self):
        """测试无效地址类别"""
        with pytest.raises(Exception):
            IPv4Strategy(ip_class="invalid")


class TestIPv6Strategy:
    """IPv6Strategy 测试"""

    def test_generate_global(self):
        """测试生成全局单播地址"""
        strategy = IPv6Strategy(address_type="global")
        ctx = StrategyContext(field_path="test", field_schema={})
        
        for _ in range(10):
            result = strategy.generate(ctx)
            ip = ipaddress.IPv6Address(result)
            assert not ip.is_private or ip.is_global

    def test_generate_link_local(self):
        """测试生成链路本地地址"""
        strategy = IPv6Strategy(address_type="link_local")
        ctx = StrategyContext(field_path="test", field_schema={})
        
        for _ in range(10):
            result = strategy.generate(ctx)
            ip = ipaddress.IPv6Address(result)
            assert ip.is_link_local

    def test_generate_loopback(self):
        """测试生成回环地址"""
        strategy = IPv6Strategy(address_type="loopback")
        ctx = StrategyContext(field_path="test", field_schema={})
        
        result = strategy.generate(ctx)
        assert result == "::1"

    def test_generate_unspecified(self):
        """测试生成未指定地址"""
        strategy = IPv6Strategy(address_type="unspecified")
        ctx = StrategyContext(field_path="test", field_schema={})
        
        result = strategy.generate(ctx)
        assert result == "::"

    def test_format_full(self):
        """测试完整格式输出"""
        strategy = IPv6Strategy(format="full")
        ctx = StrategyContext(field_path="test", field_schema={})
        
        result = strategy.generate(ctx)
        # 完整格式应有 8 组，每组 4 字符
        parts = result.split(":")
        assert len(parts) == 8
        for part in parts:
            assert len(part) == 4

    def test_format_compressed(self):
        """测试压缩格式输出"""
        strategy = IPv6Strategy(format="compressed")
        ctx = StrategyContext(field_path="test", field_schema={})
        
        result = strategy.generate(ctx)
        # 验证是有效的 IPv6 地址
        ip = ipaddress.IPv6Address(result)
        assert ip.version == 6

    def test_ipv4_mapped(self):
        """测试 IPv4 映射地址"""
        strategy = IPv6Strategy(address_type="ipv4_mapped")
        ctx = StrategyContext(field_path="test", field_schema={})
        
        result = strategy.generate(ctx)
        assert result.startswith("::ffff:")


class TestDomainStrategy:
    """DomainStrategy 测试"""

    def test_generate_basic(self):
        """测试生成基本域名"""
        strategy = DomainStrategy()
        ctx = StrategyContext(field_path="test", field_schema={})
        
        for _ in range(10):
            result = strategy.generate(ctx)
            assert "." in result
            assert len(result) >= 3

    def test_generate_with_tld(self):
        """测试指定 TLD"""
        strategy = DomainStrategy(tld="com")
        ctx = StrategyContext(field_path="test", field_schema={})
        
        for _ in range(10):
            result = strategy.generate(ctx)
            assert result.endswith(".com")

    def test_generate_with_prefix(self):
        """测试添加前缀"""
        strategy = DomainStrategy(prefix="test-")
        ctx = StrategyContext(field_path="test", field_schema={})
        
        for _ in range(10):
            result = strategy.generate(ctx)
            # 第一个标签应以 test- 开头
            first_label = result.split(".")[0]
            assert first_label.startswith("test-")

    def test_generate_reserved_tld(self):
        """测试保留 TLD"""
        strategy = DomainStrategy(use_reserved_tld=True)
        ctx = StrategyContext(field_path="test", field_schema={})
        
        found_reserved = False
        for _ in range(20):
            result = strategy.generate(ctx)
            tld = result.split(".")[-1]
            if tld in ["test", "example", "invalid", "localhost"]:
                found_reserved = True
                break
        assert found_reserved

    def test_generate_idn(self):
        """测试 IDN 域名"""
        strategy = DomainStrategy(idn=True)
        ctx = StrategyContext(field_path="test", field_schema={})
        
        result = strategy.generate(ctx)
        # IDN 域名可能包含非 ASCII 字符
        assert isinstance(result, str)

    def test_generate_idn_punycode(self):
        """测试 IDN Punycode 输出"""
        strategy = DomainStrategy(idn=True, output_format="punycode")
        ctx = StrategyContext(field_path="test", field_schema={})
        
        result = strategy.generate(ctx)
        # Punycode 应以 xn-- 开头
        assert "xn--" in result


class TestURLStrategy:
    """URLStrategy 测试"""

    def test_generate_absolute(self):
        """测试生成绝对 URL"""
        strategy = URLStrategy(url_type="absolute")
        ctx = StrategyContext(field_path="test", field_schema={})
        
        for _ in range(10):
            result = strategy.generate(ctx)
            assert "://" in result

    def test_generate_relative(self):
        """测试生成相对 URL"""
        strategy = URLStrategy(url_type="relative")
        ctx = StrategyContext(field_path="test", field_schema={})
        
        for _ in range(10):
            result = strategy.generate(ctx)
            assert "://" not in result
            assert result.startswith("/")

    def test_generate_with_query(self):
        """测试带查询参数"""
        strategy = URLStrategy(include_query=True)
        ctx = StrategyContext(field_path="test", field_schema={})
        
        for _ in range(10):
            result = strategy.generate(ctx)
            if "?" in result:
                assert "=" in result

    def test_generate_with_fragment(self):
        """测试带片段"""
        strategy = URLStrategy(include_fragment=True)
        ctx = StrategyContext(field_path="test", field_schema={})
        
        found_fragment = False
        for _ in range(20):
            result = strategy.generate(ctx)
            if "#" in result:
                found_fragment = True
                break
        assert found_fragment

    def test_specified_scheme(self):
        """测试指定 scheme"""
        strategy = URLStrategy(scheme="https")
        ctx = StrategyContext(field_path="test", field_schema={})
        
        for _ in range(10):
            result = strategy.generate(ctx)
            assert result.startswith("https://")


class TestMACStrategy:
    """MACStrategy 测试"""

    def test_generate_basic(self):
        """测试生成基本 MAC 地址"""
        strategy = MACStrategy()
        ctx = StrategyContext(field_path="test", field_schema={})
        
        for _ in range(10):
            result = strategy.generate(ctx)
            # 验证格式：6 组十六进制，用冒号分隔
            parts = result.split(":")
            assert len(parts) == 6
            for part in parts:
                assert len(part) == 2
                int(part, 16)  # 验证是有效十六进制

    def test_format_hyphen(self):
        """测试连字符格式"""
        strategy = MACStrategy(format="hyphen")
        ctx = StrategyContext(field_path="test", field_schema={})
        
        result = strategy.generate(ctx)
        assert "-" in result
        assert ":" not in result

    def test_format_dot(self):
        """测试点分格式"""
        strategy = MACStrategy(format="dot")
        ctx = StrategyContext(field_path="test", field_schema={})
        
        result = strategy.generate(ctx)
        parts = result.split(".")
        assert len(parts) == 3

    def test_format_no_separator(self):
        """测试无分隔符格式"""
        strategy = MACStrategy(format="no_separator")
        ctx = StrategyContext(field_path="test", field_schema={})
        
        result = strategy.generate(ctx)
        assert len(result) == 12
        assert ":" not in result
        assert "-" not in result

    def test_unicast_address(self):
        """测试单播地址"""
        strategy = MACStrategy(address_type="unicast")
        ctx = StrategyContext(field_path="test", field_schema={})
        
        for _ in range(10):
            result = strategy.generate(ctx)
            parts = result.split(":")
            first_octet = int(parts[0], 16)
            # 单播地址：最低位为 0
            assert (first_octet & 0x01) == 0

    def test_multicast_address(self):
        """测试组播地址"""
        strategy = MACStrategy(address_type="multicast")
        ctx = StrategyContext(field_path="test", field_schema={})
        
        for _ in range(10):
            result = strategy.generate(ctx)
            parts = result.split(":")
            first_octet = int(parts[0], 16)
            # 组播地址：最低位为 1
            assert (first_octet & 0x01) == 1

    def test_broadcast_address(self):
        """测试广播地址"""
        strategy = MACStrategy(address_type="broadcast")
        ctx = StrategyContext(field_path="test", field_schema={})
        
        result = strategy.generate(ctx)
        assert result.lower() == "ff:ff:ff:ff:ff:ff"

    def test_uppercase(self):
        """测试大写输出"""
        strategy = MACStrategy(uppercase=True)
        ctx = StrategyContext(field_path="test", field_schema={})
        
        result = strategy.generate(ctx)
        assert result.isupper()


class TestCIDRStrategy:
    """CIDRStrategy 测试"""

    def test_generate_ipv4(self):
        """测试生成 IPv4 CIDR"""
        strategy = CIDRStrategy(version=4)
        ctx = StrategyContext(field_path="test", field_schema={})
        
        for _ in range(10):
            result = strategy.generate(ctx)
            network = ipaddress.IPv4Network(result, strict=False)
            assert network.version == 4

    def test_generate_ipv6(self):
        """测试生成 IPv6 CIDR"""
        strategy = CIDRStrategy(version=6)
        ctx = StrategyContext(field_path="test", field_schema={})
        
        for _ in range(10):
            result = strategy.generate(ctx)
            network = ipaddress.IPv6Network(result, strict=False)
            assert network.version == 6

    def test_specified_prefix_length(self):
        """测试指定前缀长度"""
        strategy = CIDRStrategy(prefix_length=24)
        ctx = StrategyContext(field_path="test", field_schema={})
        
        for _ in range(10):
            result = strategy.generate(ctx)
            assert "/24" in result


class TestIPRangeStrategy:
    """IPRangeStrategy 测试"""

    def test_generate_ipv4_range(self):
        """测试生成 IPv4 范围"""
        strategy = IPRangeStrategy(version=4)
        ctx = StrategyContext(field_path="test", field_schema={})
        
        for _ in range(10):
            result = strategy.generate(ctx)
            assert "-" in result
            start, end = result.split("-")
            start_ip = ipaddress.IPv4Address(start)
            end_ip = ipaddress.IPv4Address(end)
            assert start_ip <= end_ip

    def test_generate_ipv6_range(self):
        """测试生成 IPv6 范围"""
        strategy = IPRangeStrategy(version=6)
        ctx = StrategyContext(field_path="test", field_schema={})
        
        for _ in range(10):
            result = strategy.generate(ctx)
            assert "-" in result
            start, end = result.split("-")
            start_ip = ipaddress.IPv6Address(start)
            end_ip = ipaddress.IPv6Address(end)
            assert start_ip <= end_ip

    def test_custom_separator(self):
        """测试自定义分隔符"""
        strategy = IPRangeStrategy(separator=" to ")
        ctx = StrategyContext(field_path="test", field_schema={})
        
        result = strategy.generate(ctx)
        assert " to " in result

    def test_specified_range(self):
        """测试指定范围"""
        strategy = IPRangeStrategy(start_ip="192.168.1.1", end_ip="192.168.1.100")
        ctx = StrategyContext(field_path="test", field_schema={})
        
        result = strategy.generate(ctx)
        assert result == "192.168.1.1-192.168.1.100"


class TestHostnameStrategy:
    """HostnameStrategy 测试"""

    def test_generate_basic(self):
        """测试生成基本主机名"""
        strategy = HostnameStrategy()
        ctx = StrategyContext(field_path="test", field_schema={})
        
        for _ in range(10):
            result = strategy.generate(ctx)
            assert isinstance(result, str)
            assert len(result) >= 1
            assert "." not in result  # 默认不包含 TLD

    def test_generate_with_tld(self):
        """测试包含 TLD 的主机名"""
        strategy = HostnameStrategy(include_tld=True)
        ctx = StrategyContext(field_path="test", field_schema={})
        
        for _ in range(10):
            result = strategy.generate(ctx)
            assert "." in result

    def test_generate_with_specific_tld(self):
        """测试指定 TLD"""
        strategy = HostnameStrategy(include_tld=True, tld="com")
        ctx = StrategyContext(field_path="test", field_schema={})
        
        for _ in range(10):
            result = strategy.generate(ctx)
            assert result.endswith(".com")

    def test_generate_multi_labels(self):
        """测试多标签主机名"""
        strategy = HostnameStrategy(labels=3)
        ctx = StrategyContext(field_path="test", field_schema={})
        
        for _ in range(10):
            result = strategy.generate(ctx)
            # 3 个标签应该有 2 个点号
            assert result.count(".") == 2

    def test_generate_idn(self):
        """测试 IDN 主机名"""
        strategy = HostnameStrategy(idn=True)
        ctx = StrategyContext(field_path="test", field_schema={})
        
        result = strategy.generate(ctx)
        assert isinstance(result, str)
        # IDN 主机名可能包含非 ASCII 字符

    def test_generate_idn_punycode(self):
        """测试 IDN Punycode 输出"""
        strategy = HostnameStrategy(idn=True, output_format="punycode")
        ctx = StrategyContext(field_path="test", field_schema={})
        
        result = strategy.generate(ctx)
        # Punycode 应包含 xn--
        assert "xn--" in result

    def test_generate_idn_both(self):
        """测试 IDN 双格式输出"""
        strategy = HostnameStrategy(idn=True, output_format="both")
        ctx = StrategyContext(field_path="test", field_schema={})
        
        result = strategy.generate(ctx)
        assert isinstance(result, dict)
        assert "unicode" in result
        assert "punycode" in result

    def test_boundary_values(self):
        """测试边界值"""
        strategy = HostnameStrategy()
        boundaries = strategy.boundary_values()
        
        assert "a" in boundaries
        assert "localhost" in boundaries
        assert "中国.中国" in boundaries

    def test_invalid_values(self):
        """测试非法值"""
        strategy = HostnameStrategy()
        invalid = strategy.invalid_values()
        
        assert "-hostname" in invalid
        assert "hostname-" in invalid
        assert "" in invalid
        assert None in invalid
        assert "host name" in invalid  # 包含空格
