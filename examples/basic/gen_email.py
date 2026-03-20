"""
EmailFakerStrategy 使用示例

展示 email 策略的各种用法，包括：
- 基础用法（不同邮箱类型）
- 指定 locale（区域语言）
- 通过配置创建（使用 StrategyRegistry）
- 结合 BuilderConfig 和 FieldPolicy 使用
- 多种邮箱类型（qq、gmail、163、outlook、custom、safe、idn）
- 自定义域名和参数别名
- IDN 国际化域名邮箱（unicode/punycode/both 格式）
"""

from data_builder import DataBuilder


def example_basics():
    """基础用法示例：生成不同类型的邮箱"""
    print("=" * 60)
    print("1. 基础用法（不同邮箱类型）")
    print("=" * 60)

    schema = {"type": "object", "properties": {"email": {"type": "string"}}}

    # QQ 邮箱：8位纯数字用户名
    config = DataBuilder.config_from_dict({
        "policies": [
            {"path": "email", "strategy": {"type": "email", "email_type": "qq"}}
        ]
    })
    builder = DataBuilder(schema, config)
    data = builder.build(3)
    print("  QQ 邮箱:")
    for item in data:
        print(f"    {item['email']}")

    # Gmail：first.last 格式（小写，中间点号）
    config = DataBuilder.config_from_dict({
        "policies": [
            {"path": "email", "strategy": {"type": "email", "email_type": "gmail"}}
        ]
    })
    builder = DataBuilder(schema, config)
    data = builder.build(3)
    print("  Gmail:")
    for item in data:
        print(f"    {item['email']}")

    # 163 邮箱
    config = DataBuilder.config_from_dict({
        "policies": [
            {"path": "email", "strategy": {"type": "email", "email_type": "163"}}
        ]
    })
    builder = DataBuilder(schema, config)
    data = builder.build(3)
    print("  163 邮箱:")
    for item in data:
        print(f"    {item['email']}")

    # Outlook 邮箱
    config = DataBuilder.config_from_dict({
        "policies": [
            {"path": "email", "strategy": {"type": "email", "email_type": "outlook"}}
        ]
    })
    builder = DataBuilder(schema, config)
    data = builder.build(3)
    print("  Outlook 邮箱:")
    for item in data:
        print(f"    {item['email']}")

    # 自定义域名
    config = DataBuilder.config_from_dict({
        "policies": [
            {"path": "email", "strategy": {"type": "email", "email_type": "custom", "domains": ["example.com", "test.org", "mycompany.net"]}}
        ]
    })
    builder = DataBuilder(schema, config)
    data = builder.build(3)
    print("  自定义域名:")
    for item in data:
        print(f"    {item['email']}")

    # 安全邮箱（Faker 内置）
    config = DataBuilder.config_from_dict({
        "policies": [
            {"path": "email", "strategy": {"type": "email", "email_type": "safe"}}
        ]
    })
    builder = DataBuilder(schema, config)
    data = builder.build(3)
    print("  安全邮箱:")
    for item in data:
        print(f"    {item['email']}")


def example_with_locale():
    """指定 locale（区域语言）示例"""
    print("\n" + "=" * 60)
    print("2. 指定 locale（区域语言）")
    print("=" * 60)

    schema = {"type": "object", "properties": {"email": {"type": "string"}}}

    # 英文 locale
    config = DataBuilder.config_from_dict({
        "policies": [
            {"path": "email", "strategy": {"type": "email", "email_type": "gmail", "locale": "en_US"}}
        ]
    })
    builder = DataBuilder(schema, config)
    data = builder.build(3)
    print("  Gmail (en_US):")
    for item in data:
        print(f"    {item['email']}")

    # 中文 locale（默认）
    config = DataBuilder.config_from_dict({
        "policies": [
            {"path": "email", "strategy": {"type": "email", "email_type": "gmail", "locale": "zh_CN"}}
        ]
    })
    builder = DataBuilder(schema, config)
    data = builder.build(3)
    print("  Gmail (zh_CN):")
    for item in data:
        print(f"    {item['email']}")


