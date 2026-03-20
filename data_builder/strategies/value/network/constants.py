"""网络数据生成策略常量定义"""

# =============================================================================
# IPv4 地址常量
# =============================================================================

# IPv4 地址类别范围（排除保留地址）
IPV4_CLASS_A = (1, 0, 0, 0), (126, 255, 255, 255)      # A类: 1.0.0.0 - 126.255.255.255
IPV4_CLASS_B = (128, 0, 0, 0), (191, 255, 255, 255)    # B类: 128.0.0.0 - 191.255.255.255
IPV4_CLASS_C = (192, 0, 0, 0), (223, 255, 255, 255)    # C类: 192.0.0.0 - 223.255.255.255
IPV4_CLASS_D = (224, 0, 0, 0), (239, 255, 255, 255)    # D类(组播): 224.0.0.0 - 239.255.255.255
IPV4_CLASS_E = (240, 0, 0, 0), (255, 255, 255, 254)    # E类(保留): 240.0.0.0 - 255.255.255.254

# 私有地址范围
IPV4_PRIVATE_A = "10.0.0.0/8"          # A类私有: 10.0.0.0 - 10.255.255.255
IPV4_PRIVATE_B = "172.16.0.0/12"       # B类私有: 172.16.0.0 - 172.31.255.255
IPV4_PRIVATE_C = "192.168.0.0/16"      # C类私有: 192.168.0.0 - 192.168.255.255

# 特殊用途地址
IPV4_LOOPBACK = "127.0.0.0/8"          # 回环地址
IPV4_LINK_LOCAL = "169.254.0.0/16"     # 链路本地
IPV4_ANY = "0.0.0.0"                    # 任意地址
IPV4_BROADCAST = "255.255.255.255"      # 有限广播

# 组播地址范围
IPV4_MULTICAST_LOCAL = "224.0.0.0/24"           # 本地网络控制
IPV4_MULTICAST_INTERNET = "224.0.1.0/238.255.255.255"  # 全球组播
IPV4_MULTICAST_ADMIN = "239.0.0.0/8"            # 管理范围组播

# 保留/测试网络
IPV4_TEST_NET_1 = "192.0.2.0/24"       # TEST-NET-1
IPV4_TEST_NET_2 = "198.51.100.0/24"    # TEST-NET-2
IPV4_TEST_NET_3 = "203.0.113.0/24"     # TEST-NET-3

# 子网掩码（CIDR -> 点分十进制映射）
SUBNET_MASKS = {
    0: "0.0.0.0",
    1: "128.0.0.0",
    8: "255.0.0.0",
    16: "255.255.0.0",
    24: "255.255.255.0",
    25: "255.255.255.128",
    26: "255.255.255.192",
    27: "255.255.255.224",
    28: "255.255.255.240",
    29: "255.255.255.248",
    30: "255.255.255.252",
    31: "255.255.255.254",
    32: "255.255.255.255",
}

# =============================================================================
# IPv6 地址常量
# =============================================================================

# IPv6 地址类型前缀
IPV6_UNSPECIFIED = "::"                           # 未指定地址
IPV6_LOOPBACK = "::1"                             # 回环地址
IPV6_IPV4_MAPPED_PREFIX = "::ffff:"               # IPv4映射地址前缀
IPV6_LINK_LOCAL_PREFIX = "fe80::/10"              # 链路本地
IPV6_UNIQUE_LOCAL_PREFIX = "fc00::/7"             # 唯一本地
IPV6_MULTICAST_PREFIX = "ff00::/8"                # 组播地址
IPV6_GLOBAL_UNICAST_PREFIX = "2000::/3"           # 全局单播

# IPv6 组播范围
IPV6_MULTICAST_SCOPES = {
    0: "reserved",      # 保留
    1: "interface",     # 接口本地
    2: "link",          # 链路本地
    3: "subnet",        # 子网本地
    4: "admin",         # 管理本地
    5: "site",          # 站点本地
    8: "organization",  # 组织本地
    14: "global",       # 全球
}

# =============================================================================
# 域名常量
# =============================================================================

# 常见顶级域名（TLD）
COMMON_TLDS = [
    # 通用顶级域
    "com", "org", "net", "edu", "gov", "mil", "int", "io", "co", "ai",
    # 国家代码顶级域
    "cn", "us", "uk", "jp", "de", "fr", "ru", "kr", "tw", "hk",
    # 新通用顶级域
    "app", "dev", "blog", "shop", "online", "site", "tech", "cloud",
]

