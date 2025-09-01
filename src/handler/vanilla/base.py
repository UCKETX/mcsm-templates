from datetime import datetime
from ...utils import SyncLogger, get_json, update_database


class VanillaLoader:
    def __init__(self):
        self.core_type = "Vanilla"
        self.version_manifest_url = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"
    
    async def load_versions(self):
        """从Mojang官方API加载所有版本信息"""
        try:
            # 获取版本清单
            manifest_data = await get_json(self.version_manifest_url)
            if not manifest_data:
                SyncLogger.error(f"{self.core_type} | Failed to fetch version manifest")
                return
            
            versions = {}
            
            # 处理所有release版本
            for version_info in manifest_data.get('versions', []):
                if version_info.get('type') == 'release':
                    version_id = version_info.get('id')
                    release_time = version_info.get('releaseTime')
                    version_url = version_info.get('url')
                    
                    if not all([version_id, release_time, version_url]):
                        continue
                    
                    # 获取具体版本的详细信息
                    version_data = await get_json(version_url)
                    if not version_data:
                        SyncLogger.warning(f"{self.core_type} | Failed to fetch version data for {version_id}")
                        continue
                    
                    # 获取服务端下载链接
                    downloads = version_data.get('downloads', {})
                    server_info = downloads.get('server')
                    
                    if not server_info or not server_info.get('url'):
                        SyncLogger.warning(f"{self.core_type} | No server download found for version {version_id}")
                        continue
                    
                    # 转换时间格式
                    try:
                        sync_time = datetime.fromisoformat(release_time.replace('Z', '+00:00')).isoformat() + 'Z'
                    except Exception as e:
                        SyncLogger.warning(f"{self.core_type} | Failed to parse release time for {version_id}: {e}")
                        sync_time = datetime.now().isoformat() + 'Z'
                    
                    versions[version_id] = [{
                        "sync_time": sync_time,
                        "download_url": server_info.get('url'),
                        "core_type": self.core_type,
                        "mc_version": version_id,
                        "core_version": "Official",
                        "sha1": server_info.get('sha1', ''),
                        "size": server_info.get('size', 0)
                    }]
                    
                    SyncLogger.info(f"{self.core_type} | Loaded version {version_id}")
            
            # 保存数据到数据库
            await self.save_data(versions)
            
        except Exception as e:
            SyncLogger.error(f"{self.core_type} | Error loading versions: {e}")
    
    async def save_data(self, data_dict: dict):
        """保存版本数据到数据库"""
        for mc_version, builds in data_dict.items():
            update_database("runtime", self.core_type, mc_version, builds=builds)
        SyncLogger.success(f"{self.core_type} | All versions were loaded. Total: {len(data_dict)} versions")