#!/usr/bin/env python3
"""
网络数据生成策略使用示例

本示例展示如何使用 dbsdk 框架生成各类网络数据：
1. 新增的网络策略：IPv4、IPv6、域名、主机名、URL、MAC、CIDR、IP范围
2. 复用已有策略：端口、网络服务地址、网络接口名称

本示例使用字典配置方式，不直接依赖 BuilderConfig 和策略类
"""

from data_builder import DataBuilder


def example_ipv4():
    """IPv4 地址生成示例 - 使用字典配置方式"""
    print("=" * 50)
    print("IPv4 地址生成示例 - 字典配置方式")
    print("=" * 50)

    schema = {
        "type": "object",
        "properties": {
            "any_ip": {"type": "string"},
            "private_ip": {"type": "string"},
            "loopback_ip": {"type": "string"},
            "multicast_ip": {"type": "string"},
            "subnet_ip": {"type": "string"},
            "binary_ip": {"type": "string"},
            "cidr_ip": {"type": "string"},
        }
    }

    config_dict = {
        "policies": [
            {"path": "any_ip", "strategy": {"type": "ipv4", "ip_class": "any"}},
            {"path": "private_ip", "strategy": {"type": "ipv4", "ip_class": "private"}},
            {"path": "loopback_ip", "strategy": {"type": "ipv4", "ip_class": "loopback"}},
            {"path": "multicast_ip", "strategy": {"type": "ipv4", "ip_class": "multicast"}},
            {"path": "subnet_ip", "strategy": {"type": "ipv4", "subnet": "10.0.0.0/24"}},
            {"path": "binary_ip", "strategy": {"type": "ipv4", "format": "binary"}},
            {"path": "cidr_ip", "strategy": {"type": "ipv4", "format": "cidr", "prefix_length": 24}},
        ]
    }

    config = DataBuilder.config_from_dict(config_dict)
    builder = DataBuilder(schema, config)
    result = builder.build()

    for key, value in result.items():
        print(f"  {key}: {value}")
    print()


def example_ipv6():
    """IPv6 地址生成示例 - 使用字典配置方式"""
    print("=" * 50)
    print("IPv6 地址生成示例 - 字典配置方式")
    print("=" * 50)

    schema = {
        "type": "object",
        "properties": {
            "global_ip": {"type": "string"},
            "link_local_ip": {"type": "string"},
            "unique_local_ip": {"type": "string"},
            "loopback_ip": {"type": "string"},
            "ipv4_mapped_ip": {"type": "string"},
            "full_format": {"type": "string"},
        }
    }

    config_dict = {
        "policies": [
            {"path": "global_ip", "strategy": {"type": "ipv6", "address_type": "global"}},
            {"path": "link_local_ip", "strategy": {"type": "ipv6", "address_type": "link_local"}},
            {"path": "unique_local_ip", "strategy": {"type": "ipv6", "address_type": "unique_local"}},
            {"path": "loopback_ip", "strategy": {"type": "ipv6", "address_type": "loopback"}},
            {"path": "ipv4_mapped_ip", "strategy": {"type": "ipv6", "address_type": "ipv4_mapped"}},
            {"path": "full_format", "strategy": {"type": "ipv6", "format": "full"}},
        ]
    }

    config = DataBuilder.config_from_dict(config_dict)
    builder = DataBuilder(schema, config)
    result = builder.build()

    for key, value in result.items():
        print(f"  {key}: {value}")
    print()


