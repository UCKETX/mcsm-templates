import sqlite3
from .logger import SyncLogger
from .minecraft import sort_versions_descending

available_downloads = [
    "Arclight",
    "Lightfall",
    "LightfallClient",
    "Banner",
    "Mohist",
    "Spigot",
    "BungeeCord",
    "Leaves",
    "Pufferfish",
    "Pufferfish+",
    "Pufferfish+Purpur",
    "SpongeForge",
    "SpongeVanilla",
    "Paper",
    "Folia",
    "Travertine",
    "Velocity",
    "Waterfall",
    "Purpur",
    "Purformance",
    "CatServer",
    "Craftbukkit",
    "Vanilla",
    "Fabric",
    "Forge",
    "Akarin",
    "NukkitX",
    "Thermos",
    "Contigo",
    "Luminol",
    "LightingLuminol",
    "Geyser",
    "Floodgate",
]


def init_database() -> None:
    for core_type in available_downloads:
        with sqlite3.connect(f"data/runtime/{core_type}.db"):
            pass


async def get_mc_versions(database_type: str, core_type: str) -> list[str]:
    with sqlite3.connect(f"data/{database_type}/{core_type}.db") as core:
        cursor = core.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        version_list = [row[0] for row in cursor.fetchall()]
        try:
            version_list = sort_versions_descending(version_list)
        except Exception:
            # 如果版本排序失败，使用字符串降序排序作为备选
            version_list = sorted(version_list, reverse=True)
        return version_list


async def get_core_versions(
    database_type: str, core_type: str, mc_version: str
) -> list[str]:
    with sqlite3.connect(f"data/{database_type}/{core_type}.db") as core:
        cursor = core.cursor()
        cursor.execute(f"SELECT core_version FROM '{mc_version}' ORDER BY core_version")
        version_list = [row[0] for row in cursor.fetchall()]
        try:
            version_list = sort_versions_descending(version_list)
        except Exception:
            # 如果版本排序失败，使用字符串降序排序作为备选
            version_list = sorted(version_list, reverse=True)
        return version_list


async def get_specified_core_data(
    database_type: str, core_type: str, mc_version: str, core_version: str
) -> dict[str, str]:
    with sqlite3.connect(f"data/{database_type}/{core_type}.db") as core:
        cursor = core.cursor()
        cursor.execute(
            f"SELECT * FROM '{mc_version}' WHERE core_version='{core_version}'"
        )
        columns = [column[0] for column in cursor.description]
        core_data = [dict(zip(columns, row)) for row in cursor.fetchall()][0]
        return core_data


@SyncLogger.catch
def update_database(
    database_type: str, core_type: str, mc_version: str, builds: list
) -> None:
    with sqlite3.connect(f"data/{database_type}/{core_type}.db") as database:
        cursor = database.cursor()
        try:
            cursor.execute(
                f"""
                    CREATE TABLE "{mc_version}" (
                        sync_time TEXT,
                        download_url TEXT,
                        core_type TEXT,
                        mc_version TEXT,
                        core_version TEXT
                    )
                    """
            )
        except sqlite3.OperationalError:
            pass
        
        # 统计更新和插入的数量
        updated_count = 0
        inserted_count = 0
        
        # 增量更新逻辑：检查每个构建是否已存在
        for build in builds:
            # 检查是否已存在相同的记录（基于 download_url 和 core_version）
            cursor.execute(
                f"""
                SELECT COUNT(*) FROM "{mc_version}" 
                WHERE download_url = ? AND core_version = ?
                """,
                (build['download_url'], build['core_version'])
            )
            exists = cursor.fetchone()[0] > 0
            
            if exists:
                # 更新现有记录的 sync_time
                cursor.execute(
                    f"""
                    UPDATE "{mc_version}" 
                    SET sync_time = ?
                    WHERE download_url = ? AND core_version = ?
                    """,
                    (build['sync_time'], build['download_url'], build['core_version'])
                )
                updated_count += 1
            else:
                # 插入新记录
                cursor.execute(
                    f"""
                    INSERT INTO "{mc_version}" (sync_time, download_url, core_type, mc_version, core_version)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (build['sync_time'], build['download_url'], build['core_type'], 
                     build['mc_version'], build['core_version'])
                )
                inserted_count += 1
        
        # 去重逻辑（保留现有逻辑）
        cursor.execute(
            f"""
            DELETE FROM "{mc_version}"
            WHERE ROWID NOT IN (
                SELECT MIN(ROWID)
                FROM "{mc_version}"
                GROUP BY sync_time, download_url, core_type, mc_version, core_version
            )
            """
        )
        
        # 检查表是否为空，如果为空则删除表
        cursor.execute(f"SELECT COUNT(*) FROM '{mc_version}'")
        count = cursor.fetchone()[0]
        if count == 0:
            cursor.execute(f"DROP TABLE '{mc_version}'")
            SyncLogger.info(f"{core_type} | {mc_version} | Table dropped (empty)")
        else:
            SyncLogger.info(f"{core_type} | {mc_version} | Updated: {updated_count}, Inserted: {inserted_count}, Total: {count}")
        
        database.commit()


async def optimize_core_data(database_type: str = "runtime") -> None:
    for core_type in available_downloads:
        with sqlite3.connect(f"data/{database_type}/{core_type}.db") as core:
            cursor = core.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            table_list = [row[0] for row in cursor.fetchall()]
            for table_name in table_list:
                cursor.execute(
                    f"SELECT * FROM '{table_name}' ORDER BY ROWID DESC LIMIT 35"
                )
                rows = cursor.fetchall()
                cursor.execute(f"DELETE FROM '{table_name}'")
                cursor.executemany(
                    f"INSERT INTO '{table_name}' VALUES (?, ?, ?, ?, ?)", rows
                )
                cursor.execute(f"SELECT COUNT(*) FROM '{table_name}'")
                count = cursor.fetchone()[0]
                if count == 0:
                    cursor.execute(f"DROP TABLE '{table_name}'")
            core.commit()
