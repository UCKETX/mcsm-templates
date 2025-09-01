# MCSM-Templates

MCSManager-Minecraft服务端快速配置模板

## 简介

- **名字**：MCSM-Templates
- **作者**：[UCKETX](https://github.com/UCKETX)
- **内容概括**：MCSM-MC服务端快速配置模板
- **协议**：MIT
- **最后更新**：2025.8.5
- **关于AI**：人工收集，如有错误请联系作者。
- **版权**：侵权必删

## 使用方法

#### 配置方法：

1. 打开并登录你的 MCSM 面板

2. 进入设置

3. 在 基本设置 - 实例模板配置 中填写 

   ```
     https://github.com/UCKETX/mcsm-templates/releases/latest/download/server.json
   ```

#### 使用方法：

1. 点击 `应用市场`

2. 选择适合的服务器版本和类型

3. 下载对应的服务器文件

4. 确保已安装符合要求的 JDK 版本

5. 使用提供的启动命令运行服务器：

   ```
   # 示例启动命令
   java -Xms4096M -Xmx4096M -jar server.jar nogui
   ```

##### 小贴士：

如果出现：

```
网络故障中
很抱歉，无法获取最新预设整合包列表，可能是您的网络问题或服务器正在维护中。
```

点击 `知道了` 即可。

#### 其他模板：

官方模板：

```
https://script.mcsmanager.com/market.json
```

本模板的 `bgithub.xyz` 加速：

```
https://raw.bgithub.xyz/UCKETX/mcsm-templates/releases/latest/download/server.json
```

## 功能特点

- 支持超多种 Minecraft 版本（1.2.5 - 1.21.8）！！！
- 提供超多种服务器核心选择（Paper、Forge等）
- 包含预配置的整合包服务端（不过网络问题好像不能用）

## 使用要求

- JDK 版本要求：
  - 1.21.x 版本：JDK 21+
  - 1.20.x 版本：JDK 17+
  - 1.16.x 及更早版本：JDK 8+
- 内存要求：最低 2GB RAM
- 建议使用 SSD 存储以获得更好性能

## 注意事项

- 首次启动服务器需要同意 EULA 协议
- 建议定期备份服务器数据
- 根据实际硬件配置调整内存分配
- 确保使用正确版本的 JDK

## 技术支持

如果遇到问题或需要帮助，可以：

- 如果你在使用过程中遇到本项目的问题或 Bug，可以前往 [项目的 Issues 页面](https://github.com/UCKETX/mcsm-templates/issues) 提交反馈，我们会 ~~尽快~~ 处理。
- 查看对应版本的官方文档(https://docs.mcsmanager.com/)
- 参考社区讨论
- 提交 Issue 反馈问题

## 贡献

欢迎提交新的服务器配置或改进建议，让我们一起完善这个项目！

## 鸣谢

- [MCSL-Sync-Backend](https://github.com/MCSLTeam/MCSL-Sync-Backend)
- [mcsm-template-editor](https://github.com/Lirzh/mcsm-template-editor/tree/main)

## 许可证

本项目遵循 GPL-3.0 协议，详情请参见 LICENSE 文件。