def example_domain():
    """域名生成示例 - 使用字典配置方式"""
    print("=" * 50)
    print("域名生成示例 - 字典配置方式")
    print("=" * 50)

    schema = {
        "type": "object",
        "properties": {
            "basic_domain": {"type": "string"},
            "com_domain": {"type": "string"},
            "test_domain": {"type": "string"},
            "prefixed_domain": {"type": "string"},
            "idn_domain": {"type": "string"},
            "idn_punycode": {"type": "string"},
        }
    }

    config_dict = {
        "policies": [
            {"path": "basic_domain", "strategy": {"type": "domain"}},
            {"path": "com_domain", "strategy": {"type": "domain", "tld": "com"}},
            {"path": "test_domain", "strategy": {"type": "domain", "use_reserved_tld": True}},
            {"path": "prefixed_domain", "strategy": {"type": "domain", "prefix": "api-", "tld": "io"}},
            {"path": "idn_domain", "strategy": {"type": "domain", "idn": True, "output_format": "unicode"}},
            {"path": "idn_punycode", "strategy": {"type": "domain", "idn": True, "output_format": "punycode"}},
        ]
    }

    config = DataBuilder.config_from_dict(config_dict)
    builder = DataBuilder(schema, config)
    result = builder.build()

    for key, value in result.items():
        print(f"  {key}: {value}")
    print()


def example_hostname():
    """主机名生成示例 - 使用字典配置方式"""
    print("=" * 50)
    print("主机名生成示例 - 字典配置方式")
    print("=" * 50)

    schema = {
        "type": "object",
        "properties": {
            "basic_hostname": {"type": "string"},
            "fqdn_hostname": {"type": "string"},
            "com_hostname": {"type": "string"},
            "multi_label_hostname": {"type": "string"},
            "idn_hostname": {"type": "string"},
            "idn_punycode": {"type": "string"},
        }
    }

    config_dict = {
        "policies": [
            # 基本主机名（无 TLD）
            {"path": "basic_hostname", "strategy": {"type": "hostname"}},
            # 完全限定域名（包含 TLD）
            {"path": "fqdn_hostname", "strategy": {"type": "hostname", "include_tld": True}},
            # 指定 TLD 的主机名
            {"path": "com_hostname", "strategy": {"type": "hostname", "include_tld": True, "tld": "com"}},
            # 多标签主机名（如 db-master-01.local）
            {"path": "multi_label_hostname", "strategy": {"type": "hostname", "labels": 2, "include_tld": True, "tld": "local"}},
            # IDN 国际化主机名（Unicode 格式）
            {"path": "idn_hostname", "strategy": {"type": "hostname", "idn": True, "output_format": "unicode"}},
            # IDN 主机名（Punycode 格式）
            {"path": "idn_punycode", "strategy": {"type": "hostname", "idn": True, "output_format": "punycode"}},
        ]
    }

    config = DataBuilder.config_from_dict(config_dict)
    builder = DataBuilder(schema, config)
    result = builder.build()

    for key, value in result.items():
        print(f"  {key}: {value}")
    print()


def example_url():
    """URL 生成示例 - 使用字典配置方式"""
    print("=" * 50)
    print("URL 生成示例 - 字典配置方式")
    print("=" * 50)

    schema = {
        "type": "object",
        "properties": {
            "http_url": {"type": "string"},
            "https_url": {"type": "string"},
            "url_with_query": {"type": "string"},
            "url_with_fragment": {"type": "string"},
            "relative_url": {"type": "string"},
        }
    }

    config_dict = {
        "policies": [
            {"path": "http_url", "strategy": {"type": "url", "scheme": "http"}},
            {"path": "https_url", "strategy": {"type": "url", "scheme": "https"}},
            {"path": "url_with_query", "strategy": {"type": "url", "include_query": True}},
            {"path": "url_with_fragment", "strategy": {"type": "url", "include_fragment": True}},
            {"path": "relative_url", "strategy": {"type": "url", "url_type": "relative"}},
        ]
    }

    config = DataBuilder.config_from_dict(config_dict)
    builder = DataBuilder(schema, config)
    result = builder.build()

    for key, value in result.items():
        print(f"  {key}: {value}")
    print()