# 保留/测试用顶级域
RESERVED_TLDS = [
    "test", "example", "invalid", "localhost",
]

# 常用二级域名前缀
COMMON_SUBDOMAINS = [
    "www", "mail", "ftp", "blog", "api", "cdn", "static",
    "admin", "portal", "app", "mobile", "shop", "store",
]

# IDN 国际化域名池
IDN_DOMAINS = [
    "中国.cn", "公司.cn", "网络.cn",
    "中国.com", "中国.net",
    "世界.org", "日本.jp", "한국.kr",
    "德国.de", "法国.fr", "俄国.ru",
]

# =============================================================================
# URL 常量
# =============================================================================

# 常见 URL scheme
URL_SCHEMES = [
    "http", "https", "ftp", "ftps", "sftp",
    "file", "ws", "wss", "mailto", "tel",
]

# 常见端口号与服务映射
WELL_KNOWN_PORTS = {
    20: "ftp-data",
    21: "ftp",
    22: "ssh",
    23: "telnet",
    25: "smtp",
    53: "dns",
    80: "http",
    110: "pop3",
    143: "imap",
    443: "https",
    465: "smtps",
    587: "smtp-tls",
    993: "imaps",
    995: "pop3s",
    3306: "mysql",
    5432: "postgresql",
    6379: "redis",
    8080: "http-proxy",
    8443: "https-proxy",
    27017: "mongodb",
}

# 常见 URL 路径
URL_PATHS = [
    "/", "/index.html", "/api", "/api/v1", "/api/v2",
    "/login", "/logout", "/register", "/user", "/admin",
    "/search", "/upload", "/download", "/static", "/assets",
]

# =============================================================================
# MAC 地址常量
# =============================================================================