def example_with_registry():
    """通过配置创建邮箱策略示例"""
    print("\n" + "=" * 60)
    print("3. 通过 config_from_dict 配置")
    print("=" * 60)

    # 使用 config_from_dict 创建策略
    config = DataBuilder.config_from_dict({
        "policies": [{"path": "email", "strategy": {"type": "email", "email_type": "qq"}}]
    })
    strategy = config.policies[0].strategy

    print(f"  策略类型: {type(strategy).__name__}")
    print(f"  邮箱类型: {strategy.email_type}")

    # 生成数据
    schema = {"type": "object", "properties": {"email": {"type": "string"}}}
    builder = DataBuilder(schema, config)
    data = builder.build(3)
    print("  生成3条数据:")
    for item in data:
        print(f"    {item['email']}")


def example_custom_domains():
    """自定义域名示例"""
    print("\n" + "=" * 60)
    print("4. 自定义域名")
    print("=" * 60)

    schema = {"type": "object", "properties": {"email": {"type": "string"}}}

    # 通过 domains 参数指定多个域名
    config = DataBuilder.config_from_dict({
        "policies": [
            {"path": "email", "strategy": {"type": "email", "email_type": "custom", "domains": ["example.com", "test.org", "mycompany.net"]}}
        ]
    })
    builder = DataBuilder(schema, config)
    data = builder.build(5)
    print("  自定义多域名:")
    for item in data:
        print(f"    {item['email']}")

    # 通过配置字典创建 custom 类型
    config = DataBuilder.config_from_dict({
        "policies": [{"path": "email", "strategy": {"type": "email", "email_type": "custom", "domain": "example.com,company.org"}}]
    })
    strategy2 = config.policies[0].strategy
    print(f"  策略类型: {type(strategy2).__name__}")
    print(f"  域名列表: {strategy2.domains}")


def example_with_builder_config():
    """使用 BuilderConfig（policies 格式）示例"""
    print("\n" + "=" * 60)
    print("5. 使用 BuilderConfig（policies 格式）")
    print("=" * 60)

    schema = {
        "type": "object",
        "properties": {
            "user_email": {"type": "string"},
            "work_email": {"type": "string"},
            "personal_email": {"type": "string"},
            "contact_email": {"type": "string"},
        },
    }

    # 使用 policies 格式配置策略
    # 注意：outlook 类型只支持 outlook.com/hotmail.com，不支持自定义域名
    config = DataBuilder.config_from_dict({
        "policies": [
            {"path": "user_email", "strategy": {"type": "email", "email_type": "qq"}},
            {"path": "work_email", "strategy": {"type": "email", "email_type": "outlook"}},
            {"path": "personal_email", "strategy": {"type": "email", "email_type": "gmail"}},
            {"path": "contact_email", "strategy": {"type": "email", "email_type": "safe", "domain": "example.com"}},
        ]
    })

    builder = DataBuilder(schema, config)
    results = builder.build(count=3)

    for idx, row in enumerate(results):
        print(f"\n  样本 {idx + 1}:")
        print(f"    用户邮箱 (QQ): {row['user_email']}")
        print(f"    工作邮箱 (Outlook): {row['work_email']}")
        print(f"    个人邮箱 (Gmail): {row['personal_email']}")
        print(f"    联系邮箱 (安全): {row['contact_email']}")