def example_iri():
    """IRI 生成示例 - 使用字典配置方式

    IRI (Internationalized Resource Identifier) 是 RFC 3987 定义的国际化资源标识符，
    允许在主机名、路径、查询参数中使用 Unicode 字符。
    """
    print("=" * 50)
    print("IRI 生成示例 - 字典配置方式")
    print("=" * 50)

    schema = {
        "type": "object",
        "properties": {
            "iri_unicode": {"type": "string"},
            "iri_punycode": {"type": "string"},
            "iri_with_query": {"type": "string"},
            "iri_reference": {"type": "string"},
        }
    }

    config_dict = {
        "policies": [
            # IRI（Unicode 格式输出）
            {"path": "iri_unicode", "strategy": {"type": "url", "iri_mode": True, "output_format": "unicode"}},
            # IRI（Punycode 格式输出）
            {"path": "iri_punycode", "strategy": {"type": "url", "iri_mode": True, "output_format": "punycode"}},
            # IRI 含查询参数
            {"path": "iri_with_query", "strategy": {"type": "url", "iri_mode": True, "include_query": True}},
            # IRI reference（相对 IRI）
            {"path": "iri_reference", "strategy": {"type": "url", "iri_mode": True, "url_type": "relative"}},
        ]
    }

    config = DataBuilder.config_from_dict(config_dict)
    builder = DataBuilder(schema, config)
    result = builder.build()

    for key, value in result.items():
        print(f"  {key}: {value}")
    print()


def example_mac():
    """MAC 地址生成示例 - 使用字典配置方式"""
    print("=" * 50)
    print("MAC 地址生成示例 - 字典配置方式")
    print("=" * 50)

    schema = {
        "type": "object",
        "properties": {
            "basic_mac": {"type": "string"},
            "hyphen_mac": {"type": "string"},
            "dot_mac": {"type": "string"},
            "unicast_mac": {"type": "string"},
            "multicast_mac": {"type": "string"},
            "broadcast_mac": {"type": "string"},
            "uppercase_mac": {"type": "string"},
        }
    }

    config_dict = {
        "policies": [
            {"path": "basic_mac", "strategy": {"type": "mac"}},
            {"path": "hyphen_mac", "strategy": {"type": "mac", "format": "hyphen"}},
            {"path": "dot_mac", "strategy": {"type": "mac", "format": "dot"}},
            {"path": "unicast_mac", "strategy": {"type": "mac", "address_type": "unicast"}},
            {"path": "multicast_mac", "strategy": {"type": "mac", "address_type": "multicast"}},
            {"path": "broadcast_mac", "strategy": {"type": "mac", "address_type": "broadcast"}},
            {"path": "uppercase_mac", "strategy": {"type": "mac", "uppercase": True}},
        ]
    }

    config = DataBuilder.config_from_dict(config_dict)
    builder = DataBuilder(schema, config)
    result = builder.build()

    for key, value in result.items():
        print(f"  {key}: {value}")
    print()


def example_cidr_and_ip_range():
    """CIDR 和 IP 范围生成示例 - 使用字典配置方式"""
    print("=" * 50)
    print("CIDR 和 IP 范围生成示例 - 字典配置方式")
    print("=" * 50)

    schema = {
        "type": "object",
        "properties": {
            "ipv4_cidr": {"type": "string"},
            "ipv6_cidr": {"type": "string"},
            "ipv4_range": {"type": "string"},
            "ipv6_range": {"type": "string"},
        }
    }

    config_dict = {
        "policies": [
            {"path": "ipv4_cidr", "strategy": {"type": "cidr", "version": 4}},
            {"path": "ipv6_cidr", "strategy": {"type": "cidr", "version": 6}},
            {"path": "ipv4_range", "strategy": {"type": "ip_range", "version": 4}},
            {"path": "ipv6_range", "strategy": {"type": "ip_range", "version": 6}},
        ]
    }

    config = DataBuilder.config_from_dict(config_dict)
    builder = DataBuilder(schema, config)
    result = builder.build()

    for key, value in result.items():
        print(f"  {key}: {value}")
    print()


