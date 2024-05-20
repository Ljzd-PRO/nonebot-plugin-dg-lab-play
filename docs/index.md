<h1 align="center">
  DG-Lab-Play
</h1>

<p align="center">
  nonebot2 机器人插件 - 在群里和大家一起玩郊狼吧！
</p>

<p align="center">
  <a href="https://www.codefactor.io/repository/github/ljzd-pro/nonebot-plugin-dg-lab-play">
    <img src="https://www.codefactor.io/repository/github/ljzd-pro/nonebot-plugin-dg-lab-play/badge" alt="CodeFactor" />
  </a>

  <a href='https://dg-lab-play.readthedocs.io/'>
    <img src='https://readthedocs.org/projects/dg-lab-play/badge/?version=latest' alt='Documentation Status' />
  </a>

  <a href="https://github.com/Ljzd-PRO/nonebot-plugin-dg-lab-play/activity">
    <img src="https://img.shields.io/github/last-commit/Ljzd-PRO/nonebot-plugin-dg-lab-play/master" alt="Last Commit"/>
  </a>

  <a href="./LICENSE">
    <img src="https://img.shields.io/github/license/Ljzd-PRO/nonebot-plugin-dg-lab-play" alt="BSD 3-Clause"/>
  </a>

  <a href="https://pypi.org/project/nonebot-plugin-dg-lab-play" target="_blank">
    <img src="https://img.shields.io/github/v/release/Ljzd-PRO/nonebot-plugin-dg-lab-play?logo=python" alt="Version">
  </a>
</p>

## 💡 特性

- 通过该库可开发 Python 程序，接入 DG-Lab App
- 完全使用 asyncio 异步，并发执行各项操作
- 可部署第三方终端与 Socket 服务一体的服务端，降低部署复杂度和延迟
- 使用异步生成器、上下文管理器等，结合语言特性
- 通过 Pydantic, 枚举 管理消息结构和常量，便于开发

## 🚀 快速开始

### 🔨 安装

在您已经完成 nonebot 项目的创建和 nb-cli 的安装的前提下，\
在机器人项目下执行：
> 关于 nonebot 的安装和使用：https://nonebot.dev/docs/2.3.0/quick-start

```bash
nb plugin install nonebot-plugin-dg-lab-play
```

### ⬆️ 更新

```bash
nb plugin update nonebot-plugin-dg-lab-play
```

### ⚙️ 配置

!!! warning "注意"
    首次使用，必须更改 WebSocket 服务端配置，否则用户将可能无法连接

> nonebot 文档介绍：[dotenv 配置文件](https://nonebot.dev/docs/2.3.0/appendices/config#dotenv-%E9%85%8D%E7%BD%AE%E6%96%87%E4%BB%B6)