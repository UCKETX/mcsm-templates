class MinecraftVersion(object):
    def __init__(self, version: str) -> None:
        self.version_str = version
        try:
            self.major, self.minor, self.patch = self.serialize(version)
        except (ValueError, IndexError):
            # 处理不规范的版本号格式
            parts = version.replace("v", "").split(".")
            self.major = int(parts[0]) if len(parts) > 0 and parts[0].isdigit() else 0
            self.minor = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
            self.patch = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 0

    def serialize(self, version) -> tuple[int, int, int]:
        parts = version.replace("v", "").split(".")
        if len(parts) < 3:
            parts.extend(["0"] * (3 - len(parts)))
        return tuple([int(i) for i in parts[:3]])

    def __str__(self) -> str:
        return ".".join([str(self.major), str(self.minor), str(self.patch)])
    
    def __lt__(self, other):
        if not isinstance(other, MinecraftVersion):
            other = MinecraftVersion(str(other))
        return (self.major, self.minor, self.patch) < (other.major, other.minor, other.patch)
    
    def __le__(self, other):
        if not isinstance(other, MinecraftVersion):
            other = MinecraftVersion(str(other))
        return (self.major, self.minor, self.patch) <= (other.major, other.minor, other.patch)
    
    def __gt__(self, other):
        if not isinstance(other, MinecraftVersion):
            other = MinecraftVersion(str(other))
        return (self.major, self.minor, self.patch) > (other.major, other.minor, other.patch)
    
    def __ge__(self, other):
        if not isinstance(other, MinecraftVersion):
            other = MinecraftVersion(str(other))
        return (self.major, self.minor, self.patch) >= (other.major, other.minor, other.patch)
    
    def __eq__(self, other):
        if not isinstance(other, MinecraftVersion):
            other = MinecraftVersion(str(other))
        return (self.major, self.minor, self.patch) == (other.major, other.minor, other.patch)
    
    def __ne__(self, other):
        return not self.__eq__(other)


def sort_versions_descending(versions: list[str]) -> list[str]:
    """
    对版本号列表进行降序排序
    
    Args:
        versions: 版本号字符串列表
        
    Returns:
        降序排序后的版本号列表
    """
    if not versions:
        return []
    
    # 检查是否为 Minecraft 版本格式（包含点号）
    has_minecraft_versions = any('.' in v and not v.startswith('build') for v in versions)
    
    if has_minecraft_versions:
        try:
            # 尝试使用 MinecraftVersion 进行排序
            version_objects = [MinecraftVersion(v) for v in versions]
            sorted_objects = sorted(version_objects, reverse=True)
            return [str(v) for v in sorted_objects]
        except Exception:
            pass
    
    # 尝试数字排序（适用于构建版本）
    try:
        import re
        def extract_number(version_str):
            # 提取版本字符串中的数字
            numbers = re.findall(r'\d+', version_str)
            if numbers:
                return int(numbers[-1])  # 使用最后一个数字
            return 0
        
        return sorted(versions, key=extract_number, reverse=True)
    except Exception:
        # 最后备选：字符串排序
        return sorted(versions, reverse=True)