def example_reuse_port():
    """
    复用已有策略 - 端口号生成

    端口号生成可以直接使用 range_int 策略，无需单独实现 PortStrategy。
    """
    print("=" * 50)
    print("复用已有策略 - 端口号生成 - 字典配置方式")
    print("=" * 50)

    schema = {
        "type": "object",
        "properties": {
            "any_port": {"type": "integer"},
            "well_known_port": {"type": "integer"},   # 知名端口: 0-1023
            "registered_port": {"type": "integer"},    # 注册端口: 1024-49151
            "dynamic_port": {"type": "integer"},       # 动态端口: 49152-65535
            "http_port": {"type": "integer"},          # HTTP 端口: 80
            "https_port": {"type": "integer"},         # HTTPS 端口: 443
        }
    }

    config_dict = {
        "policies": [
            {"path": "any_port", "strategy": {"type": "range", "min": 0, "max": 65535}},
            {"path": "well_known_port", "strategy": {"type": "range", "min": 0, "max": 1023}},
            {"path": "registered_port", "strategy": {"type": "range", "min": 1024, "max": 49151}},
            {"path": "dynamic_port", "strategy": {"type": "range", "min": 49152, "max": 65535}},
            {"path": "http_port", "strategy": {"type": "fixed", "value": 80}},
            {"path": "https_port", "strategy": {"type": "fixed", "value": 443}},
        ]
    }

    config = DataBuilder.config_from_dict(config_dict)
    builder = DataBuilder(schema, config)
    result = builder.build()

    for key, value in result.items():
        print(f"  {key}: {value}")
    print()


def example_reuse_network_address():
    """
    复用已有策略 - 网络服务地址生成

    网络服务地址（IP:端口）可以使用 concat 策略组合生成。
    注意：IPv6 地址需要方括号包裹，如 [::1]:443
    """
    print("=" * 50)
    print("复用已有策略 - 网络服务地址生成 - 字典配置方式")
    print("=" * 50)

    schema = {
        "type": "object",
        "properties": {
            "ipv4_service": {"type": "string"},
            "ipv6_service": {"type": "string"},
            "private_service": {"type": "string"},
            "custom_service": {"type": "string"},
        }
    }

    config_dict = {
        "policies": [
            # IPv4 网络服务地址：IP:端口
            {
                "path": "ipv4_service",
                "strategy": {
                    "type": "concat",
                    "strategies": [
                        {"type": "ipv4", "ip_class": "private"},
                        {"type": "fixed", "value": ":"},
                        {"type": "range", "min": 1024, "max": 65535},
                    ]
                }
            },
            # IPv6 网络服务地址：[IP]:端口
            {
                "path": "ipv6_service",
                "strategy": {
                    "type": "concat",
                    "strategies": [
                        {"type": "fixed", "value": "["},
                        {"type": "ipv6", "address_type": "link_local"},
                        {"type": "fixed", "value": "]:"},
                        {"type": "range", "min": 1024, "max": 65535},
                    ]
                }
            },
            # 私有地址 + 知名端口
            {
                "path": "private_service",
                "strategy": {
                    "type": "concat",
                    "strategies": [
                        {"type": "ipv4", "ip_class": "private"},
                        {"type": "fixed", "value": ":"},
                        {"type": "fixed", "value": "8080"},
                    ]
                }
            },
            # 自定义网段 + 端口范围
            {
                "path": "custom_service",
                "strategy": {
                    "type": "concat",
                    "strategies": [
                        {"type": "ipv4", "subnet": "10.0.0.0/24"},
                        {"type": "fixed", "value": ":"},
                        {"type": "range", "min": 8000, "max": 9000},
                    ]
                }
            },
        ]
    }

    config = DataBuilder.config_from_dict(config_dict)
    builder = DataBuilder(schema, config)
    result = builder.build()

    for key, value in result.items():
        print(f"  {key}: {value}")
    print()


