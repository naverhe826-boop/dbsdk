#!/usr/bin/env python
"""
总控脚本：运行所有 gen_ 开头的示例脚本

用法：
    python run_all.py           # 默认不运行 gen_llm.py
    python run_all.py -a        # 运行所有脚本（包括 gen_llm.py）
"""

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path


def find_gen_scripts(include_all: bool = False, include_openapi: bool = True, target_dirs: list[str] | None = None):
    """递归查找所有 gen_ 开头的脚本

    Args:
        include_all: 是否包含 gen_llm.py（默认 False）
        include_openapi: 是否包含 openapi 子目录中的脚本（默认 True）
        target_dirs: 指定要运行的目录列表（如 ["basic", "advanced"]），None 表示运行所有目录
    """
    examples_dir = Path(__file__).parent
    scripts = []

    # 定义可用的子目录及其优先级顺序
    all_subdirs = ["basic", "advanced", "structure", "schema_features", "integration", "config", "openapi"]

    # 如果指定了目标目录，使用指定的；否则使用默认配置
    if target_dirs:
        subdirs = [d for d in target_dirs if d in all_subdirs]
        # 如果 openapi 不在目标列表中，则不包含
        include_openapi = "openapi" in subdirs
    else:
        subdirs = ["basic", "advanced", "structure", "schema_features", "integration", "config"]
        if include_openapi:
            subdirs.append("openapi")

    # 遍历每个子目录
    for subdir in subdirs:
        subdir_path = examples_dir / subdir
        if subdir_path.is_dir():
            # 查找该子目录下所有 gen_*.py 文件
            for script in sorted(subdir_path.glob("gen_*.py")):
                scripts.append(script)

    # 默认排除 gen_llm.py
    if not include_all:
        scripts = [s for s in scripts if s.name != "gen_llm.py"]

    return scripts


def run_script(script_path: Path) -> tuple[bool, str, float]:
    """
    运行单个脚本
    
    返回: (是否成功, 错误信息, 执行时间秒)
    """
    script_name = script_path.name
    
    try:
        start_time = time.time()
        
        # 使用 subprocess 执行脚本，确保 __name__ == "__main__" 被触发
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=60,
            cwd=script_path.parent
        )
        
        elapsed = time.time() - start_time
        
        if result.returncode == 0:
            # 打印脚本输出
            if result.stdout.strip():
                print(result.stdout)
            return True, "", elapsed
        else:
            error_msg = result.stderr.strip() if result.stderr else "未知错误"
            return False, error_msg, elapsed
        
    except subprocess.TimeoutExpired:
        elapsed = time.time() - start_time
        return False, "执行超时（60秒）", elapsed
    except Exception as e:
        elapsed = time.time() - start_time
        return False, str(e), elapsed


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="运行所有示例脚本")
    parser.add_argument("-a", "--all", action="store_true",
                        help="包含 gen_llm.py（默认不运行）")
    parser.add_argument("-d", "--dir", nargs="+", metavar="DIR",
                        help="指定要运行的目录（如：basic advanced）")
    parser.add_argument("--no-openapi", action="store_true",
                        help="不运行 openapi 子目录中的脚本")
    args = parser.parse_args()

    # 确定是否包含 openapi 脚本
    include_openapi = not args.no_openapi

    print("=" * 70)
    print("运行所有示例脚本")
    if args.all:
        print("（包含 gen_llm.py）")
    if include_openapi:
        print("（包含 openapi/ 子目录）")
    print("=" * 70)

    scripts = find_gen_scripts(include_all=args.all, include_openapi=include_openapi, target_dirs=args.dir)
    total = len(scripts)
    passed = 0
    failed = 0
    failed_scripts = []
    
    total_time = 0.0
    for i, script_path in enumerate(scripts, 1):
        # 显示相对路径（如 basic/gen_enum.py）
        examples_dir = Path(__file__).parent
        rel_path = script_path.relative_to(examples_dir)
        print(f"\n[{i}/{total}] 运行: {rel_path}")
        print("-" * 50)
        
        success, error, elapsed = run_script(script_path)
        total_time += elapsed
        
        if success:
            print(f"✅ {rel_path} - 成功 ({elapsed:.3f}s)")
            passed += 1
        else:
            print(f"❌ {rel_path} - 失败 ({elapsed:.3f}s)")
            print(f"   错误: {error}")
            failed += 1
            failed_scripts.append(str(rel_path))
    
    # 汇总结果
    print("\n" + "=" * 70)
    print("测试汇总")
    print("=" * 70)
    print(f"总脚本数: {total}")
    print(f"通过: {passed} ✅")
    print(f"失败: {failed} ❌")
    print(f"总耗时: {total_time:.3f}s")
    
    if failed > 0:
        print(f"\n⚠️  失败脚本列表:")
        for name in failed_scripts:
            print(f"   - {name}")
        sys.exit(1)
    else:
        print("\n🎉 所有脚本执行成功！")
        sys.exit(0)


if __name__ == "__main__":
    main()
