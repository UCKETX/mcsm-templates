# MCSM-Templates

为 [MCSManager](https://mcsmanager.com/) 提供 Minecraft 服务端模板源。接入后，可以在面板的应用市场按核心和 Minecraft 版本选择模板，例如 Paper、Fabric、Forge、Purpur 和 Pufferfish。实际可用版本以最新发布的 `server.json` 为准。

[最新发布](https://github.com/UCKETX/mcsm-templates/releases/latest) · [历史发布](https://github.com/UCKETX/mcsm-templates/releases) · [问题反馈](https://github.com/UCKETX/mcsm-templates/issues)

## 接入 MCSManager

1. 登录面板，打开 **设置 → 基本设置 → 实例模板配置**。
2. 填入以下地址并保存。

   ```text
   https://github.com/UCKETX/mcsm-templates/releases/latest/download/server.json
   ```

3. 打开 **应用市场**，选择所需的核心和版本，按模板提示创建实例。
4. 启动前确认运行实例的节点已安装该核心要求的 Java 版本，并检查启动命令中的 JAR 文件名和内存参数。首次启动若提示接受 Minecraft EULA，请阅读条款并按提示处理。

### 常见问题

| 现象 | 排查方法 |
| --- | --- |
| 应用市场无法加载 | 在运行面板的主机上执行 `curl -fL -o server.json https://github.com/UCKETX/mcsm-templates/releases/latest/download/server.json`，确认能下载模板索引。 |
| 能看到模板，但服务端下载失败 | 检查下载日志和对应模板的 `targetLink`，确认执行下载的主机能访问上游构建地址。 |
| 服务端启动报错 | 核对实例实际使用的 Java 版本、JAR 文件名和可用内存。Java 要求以对应核心和 Minecraft 版本的文档为准。 |

需要切回面板官方模板时，可使用 [MCSManager 官方模板源](https://script.mcsmanager.com/market.json)。面板操作可参考 [MCSManager 官方文档](https://docs.mcsmanager.com/)。

## 数据更新

GitHub Actions 每天北京时间 **08:00** 计划执行采集，也支持手动运行。流程从各核心上游获取构建数据，写入本地 SQLite，再导出 `server.json`。生成结果有变化时，流程会发布新的附件和变更说明。 [查看发布流程](.github/workflows/daily_release.yml)

如果某次采集临时漏掉 Pufferfish 条目，发布流程会补回上一版已有的条目。同一版本采到新构建时，以新构建为准。上一版附件下载失败或无法解析时，当次发布会中止。 [查看保留逻辑](preserve_pufferfish.py)

## 本地生成

以下命令适用于 Linux 和 macOS，使用 Python 3.12，与发布流程一致。

```bash
git clone https://github.com/UCKETX/mcsm-templates.git
cd mcsm-templates
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python main.py -i
.venv/bin/python main.py -u
.venv/bin/python main.py --server
```

API 启动后，保持该终端运行，在另一个终端进入仓库目录并执行以下命令。生成文件位于仓库根目录。

```bash
.venv/bin/python generate_market.py
```

运行回归测试可使用 `.venv/bin/python -m unittest discover -s tests`。

## 反馈与贡献

反馈模板问题时，请附上核心名称、Minecraft 版本、Release 标签和相关报错。欢迎通过 Issue 或 Pull Request 提交修正。 [提交 Issue](https://github.com/UCKETX/mcsm-templates/issues)

感谢 [MCSL-Sync-Backend](https://github.com/MCSLTeam/MCSL-Sync-Backend) 和 [mcsm-template-editor](https://github.com/Lirzh/mcsm-template-editor)。

## 许可证

本仓库采用 [GNU GPL v3](LICENSE)。各服务端核心及其构建适用各自的许可证。
