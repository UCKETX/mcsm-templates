#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import aiohttp
import json
from datetime import datetime
from src.utils.database import available_downloads


class MarketGenerator:
    def __init__(self, api_base_url="http://127.0.0.1:4523"):
        self.api_base_url = api_base_url
        self.market_data = {
            "languages": [],
            "packages": []
        }
    
    async def fetch_json(self, session, url):
        """异步获取JSON数据"""
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                return None
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None
    
    async def get_core_data(self, session, core_type):
        """获取指定核心的所有数据"""
        print(f"Processing {core_type}...")
        
        # 获取MC版本列表
        versions_url = f"{self.api_base_url}/core/{core_type}"
        versions_data = await self.fetch_json(session, versions_url)
        
        if not versions_data or not versions_data.get('data', {}).get('versions'):
            print(f"No versions found for {core_type}")
            return []
        
        mc_versions = versions_data['data']['versions']
        packages = []
        
        # 为每个MC版本获取最新构建
        for mc_version in mc_versions:  # 获取所有版本
            builds_url = f"{self.api_base_url}/core/{core_type}/{mc_version}"
            builds_data = await self.fetch_json(session, builds_url)
            
            if not builds_data or not builds_data.get('data', {}).get('builds'):
                continue
            
            builds = builds_data['data']['builds']
            if not builds:
                continue
            
            # 获取最新构建的详细信息
            latest_build = builds[0]  # 假设已按版本排序
            build_url = f"{self.api_base_url}/core/{core_type}/{mc_version}/{latest_build}"
            build_data = await self.fetch_json(session, build_url)
            
            if not build_data or not build_data.get('data'):
                continue
            
            build_info = build_data['data']['build']
            
            # 生成包信息
            package = self.create_package(core_type, mc_version, latest_build, build_info)
            if package:
                packages.append(package)
        
        return packages
    
    def create_package(self, core_type, mc_version, core_version, build_info):
        """创建包信息，严格按照MCSM市场格式"""
        try:
            # 根据核心类型确定分类和运行时
            category, runtime, game_type = self.get_core_category(core_type)
            
            # 生成包数据，严格按照原始market.json格式
            package = {
                "language": core_type.lower(),  # 使用核心名作为语言标识
                "platform": "ALL",
                "description": f"{core_type} {mc_version} 服务端 - 构建版本 {core_version}，自动下载最新版本",
                "image": "https://mcsmanager.oss-cn-guangzhou.aliyuncs.com/package-images/minecraft.webp",
                "gameType": game_type,
                "title": f"{core_type} {mc_version}",
                "category": category,
                "runtime": runtime,
                "hardware": "RAM 4G+",
                "size": "自动下载",
                "remark": f"最新 {core_type} 构建版本，支持 Minecraft {mc_version}",
                "targetLink": build_info.get('download_url', ''),
                "author": f"{core_type} 开发团队",
                "setupInfo": self.get_setup_info(core_type, mc_version, core_version, build_info)
            }
            
            return package
        except Exception as e:
            print(f"Error creating package for {core_type} {mc_version}: {e}")
            return None
    
    def get_core_category(self, core_type):
        """根据核心类型获取分类信息 - 所有服务端都归类到 mc-banner"""
        # 根据核心类型确定运行时要求
        runtime_requirements = {
            'Paper': 'Java 21+',
            'Purpur': 'Java 21+',
            'Spigot': 'Java 17+',
            'Fabric': 'Java 17+',
            'Forge': 'Java 17+',
            'Folia': 'Java 21+',
            'Velocity': 'Java 17+',
            'Waterfall': 'Java 17+',
            'BungeeCord': 'Java 17+',
            'Mohist': 'Java 17+',
            'CatServer': 'Java 17+',
            'Arclight': 'Java 17+',
            'Banner': 'Java 17+',
            'Leaves': 'Java 21+',
            'Pufferfish': 'Java 17+',
            'SpongeVanilla': 'Java 17+',
            'SpongeForge': 'Java 17+',
            'Vanilla': 'Java 17+',
            'Craftbukkit': 'Java 17+',
            'NukkitX': 'Java 17+',
            'Geyser': 'Java 17+',
            'Floodgate': 'Java 17+',
        }
        
        runtime = runtime_requirements.get(core_type, 'Java 17+')
        # 所有服务端版本选择都归类到 mc-banner
        return ('mc-banner', runtime, 'Minecraft')
    
    def get_setup_info(self, core_type, mc_version, core_version, build_info=None):
        """生成启动配置信息，按照MCSM格式"""
        jar_name = f"{core_type.lower()}-{mc_version}-{core_version}.jar"
        
        # 特殊处理Vanilla文件名
        if core_type == 'Vanilla':
            jar_name = "server.jar"
        # 特殊处理Fabric文件名
        elif core_type == 'Fabric' and build_info and 'download_url' in build_info:
            # 从下载URL中提取正确的文件名
            download_url = build_info['download_url']
            # Fabric URL格式: https://meta.fabricmc.net/v2/versions/loader/{mc_version}/{loader_version}/{launcher_version}/server/jar
            # 实际文件名格式: fabric-server-mc.{mc_version}-loader.{loader_version}-launcher.{launcher_version}.jar
            url_parts = download_url.split('/')
            if len(url_parts) >= 8:
                mc_ver = url_parts[6]  # mc_version
                loader_ver = url_parts[7]  # loader_version  
                launcher_ver = url_parts[8]  # launcher_version
                jar_name = f"fabric-server-mc.{mc_ver}-loader.{loader_ver}-launcher.{launcher_ver}.jar"
        
        setup_info = {
            "type": "minecraft/java",
            "startCommand": f"java -Xms2048M -Xmx4096M -jar {jar_name} nogui",
            "stopCommand": "stop",
            "updateCommand": "",
            "ie": "utf-8",
            "oe": "utf-8"
        }
        
        # 特殊处理某些核心类型
        if core_type in ['Forge']:
            # Forge文件名格式: forge-{mc_version}-{forge_version}-installer.jar
            forge_jar_name = f"forge-{mc_version}-{core_version}-installer.jar"
            setup_info["startCommand"] = f"java -Xms2048M -Xmx4096M -jar {forge_jar_name} --installServer"
            setup_info["updateCommand"] = f"java -jar {forge_jar_name} --installServer"
        elif core_type in ['BungeeCord', 'Waterfall', 'Velocity']:
            setup_info["type"] = "minecraft/java/proxy"
        elif core_type in ['NukkitX']:
            setup_info["type"] = "minecraft/bedrock"
        
        return setup_info
    
    def get_core_chinese_name(self, core_type):
        """获取核心类型的中文名称"""
        chinese_names = {
            'Paper': 'Paper 服务端',
            'Purpur': 'Purpur 服务端',
            'Spigot': 'Spigot 服务端',
            'Fabric': 'Fabric 服务端',
            'Forge': 'Forge 服务端',
            'Folia': 'Folia 服务端',
            'Velocity': 'Velocity 代理',
            'Waterfall': 'Waterfall 代理',
            'BungeeCord': 'BungeeCord 代理',
            'Mohist': 'Mohist 服务端',
            'CatServer': 'CatServer 服务端',
            'Arclight': 'Arclight 服务端',
            'Banner': 'Banner 服务端',
            'Leaves': 'Leaves 服务端',
            'Pufferfish': 'Pufferfish 服务端',
            'SpongeVanilla': 'SpongeVanilla 服务端',
            'SpongeForge': 'SpongeForge 服务端',
            'Vanilla': 'Vanilla 原版服务端',
            'Craftbukkit': 'CraftBukkit 服务端',
            'NukkitX': 'NukkitX 基岩版服务端',
            'Geyser': 'Geyser 互通代理',
            'Floodgate': 'Floodgate 互通插件',
        }
        return chinese_names.get(core_type, f'{core_type} 服务端')
    
    async def generate_market_data(self):
        """生成完整的市场数据"""
        print("Starting market data generation...")
        
        # 生成languages字段 - 每个核心作为一种语言，使用中文标签
        for core_type in available_downloads:
            self.market_data["languages"].append({
                "label": self.get_core_chinese_name(core_type),
                "value": core_type.lower(),
                "path": f"templates-{core_type.lower()}.json"
            })
        
        # 获取所有核心的包数据
        async with aiohttp.ClientSession() as session:
            all_packages = []
            
            # 并发获取所有核心数据
            tasks = []
            for core_type in available_downloads:
                task = asyncio.create_task(self.get_core_data(session, core_type))
                tasks.append(task)
            
            # 等待所有任务完成
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 收集所有包数据
            for result in results:
                if isinstance(result, list):
                    all_packages.extend(result)
                elif isinstance(result, Exception):
                    print(f"Task failed with exception: {result}")
            
            self.market_data["packages"] = all_packages
        
        print(f"Generated {len(all_packages)} packages for {len(available_downloads)} cores")
        return self.market_data
    
    async def save_to_file(self, filename="server.json"):
        """保存市场数据到文件"""
        market_data = await self.generate_market_data()
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(market_data, f, ensure_ascii=False, indent=2)
        
        print(f"Market data saved to {filename}")
        return filename


async def main():
    generator = MarketGenerator()
    await generator.save_to_file()


if __name__ == "__main__":
    asyncio.run(main())