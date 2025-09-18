#!/usr/bin/env python3
"""
测试运行脚本
用于运行所有测试用例
"""

import subprocess
import sys
import os

def run_tests():
    """运行所有测试"""
    print("🧪 开始运行测试套件...")
    
    # 确保在项目根目录
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    os.chdir(project_root)
    
    # 运行pytest
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/unit/",
        "tests/integration/",
        "-v",  # 详细输出
        "--tb=short",  # 简短的错误追踪
        "--color=yes",  # 彩色输出
        "--durations=10",  # 显示最慢的10个测试
    ]
    
    try:
        result = subprocess.run(cmd, check=True)
        print("\n✅ 所有测试通过！")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ 测试失败，退出码: {e.returncode}")
        return False
    except Exception as e:
        print(f"\n❌ 运行测试时出错: {str(e)}")
        return False

def run_specific_test(test_file):
    """运行特定测试文件"""
    print(f"🧪 运行特定测试: {test_file}")
    
    cmd = [
        sys.executable, "-m", "pytest",
        f"tests/unit/{test_file}",
        f"tests/integration/{test_file}",
        "-v",
        "--tb=short",
        "--color=yes"
    ]
    
    try:
        result = subprocess.run(cmd, check=True)
        print(f"\n✅ {test_file} 测试通过！")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ {test_file} 测试失败，退出码: {e.returncode}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # 运行特定测试文件
        test_file = sys.argv[1]
        success = run_specific_test(test_file)
    else:
        # 运行所有测试
        success = run_tests()
    
    sys.exit(0 if success else 1)
