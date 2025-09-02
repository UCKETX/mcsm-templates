#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import sys
from pathlib import Path


def load_json_file(file_path):
    """加载JSON文件，如果文件不存在返回空字典"""
    try:
        if Path(file_path).exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return {}


def analyze_changes(old_file, new_file):
    """分析两个JSON文件之间的变更"""
    old_data = load_json_file(old_file)
    new_data = load_json_file(new_file)
    
    # 统计信息
    stats = {
        'new_versions': 0,
        'updated_versions': 0,
        'removed_versions': 0,
        'new_cores': 0,
        'total_packages': len(new_data.get('packages', [])),
        'total_languages': 0  # 将在后面计算
    }
    
    # 创建旧数据的索引
    old_packages = {}
    for package in old_data.get('packages', []):
        key = f"{package.get('category', '')}-{package.get('title', '')}"
        old_packages[key] = package
    
    # 分析新数据
    new_versions = []
    updated_versions = []
    
    for package in new_data.get('packages', []):
        key = f"{package.get('category', '')}-{package.get('title', '')}"
        
        if key not in old_packages:
            # 新版本
            new_versions.append({
                'core': package.get('category', ''),
                'version': package.get('title', ''),
                'description': package.get('description', '')
            })
            stats['new_versions'] += 1
        else:
            # 检查是否有更新
            old_pkg = old_packages[key]
            if (package.get('targetLink') != old_pkg.get('targetLink') or 
                package.get('description') != old_pkg.get('description')):
                updated_versions.append({
                    'core': package.get('category', ''),
                    'version': package.get('title', ''),
                    'description': package.get('description', '')
                })
                stats['updated_versions'] += 1
    
    # 检查移除的版本
    removed_versions = []
    for key, package in old_packages.items():
        new_key_exists = any(
            f"{pkg.get('category', '')}-{pkg.get('title', '')}" == key 
            for pkg in new_data.get('packages', [])
        )
        if not new_key_exists:
            removed_versions.append({
                'core': package.get('category', ''),
                'version': package.get('title', ''),
                'description': package.get('description', '')
            })
            stats['removed_versions'] += 1
    
    # 检查新增的核心类型
    # 统计旧数据中 packages 的唯一 category 值
    old_categories = set()
    for package in old_data.get('packages', []):
        category = package.get('category', '')
        if category:
            old_categories.add(category)
    
    # 统计新数据中 packages 的唯一 category 值
    new_categories = set()
    for package in new_data.get('packages', []):
        category = package.get('category', '')
        if category:
            new_categories.add(category)
    
    # 计算新增的核心类型
    new_cores_list = list(new_categories - old_categories)
    stats['new_cores'] = len(new_cores_list)
    
    # 更新支持核心总数
    stats['total_languages'] = len(new_categories)
    
    # 生成发布说明
    release_notes = generate_release_notes(stats, new_versions, updated_versions, removed_versions, new_cores_list)
    
    return stats, release_notes


def generate_release_notes(stats, new_versions, updated_versions, removed_versions, new_cores):
    """生成发布说明"""
    from datetime import datetime
    
    notes = []
    notes.append(f"# 🎮 MCSL 数据源更新 - {datetime.now().strftime('%Y-%m-%d')}")
    notes.append("")
    notes.append("## 📊 更新统计")
    notes.append(f"- 📦 总包数量: {stats['total_packages']}")
    notes.append(f"- 🏷️ 支持核心: {stats['total_languages']}")
    notes.append(f"- ✨ 新增版本: {stats['new_versions']}")
    notes.append(f"- 🔄 更新版本: {stats['updated_versions']}")
    notes.append(f"- ❌ 移除版本: {stats['removed_versions']}")
    notes.append(f"- 🆕 新增核心: {stats['new_cores']}")
    notes.append("")
    
    if new_cores:
        notes.append("## 🆕 新增核心类型")
        for core in new_cores:
            notes.append(f"- {core}")
        notes.append("")
    
    if new_versions:
        notes.append("## ✨ 新增版本")
        # 按核心类型分组
        cores_dict = {}
        for version in new_versions:
            core = version['core']
            if core not in cores_dict:
                cores_dict[core] = []
            cores_dict[core].append(version)
        
        for core, versions in sorted(cores_dict.items()):
            notes.append(f"### {core.upper()}")
            for version in versions[:5]:  # 限制显示数量
                notes.append(f"- {version['version']}")
            if len(versions) > 5:
                notes.append(f"- ... 以及其他 {len(versions) - 5} 个版本")
            notes.append("")
    
    if updated_versions:
        notes.append("## 🔄 更新版本")
        cores_dict = {}
        for version in updated_versions:
            core = version['core']
            if core not in cores_dict:
                cores_dict[core] = []
            cores_dict[core].append(version)
        
        for core, versions in sorted(cores_dict.items()):
            notes.append(f"### {core.upper()}")
            for version in versions[:3]:  # 限制显示数量
                notes.append(f"- {version['version']}")
            if len(versions) > 3:
                notes.append(f"- ... 以及其他 {len(versions) - 3} 个版本")
            notes.append("")
    
    if removed_versions:
        notes.append("## ❌ 移除版本")
        for version in removed_versions[:10]:  # 限制显示数量
            notes.append(f"- {version['core'].upper()}: {version['version']}")
        if len(removed_versions) > 10:
            notes.append(f"- ... 以及其他 {len(removed_versions) - 10} 个版本")
        notes.append("")
    
    notes.append("---")
    notes.append("*此数据源包含最新的 Minecraft 服务端核心版本信息，支持 MCSM 面板自动下载和部署。*")
    
    return "\n".join(notes)


def main():
    """主函数"""
    if len(sys.argv) != 3:
        print("Usage: python analyze_changes.py <old_file> <new_file>")
        sys.exit(1)
    
    old_file = sys.argv[1]
    new_file = sys.argv[2]
    
    stats, release_notes = analyze_changes(old_file, new_file)
    
    # 输出统计信息
    print(f"NEW_VERSIONS={stats['new_versions']}")
    print(f"UPDATED_VERSIONS={stats['updated_versions']}")
    print(f"REMOVED_VERSIONS={stats['removed_versions']}")
    print(f"NEW_CORES={stats['new_cores']}")
    print(f"TOTAL_PACKAGES={stats['total_packages']}")
    
    # 保存发布说明
    with open('release_notes.md', 'w', encoding='utf-8') as f:
        f.write(release_notes)
    
    print("Release notes saved to release_notes.md")


if __name__ == "__main__":
    main()