# 常见厂商 OUI（前3字节）
VENDOR_OUIS = {
    "00:00:00": "Xerox",
    "00:05:02": "Apple",
    "00:0A:95": "Apple",
    "00:0D:93": "Apple",
    "00:0E:35": "Apple",
    "00:17:F2": "Apple",
    "00:1B:63": "Apple",
    "00:1C:B3": "Apple",
    "00:1E:52": "Apple",
    "00:1F:5B": "Apple",
    "00:1F:F3": "Apple",
    "00:23:12": "Apple",
    "00:23:DF": "Apple",
    "00:25:00": "Apple",
    "00:25:4B": "Apple",
    "00:25:BC": "Apple",
    "00:26:08": "Apple",
    "00:26:4A": "Apple",
    "00:26:B0": "Apple",
    "00:26:BB": "Apple",
    "00:30:65": "Apple",
    "00:50:E4": "Apple",
    "00:A0:40": "Apple",
    "00:E0:33": "Apple",
    "00:03:93": "Apple",
    "08:00:07": "Apple",
    "10:9A:DD": "Apple",
    "10:DD:B1": "Apple",
    "14:10:9F": "Apple",
    "14:20:5E": "Apple",
    "18:34:51": "Apple",
    "18:E7:F4": "Apple",
    "1C:1A:C0": "Apple",
    "1C:AB:A7": "Apple",
    "20:C9:D0": "Apple",
    "24:A0:74": "Apple",
    "24:A2:E1": "Apple",
    "28:0B:5C": "Apple",
    "28:37:37": "Apple",
    "28:A0:2B": "Apple",
    "28:E1:2C": "Apple",
    "28:E7:CF": "Apple",
    "2C:33:11": "Apple",
    "2C:56:DC": "Apple",
    "2C:9C:A2": "Apple",
    "30:10:B3": "Apple",
    "30:63:6B": "Apple",
    "30:90:AB": "Apple",
    "34:12:F9": "Apple",
    "34:36:B1": "Apple",
    "34:A3:95": "Apple",
    "34:C0:59": "Apple",
    "34:E2:FD": "Apple",
    "38:C9:86": "Apple",
    "3C:07:54": "Apple",
    "3C:15:B2": "Apple",
    "3C:2E:F9": "Apple",
    "3C:8B:FE": "Apple",
    "3C:A5:34": "Apple",
    "3C:D9:2B": "Apple",
    "40:33:1A": "Apple",
    "40:3C:FC": "Apple",
    "40:A6:D9": "Apple",
    "40:B3:21": "Apple",
    "40:CB:C0": "Apple",
    "40:D3:2D": "Apple",
    "44:38:39": "Apple",
    "44:4B:D1": "Apple",
    "44:59:E3": "Apple",
    "44:D8:84": "Apple",
    "48:43:7C": "Apple",
    "48:60:BC": "Apple",
    "48:A1:95": "Apple",
    "48:A9:D2": "Apple",
    "48:D7:05": "Apple",
    "4C:57:CA": "Apple",
    "4C:7C:5F": "Apple",
    "50:32:37": "Apple",
    "50:4B:BD": "Apple",
    "50:7A:55": "Apple",
    "50:BC:96": "Apple",
    "50:DD:47": "Apple",
    "54:10:0D": "Apple",
    "54:26:96": "Apple",
    "54:4E:90": "Apple",
    "54:59:90": "Apple",
    "54:72:4F": "Apple",
    "54:80:D3": "Apple",
    "54:9F:13": "Apple",
    "54:AF:97": "Apple",
    "54:B5:03": "Apple",
    "54:E1:AD": "Apple",
    "58:1F:AA": "Apple",
    "58:40:4E": "Apple",
    "58:55:CA": "Apple",
    "58:B0:35": "Apple",
    "5C:95:AE": "Apple",
    "5C:F9:38": "Apple",
    "60:03:08": "Apple",
    "60:33:4B": "Apple",
    "60:45:CB": "Apple",
    "60:92:3E": "Apple",
    "60:C5:47": "Apple",
    "60:F8:1D": "Apple",
    "60:FA:CD": "Apple",
    "60:FB:42": "Apple",
    "64:20:0C": "Apple",
    "64:4B:F0": "Apple",
    "64:76:BA": "Apple",
    "64:9A:BE": "Apple",
    "64:A3:CB": "Apple",
    "64:B9:E8": "Apple",
    "64:E6:06": "Apple",
    "68:5B:35": "Apple",
    "68:64:4B": "Apple",
    "68:9C:70": "Apple",
    "68:A8:6D": "Apple",
    "68:DB:CA": "Apple",
    "6C:19:C0": "Apple",
    "6C:3E:6D": "Apple",
    "6C:40:08": "Apple",
    "6C:57:34": "Apple",
    "6C:70:9F": "Apple",
    "6C:72:E7": "Apple",
    "6C:94:66": "Apple",
    "70:11:24": "Apple",
    "70:3E:AC": "Apple",
    "70:48:0F": "Apple",
    "70:56:81": "Apple",
    "70:73:CB": "Apple",
    "70:85:C0": "Apple",
    "70:9E:84": "Apple",
    "70:CD:60": "Apple",
    "70:DE:A2": "Apple",
    "74:1B:B2": "Apple",
    "74:23:44": "Apple",
    "74:45:CE": "Apple",
    "74:81:14": "Apple",
    "74:9E:AF": "Apple",
    "74:A3:E4": "Apple",
    "74:B5:7E": "Apple",
    "74:D4:35": "Apple",
    "74:D8:3B": "Apple",
    "74:E1:B6": "Apple",
    "74:E2:F5": "Apple",
    "78:31:C1": "Apple",
    "78:4F:43": "Apple",
    "78:7B:8A": "Apple",
    "78:88:6D": "Apple",
    "78:A3:E4": "Apple",
    "78:CA:39": "Apple",
    "78:D7:51": "Apple",
    "78:FD:20": "Apple",
    "7C:01:91": "Apple",
    "7C:11:BE": "Apple",
    "7C:3E:CB": "Apple",
    "7C:6D:62": "Apple",
    "7C:70:BC": "Apple",
    "7C:83:EF": "Apple",
    "7C:C3:A1": "Apple",
    "7C:D1:C3": "Apple",
    "7C:D5:6E": "Apple",
    "7C:F0:5F": "Apple",
    "7C:F9:0E": "Apple",
    "80:13:77": "Apple",
    "80:35:C1": "Apple",
    "80:4E:81": "Apple",
    "80:69:1A": "Apple",
    "80:85:89": "Apple",
    "80:92:9F": "Apple",
    "80:A5:89": "Apple",
    "80:E8:2C": "Apple",
    "84:38:35": "Apple",
    "84:3A:5B": "Apple",
    "84:4B:F5": "Apple",
    "84:78:8B": "Apple",
    "84:89:AD": "Apple",
    "84:A1:D1": "Apple",
    "84:B1:53": "Apple",
    "84:C5:A6": "Apple",
    "84:D6:D0": "Apple",
    "84:E8:7E": "Apple",
    "84:FC:FE": "Apple",
    "88:1F:A1": "Apple",
    "88:53:2D": "Apple",
    "88:63:DF": "Apple",
    "88:66:5A": "Apple",
    "88:6B:9F": "Apple",
    "88:87:17": "Apple",
    "88:AE:1D": "Apple",
    "88:C6:26": "Apple",
    "88:CB:87": "Apple",
    "88:E7:12": "Apple",
    "8C:00:6D": "Apple",
    "8C:29:37": "Apple",
    "8C:2D:AA": "Apple",
    "8C:58:77": "Apple",
    "8C:7C:93": "Apple",
    "8C:85:90": "Apple",
    "8C:8E:F2": "Apple",
    "8C:BE:BE": "Apple",
    "8C:D9:3D": "Apple",
    "8C:ED:D7": "Apple",
    "8C:F5:A3": "Apple",
    "8C:FF:28": "Apple",
    "90:03:B7": "Apple",
    "90:27:E4": "Apple",
    "90:4C:8E": "Apple",
    "90:72:40": "Apple",
    "90:79:44": "Apple",
    "90:84:0D": "Apple",
    "90:8D:6C": "Apple",
    "90:95:26": "Apple",
    "90:B2:1F": "Apple",
    "90:B7:D0": "Apple",
    "90:CD:B4": "Apple",
    "90:E2:FC": "Apple",
    "94:0E:6B": "Apple",
    "94:4A:50": "Apple",
    "94:65:2D": "Apple",
    "94:6A:77": "Apple",
    "94:87:11": "Apple",
    "94:94:26": "Apple",
    "94:9E:AC": "Apple",
    "94:B0:01": "Apple",
    "94:B1:0B": "Apple",
    "94:B3:07": "Apple",
    "94:B8:86": "Apple",
    "94:BF:AA": "Apple",
    "94:C6:91": "Apple",
    "94:D9:90": "Apple",
    "94:E9:6A": "Apple",
    "94:F6:A3": "Apple",
    "94:F8:27": "Apple",
    "98:01:A7": "Apple",
    "98:01:B6": "Apple",
    "98:03:D8": "Apple",
    "98:06:5A": "Apple",
    "98:0B:AD": "Apple",
    "98:10:E8": "Apple",
    "98:15:90": "Apple",
    "98:18:88": "Apple",
    "98:23:10": "Apple",
    "98:29:45": "Apple",
    "98:39:8E": "Apple",
    "98:40:BB": "Apple",
    "98:46:43": "Apple",
    "98:48:27": "Apple",
    "98:4F:4F": "Apple",
    "98:51:5A": "Apple",
    "98:5A:EB": "Apple",
    "98:5D:AD": "Apple",
    "98:61:22": "Apple",
    "98:63:10": "Apple",
    "98:65:0E": "Apple",
    "98:67:0D": "Apple",
    "98:6B:AD": "Apple",
    "98:6D:35": "Apple",
    "98:71:67": "Apple",
    "98:72:06": "Apple",
    "98:7A:14": "Apple",
    "98:7E:36": "Apple",
    "98:83:89": "Apple",
    "98:84:E3": "Apple",
    "98:88:6B": "Apple",
    "98:8A:59": "Apple",
    "98:8E:D8": "Apple",
    "98:90:96": "Apple",
    "98:93:70": "Apple",
    "98:94:B9": "Apple",
    "98:97:4C": "Apple",
    "98:9A:9E": "Apple",
    "98:9B:CB": "Apple",
    "98:A0:13": "Apple",
    "98:A5:0A": "Apple",
    "98:A6:7F": "Apple",
    "98:A9:43": "Apple",
    "98:AA:8F": "Apple",
    "98:AC:BC": "Apple",
    "98:AE:0B": "Apple",
    "98:B0:28": "Apple",
    "98:B5:1D": "Apple",
    "98:B8:A5": "Apple",
    "98:B9:08": "Apple",
    "98:B9:C9": "Apple",
    "98:BA:5C": "Apple",
    "98:BC:9C": "Apple",
    "98:BD:28": "Apple",
    "98:BF:21": "Apple",
    "98:C1:0A": "Apple",
    "98:C2:5C": "Apple",
    "98:C3:32": "Apple",
    "98:C5:7B": "Apple",
    "98:C7:5F": "Apple",
    "98:C8:95": "Apple",
    "98:CA:33": "Apple",
    "98:CB:8D": "Apple",
    "98:CC:0F": "Apple",
    "98:CD:AC": "Apple",
    "98:CE:5F": "Apple",
    "98:D0:2D": "Apple",
    "98:D1:9F": "Apple",
    "98:D2:03": "Apple",
    "98:D3:31": "Apple",
    "98:D4:63": "Apple",
    "98:D6:F7": "Apple",
    "98:D8:8B": "Apple",
    "98:D9:B7": "Apple",
    "98:DA:83": "Apple",
    "98:DB:15": "Apple",
    "98:DC:AD": "Apple",
    "98:DD:60": "Apple",
    "98:DE:D0": "Apple",
    "98:E0:30": "Apple",
    "98:E1:29": "Apple",
    "98:E2:0F": "Apple",
    "98:E3:34": "Apple",
    "98:E4:39": "Apple",
    "98:E5:43": "Apple",
    "98:E6:EA": "Apple",
    "98:E7:43": "Apple",
    "98:E9:28": "Apple",
    "98:EA:5D": "Apple",
    "98:EC:5F": "Apple",
    "98:EE:8A": "Apple",
    "98:F0:03": "Apple",
    "98:F1:70": "Apple",
    "98:F2:4B": "Apple",
    "98:F4:50": "Apple",
    "98:F6:21": "Apple",
    "98:F7:88": "Apple",
    "98:F8:35": "Apple",
    "98:F9:87": "Apple",
    "98:FA:E3": "Apple",
    "98:FB:E7": "Apple",
    "98:FC:11": "Apple",
    "98:FD:1D": "Apple",
    "98:FE:27": "Apple",
    "98:FF:20": "Apple",
    # 其他常见厂商
    "00:1A:A0": "Dell",
    "00:1E:C9": "Dell",
    "00:21:CC": "Dell",
    "00:22:19": "Dell",
    "00:23:AE": "Dell",
    "00:24:E8": "Dell",
    "00:50:56": "VMware",
    "00:0C:29": "VMware",
    "00:05:69": "VMware",
    "00:1C:14": "VMware",
    "00:1C:42": "Parallels",
    "00:1C:B3": "Samsung",
    "00:1E:75": "Samsung",
    "00:25:56": "Samsung",
    "00:26:37": "Samsung",
    "00:1D:0F": "Cisco",
    "00:1B:D5": "Cisco",
    "00:1E:BD": "Cisco",
    "00:22:BD": "Cisco",
    "00:23:EB": "Cisco",
    "00:25:B5": "Cisco",
    "00:26:0B": "Cisco",
    "00:50:56": "Cisco",
    "00:16:3E": "Xen",
    "52:54:00": "QEMU/KVM",
    "08:00:27": "VirtualBox",
}

