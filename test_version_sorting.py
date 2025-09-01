#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
sys.path.append('src')

from src.utils.minecraft import MinecraftVersion, sort_versions_descending

def test_minecraft_version_comparison():
    """测试 MinecraftVersion 类的比较功能"""
    print("=== 测试 MinecraftVersion 比较功能 ===")
    
    # 测试版本比较
    v1 = MinecraftVersion("1.21.4")
    v2 = MinecraftVersion("1.21.3")
    v3 = MinecraftVersion("1.20.6")
    v4 = MinecraftVersion("1.19.2")
    
    print(f"1.21.4 > 1.21.3: {v1 > v2}")
    print(f"1.21.3 > 1.20.6: {v2 > v3}")
    print(f"1.20.6 > 1.19.2: {v3 > v4}")
    print(f"1.19.2 < 1.21.4: {v4 < v1}")
    
    # 测试相等比较
    v5 = MinecraftVersion("1.21.4")
    print(f"1.21.4 == 1.21.4: {v1 == v5}")
    
    print()

def test_version_sorting():
    """测试版本排序功能"""
    print("=== 测试版本排序功能 ===")
    
    # 测试 Minecraft 版本排序
    mc_versions = ["1.19.2", "1.21.4", "1.20.6", "1.21.3", "1.18.2", "1.20.1"]
    print(f"原始版本列表: {mc_versions}")
    
    sorted_versions = sort_versions_descending(mc_versions)
    print(f"降序排序后: {sorted_versions}")
    
    # 测试构建版本排序
    build_versions = ["123", "456", "789", "100", "999"]
    print(f"\n原始构建版本: {build_versions}")
    
    sorted_builds = sort_versions_descending(build_versions)
    print(f"降序排序后: {sorted_builds}")
    
    # 测试混合版本格式
    mixed_versions = ["1.21.4-rc1", "1.21.4", "1.21.3", "1.21.4-pre1"]
    print(f"\n混合版本格式: {mixed_versions}")
    
    try:
        sorted_mixed = sort_versions_descending(mixed_versions)
        print(f"降序排序后: {sorted_mixed}")
    except Exception as e:
        print(f"排序失败，使用字符串排序: {sorted(mixed_versions, reverse=True)}")
    
    print()

def test_edge_cases():
    """测试边界情况"""
    print("=== 测试边界情况 ===")
    
    # 空列表
    empty_list = []
    print(f"空列表排序: {sort_versions_descending(empty_list)}")
    
    # 单个版本
    single_version = ["1.21.4"]
    print(f"单个版本排序: {sort_versions_descending(single_version)}")
    
    # 相同版本
    same_versions = ["1.21.4", "1.21.4", "1.21.4"]
    print(f"相同版本排序: {sort_versions_descending(same_versions)}")
    
    # 不规范版本号
    irregular_versions = ["1.21", "1.21.4.1", "1.21.4", "v1.21.3"]
    print(f"不规范版本号: {irregular_versions}")
    
    try:
        sorted_irregular = sort_versions_descending(irregular_versions)
        print(f"排序结果: {sorted_irregular}")
    except Exception as e:
        print(f"排序失败: {e}")
        print(f"使用字符串排序: {sorted(irregular_versions, reverse=True)}")
    
    print()

def main():
    """主测试函数"""
    print("开始测试版本排序逻辑...\n")
    
    test_minecraft_version_comparison()
    test_version_sorting()
    test_edge_cases()
    
    print("版本排序测试完成！")

if __name__ == "__main__":
    main()