def example_reuse_interface_name():
    """
    复用已有策略 - 网络接口名称生成

    网络接口名称是有限枚举，可以直接使用 enum 策略。
    """
    print("=" * 50)
    print("复用已有策略 - 网络接口名称生成 - 字典配置方式")
    print("=" * 50)

    # 常见网络接口名称
    INTERFACE_NAMES = [
        "eth0", "eth1", "eth2", "eth3",
        "wlan0", "wlan1",
        "enp0s3", "enp0s8",
        "wlp2s0",
        "bond0", "bond1",
        "br0", "docker0", "virbr0",
        "lo",
        "tun0", "tun1",
        "tap0", "tap1",
    ]

    # 以太网接口
    ETHERNET_INTERFACES = ["eth0", "eth1", "eth2", "enp0s3", "enp0s8"]

    # 无线接口
    WIRELESS_INTERFACES = ["wlan0", "wlan1", "wlp2s0"]

    # 虚拟接口
    VIRTUAL_INTERFACES = ["docker0", "virbr0", "tun0", "tap0", "bond0"]

    schema = {
        "type": "object",
        "properties": {
            "any_interface": {"type": "string"},
            "ethernet_interface": {"type": "string"},
            "wireless_interface": {"type": "string"},
            "virtual_interface": {"type": "string"},
        }
    }

    config_dict = {
        "policies": [
            {"path": "any_interface", "strategy": {"type": "enum", "values": INTERFACE_NAMES}},
            {"path": "ethernet_interface", "strategy": {"type": "enum", "values": ETHERNET_INTERFACES}},
            {"path": "wireless_interface", "strategy": {"type": "enum", "values": WIRELESS_INTERFACES}},
            {"path": "virtual_interface", "strategy": {"type": "enum", "values": VIRTUAL_INTERFACES}},
        ]
    }

    config = DataBuilder.config_from_dict(config_dict)
    builder = DataBuilder(schema, config)
    result = builder.build()

    for key, value in result.items():
        print(f"  {key}: {value}")
    print()


def example_combined_network_data():
    """综合示例：生成完整的网络配置数据 - 使用字典配置方式"""
    print("=" * 50)
    print("综合示例：完整的网络配置数据 - 字典配置方式")
    print("=" * 50)

    schema = {
        "type": "object",
        "properties": {
            "hostname": {"type": "string"},
            "ip_address": {"type": "string"},
            "subnet_mask": {"type": "string"},
            "gateway": {"type": "string"},
            "dns_primary": {"type": "string"},
            "dns_secondary": {"type": "string"},
            "mac_address": {"type": "string"},
            "port": {"type": "integer"},
            "service_url": {"type": "string"},
            "interface": {"type": "string"},
            "cidr": {"type": "string"},
            "ip_range": {"type": "string"},
        }
    }

    # 常见 DNS 服务器
    DNS_SERVERS = ["8.8.8.8", "8.8.4.4", "1.1.1.1", "114.114.114.114"]

    config_dict = {
        "policies": [
            {"path": "hostname", "strategy": {"type": "domain", "tld": "local", "prefix": "server-"}},
            {"path": "ip_address", "strategy": {"type": "ipv4", "ip_class": "private"}},
            {"path": "subnet_mask", "strategy": {"type": "fixed", "value": "255.255.255.0"}},
            {"path": "gateway", "strategy": {"type": "ipv4", "subnet": "192.168.1.0/24"}},
            {"path": "dns_primary", "strategy": {"type": "enum", "values": DNS_SERVERS[:2]}},
            {"path": "dns_secondary", "strategy": {"type": "enum", "values": DNS_SERVERS[2:]}},
            {"path": "mac_address", "strategy": {"type": "mac", "address_type": "unicast"}},
            {"path": "port", "strategy": {"type": "range", "min": 1024, "max": 65535}},
            {"path": "service_url", "strategy": {"type": "url", "scheme": "https", "include_query": True}},
            {"path": "interface", "strategy": {"type": "enum", "values": ["eth0", "eth1", "wlan0"]}},
            {"path": "cidr", "strategy": {"type": "cidr", "version": 4, "include_private": True}},
            {"path": "ip_range", "strategy": {"type": "ip_range", "version": 4}},
        ]
    }

    config = DataBuilder.config_from_dict(config_dict)
    builder = DataBuilder(schema, config)
    result = builder.build()

    for key, value in result.items():
        print(f"  {key}: {value}")
    print()


if __name__ == "__main__":
    """运行所有示例"""
    example_ipv4()
    example_ipv6()
    example_domain()
    example_hostname()
    example_url()
    example_iri()
    example_mac()
    example_cidr_and_ip_range()
    example_reuse_port()
    example_reuse_network_address()
    example_reuse_interface_name()
    example_combined_network_data()
