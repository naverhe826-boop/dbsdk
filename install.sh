#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

PKG="dbsdk"
VERSION_FILE="data_builder/__init__.py"

get_version() {
    grep '^__version__' "$VERSION_FILE" | sed 's/.*"\(.*\)"/\1/'
}

set_version() {
    sed -i "s/^__version__ = .*/__version__ = \"$1\"/" "$VERSION_FILE"
}

cmd_list() {
    echo "当前源码版本: $(get_version)"
    pip show "$PKG" 2>/dev/null || echo "$PKG 未安装"
}

cmd_setup() {
    [ -n "$1" ] && set_version "$1"
    pip install -e . -q
    echo "$PKG $(get_version) installed"
}

cmd_remove() {
    pip uninstall "$PKG" -y 2>/dev/null && echo "$PKG removed" || echo "$PKG 未安装"
}

cmd_help() {
    cat <<EOF
Usage: ./install.sh <command> [version]

Commands:
  setup  [version]  安装到当前环境（editable），可选指定版本号
  list              查看当前版本及安装状态
  remove            卸载
  help              显示帮助
EOF
}

case "${1:-help}" in
    setup)    cmd_setup "$2" ;;
    list)     cmd_list ;;
    remove)   cmd_remove ;;
    help)     cmd_help ;;
    *)        echo "未知命令: $1"; cmd_help; exit 1 ;;
esac