# MAC 地址格式
MAC_FORMATS = {
    "colon": "xx:xx:xx:xx:xx:xx",      # 00:11:22:33:44:55
    "hyphen": "xx-xx-xx-xx-xx-xx",      # 00-11-22-33-44-55
    "dot": "xxxx.xxxx.xxxx",            # 0011.2233.4455
    "no_separator": "xxxxxxxxxxxx",      # 001122334455
}

# =============================================================================
# 网络接口名称常量
# =============================================================================

# 常见网络接口名称
INTERFACE_NAMES = [
    # 以太网接口
    "eth0", "eth1", "eth2", "eth3", "eth4",
    # 无线接口
    "wlan0", "wlan1", "wlan2",
    # 新版命名规则
    "enp0s3", "enp0s8", "enp2s0",
    "wlp2s0", "wlp3s0",
    # 绑定接口
    "bond0", "bond1",
    # 网桥
    "br0", "br1", "docker0", "virbr0",
    # 回环
    "lo",
    # VPN
    "tun0", "tun1", "tap0", "tap1",
    # 虚拟
    "veth0", "veth1",
]

# 接口名称前缀
INTERFACE_PREFIXES = {
    "ethernet": ["eth", "en"],
    "wireless": ["wlan", "wl"],
    "bond": ["bond"],
    "bridge": ["br", "virbr"],
    "loopback": ["lo"],
    "tunnel": ["tun", "tap"],
    "virtual": ["veth"],
}