def example_param_aliases():
    """参数别名示例"""
    print("\n" + "=" * 60)
    print("6. 参数别名")
    print("=" * 60)

    # 使用 email_type 参数（完整写法）
    config = DataBuilder.config_from_dict({
        "policies": [{"path": "email", "strategy": {"type": "email", "email_type": "qq"}}]
    })
    strategy = config.policies[0].strategy
    print(f"  使用完整参数 'email_type': {strategy.email_type}")
    print(f"  生成的邮箱: {strategy.generate(None)}")

    # 使用 domain 作为 domains 的简写别名（单数转复数）
    config2 = DataBuilder.config_from_dict({
        "policies": [{"path": "email", "strategy": {"type": "email", "email_type": "custom", "domain": "example.com"}}]
    })
    strategy2 = config2.policies[0].strategy
    print(f"\n  使用简写 'domain' (alias): {strategy2.domains}")
    print(f"  生成的邮箱: {strategy2.generate(None)}")

    # 使用逗号分隔的字符串指定多个域名
    config3 = DataBuilder.config_from_dict({
        "policies": [{"path": "email", "strategy": {"type": "email", "email_type": "custom", "domain": "example.com,company.org,test.net"}}]
    })
    strategy3 = config3.policies[0].strategy
    print(f"\n  多域名配置: {strategy3.domains}")
    print(f"  生成的邮箱: {strategy3.generate(None)}")


def example_real_world_scenario():
    """真实场景示例：用户注册系统"""
    print("\n" + "=" * 60)
    print("7. 真实场景：用户注册系统")
    print("=" * 60)

    schema = {
        "type": "object",
        "properties": {
            "user_id": {"type": "string"},
            "email": {"type": "string"},
            "backup_email": {"type": "string"},
            "contact": {"type": "string"},
        }
    }

    config = DataBuilder.config_from_dict({
        "policies": [
            # 用户主邮箱：使用 QQ
            {"path": "email", "strategy": {"type": "email", "email_type": "qq"}},
            # 备用邮箱：使用自定义域名
            {"path": "backup_email", "strategy": {"type": "email", "email_type": "custom", "domains": ["backup.com", "reserve.org"]}},
            # 联系邮箱：使用安全邮箱
            {"path": "contact", "strategy": {"type": "email", "email_type": "safe"}},
        ]
    })

    builder = DataBuilder(schema, config)
    data = builder.build(5)

    print("  生成5个用户的邮箱信息:")
    for item in data:
        print(f"    主邮箱: {item['email']}")
        print(f"    备用邮箱: {item['backup_email']}")
        print(f"    联系邮箱: {item['contact']}")
        print()


def example_random_type():
    """随机类型示例：每次随机选择一种邮箱类型"""
    print("\n" + "=" * 60)
    print("8. 随机类型（random）")
    print("=" * 60)

    schema = {"type": "object", "properties": {"email": {"type": "string"}}}

    # 使用 random 类型：每次生成随机选择一种邮箱格式
    config = DataBuilder.config_from_dict({
        "policies": [
            {"path": "email", "strategy": {"type": "email", "email_type": "random"}}
        ]
    })
    builder = DataBuilder(schema, config)
    data = builder.build(10)

    print("  随机类型邮箱（每次随机选择一种格式）:")
    for idx, item in enumerate(data, 1):
        print(f"    {idx}. {item['email']}")

    # 通过配置字典创建 random 类型
    print("\n  通过配置字典创建 random 类型:")
    config = DataBuilder.config_from_dict({
        "policies": [{"path": "email", "strategy": {"type": "email", "email_type": "random"}}]
    })
    strategy = config.policies[0].strategy
    print(f"    策略类型: {strategy.email_type}")
    for idx in range(5):
        print(f"    {idx+1}. {strategy.generate(None)}")


def example_idn_email():
    """IDN 国际化域名邮箱示例"""
    print("\n" + "=" * 60)
    print("9. IDN 国际化域名邮箱（idn）")
    print("=" * 60)

    schema = {"type": "object", "properties": {"email": {"type": "string"}}}

    # IDN Unicode 格式（默认）
    print("\n  IDN Unicode 格式（user@中国.cn）:")
    config = DataBuilder.config_from_dict({
        "policies": [
            {"path": "email", "strategy": {"type": "email", "email_type": "idn", "output_format": "unicode"}}
        ]
    })
    builder = DataBuilder(schema, config)
    data = builder.build(3)
    for item in data:
        print(f"    {item['email']}")

    # IDN Punycode 格式
    print("\n  IDN Punycode 格式（user@xn--fiqs8s.cn）:")
    config = DataBuilder.config_from_dict({
        "policies": [
            {"path": "email", "strategy": {"type": "email", "email_type": "idn", "output_format": "punycode"}}
        ]
    })
    builder = DataBuilder(schema, config)
    data = builder.build(3)
    for item in data:
        print(f"    {item['email']}")

    # IDN Both 格式（同时输出 unicode 和 punycode）
    print("\n  IDN Both 格式（输出字典）:")
    config = DataBuilder.config_from_dict({
        "policies": [
            {"path": "email", "strategy": {"type": "email", "email_type": "idn", "output_format": "both"}}
        ]
    })
    builder = DataBuilder(schema, config)
    data = builder.build(3)
    for item in data:
        email_dict = item['email']
        print(f"    Unicode: {email_dict['unicode']}")
        print(f"    Punycode: {email_dict['punycode']}")

    # 自定义 IDN 域名列表
    print("\n  自定义 IDN 域名列表:")
    config = DataBuilder.config_from_dict({
        "policies": [
            {"path": "email", "strategy": {
                "type": "email",
                "email_type": "idn",
                "idn_domains": ["中国.cn", "日本.jp", "한국.kr"],
                "output_format": "unicode"
            }}
        ]
    })
    builder = DataBuilder(schema, config)
    data = builder.build(3)
    for item in data:
        print(f"    {item['email']}")


def example_random_includes_idn():
    """random 类型包含 idn 邮箱示例"""
    print("\n" + "=" * 60)
    print("10. random 类型包含 IDN 邮箱")
    print("=" * 60)

    schema = {"type": "object", "properties": {"email": {"type": "string"}}}

    config = DataBuilder.config_from_dict({
        "policies": [
            {"path": "email", "strategy": {"type": "email", "email_type": "random", "include_idn": True}}
        ]
    })
    builder = DataBuilder(schema, config)
    data = builder.build(10)

    print("  random 类型生成的邮箱（可能包含 IDN）:")
    for idx, item in enumerate(data, 1):
        print(f"    {idx}. {item['email']}")


def example_random_exclude_idn():
    """random 类型排除 idn 邮箱示例"""
    print("\n" + "=" * 60)
    print("11. random 类型排除 IDN 邮箱")
    print("=" * 60)

    schema = {"type": "object", "properties": {"email": {"type": "string"}}}

    config = DataBuilder.config_from_dict({
        "policies": [
            {"path": "email", "strategy": {
                "type": "email", 
                "email_type": "random",
                "include_idn": False  # 排除 IDN 邮箱
            }}
        ]
    })
    builder = DataBuilder(schema, config)
    data = builder.build(10)

    print("  random 类型生成的邮箱（排除 IDN）:")
    for idx, item in enumerate(data, 1):
        print(f"    {idx}. {item['email']}")


def example_idn_email_format():
    """展示 JSON Schema format: idn-email 的用法"""
    print("\n" + "=" * 60)
    print("12. JSON Schema format: idn-email")
    print("=" * 60)

    schema = {
        "type": "object",
        "properties": {
            "email": {"type": "string", "format": "idn-email"}
        }
    }

    builder = DataBuilder(schema)
    data = builder.build(5)
    
    print("  生成的 IDN 邮箱:")
    for idx, item in enumerate(data, 1):
        print(f"    {idx}. {item['email']}")


if __name__ == "__main__":
    example_basics()
    example_with_locale()
    example_with_registry()
    example_custom_domains()
    example_with_builder_config()
    example_param_aliases()
    example_real_world_scenario()
    example_random_type()
    example_idn_email()
    example_random_includes_idn()
    example_random_exclude_idn()
    example_idn_email_format()
