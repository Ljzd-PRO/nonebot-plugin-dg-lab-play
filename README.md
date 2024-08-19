<h1 align="center">
  DG-Lab-Play
</h1>

<p align="center">
  nonebot2 机器人插件 - ⚡ 在群里和大家一起玩郊狼吧！⚡
</p>

<p align="center">
  <a href="https://dg-lab-play.readthedocs.io">📖 完整文档</a>
</p>

<p align="center">
  <a href="https://www.codefactor.io/repository/github/ljzd-pro/nonebot-plugin-dg-lab-play">
    <img src="https://www.codefactor.io/repository/github/ljzd-pro/nonebot-plugin-dg-lab-play/badge" alt="CodeFactor" />
  </a>

  <a href="https://github.com/Ljzd-PRO/nonebot-plugin-dg-lab-play/actions/workflows/plugin-test.yml" target="_blank">
    <img alt="Test Result" src="https://img.shields.io/github/actions/workflow/status/Ljzd-PRO/nonebot-plugin-dg-lab-play/plugin-test.yml">
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

- 兼容大部分 nonebot 适配器
  - OneBot v11, OneBot v12, Kaiheila, Telegram, Feishu, Red, DoDo
- 支持多个郊狼玩家同时连接
- DG-Lab App Socket 服务端可选择本地搭建或连接远程服务器
- 命令和回复文本均可自定义
- 支持以下功能：
    - 🕹️查看当前郊狼玩家
    - 🔺🔻增大/减小玩家通道强度
    - 🎲随机通道强度
    - ⤴️自定义波形（拼接波形）
    - 🎲随机波形
    - 🎲骰子玩法
    - ...

## 🔨 安装

### 🔨 安装

> 关于 nonebot 的安装和使用：[快速上手](https://nonebot.dev/docs/2.3.0/quick-start)

在您已经完成 nonebot 项目的创建和 nb-cli 脚手架的安装的前提下，\
在机器人项目下执行：

```bash
nb plugin install nonebot-plugin-dg-lab-play
```

### ⬆️ 更新

```bash
nb plugin update nonebot-plugin-dg-lab-play
```

## ⚙️ 配置

> [!Warning]
> 首次使用，必须更改 WebSocket 服务端配置，否则用户将可能无法连接

> [!Note]
> 更多配置内容参考 [插件配置](https://dg-lab-play.readthedocs.io/zh-cn/latest/config/guide/)

> nonebot 文档介绍：[dotenv 配置文件](https://nonebot.dev/docs/2.3.0/appendices/config#dotenv-%E9%85%8D%E7%BD%AE%E6%96%87%E4%BB%B6)

有两种配置 DG-Lab WebSocket 服务端的方法，分别为本地搭建和连接远程服务器，默认为本地搭建

### 📌（默认）采用本地搭建 WebSocket 服务端的方法

修改 nonebot 目录下的 `.env` 文件，参考如下：

#### 🔗（可选）设置本地服务端监听主机号和端口
```dotenv
# 本地搭建的服务端 host，默认为 0.0.0.0
DG_LAB_PLAY__WS_SERVER__LOCAL_SERVER_HOST=0.0.0.0
# 本地搭建的服务端监听端口，默认为 4567
DG_LAB_PLAY__WS_SERVER__LOCAL_SERVER_PORT=4567
```

#### ❗（必需）设置供 DG-Lab App 连接的本地 WebSocket 服务端 URI

```dotenv
# 生成二维码时，使用的本地服务端 URI（需要郊狼用户能够连接，即本机的公网地址）
# 首次使用，该配置必须更改，默认为本地环回地址，用户的 App 无法连接
# 普通连接为 ws://，SSL 加密连接为 wss://
DG_LAB_PLAY__WS_SERVER__LOCAL_SERVER_PUBLISH_URI="ws://my-server.net:4567"
```

#### 🔐（可选）设置 SSL 连接

```dotenv
# 是否启用 SSL 连接
DG_LAB_PLAY__WS_SERVER__LOCAL_SERVER_SECURE=True
# SSL 证书文件路径
# 若使用相对路径，起始位置为机器人项目目录
DG_LAB_PLAY__WS_SERVER__LOCAL_SERVER_SSL_CERT="/path/to/证书文件"
# SSL 私钥路径
# 若使用相对路径，起始位置为机器人项目目录
DG_LAB_PLAY__WS_SERVER__LOCAL_SERVER_SSL_KEY="/path/to/私钥文件"
# SSL 私钥密码
DG_LAB_PLAY__WS_SERVER__LOCAL_SERVER_SSL_PASSWORD=123456
```

📡 最后，记得完成对公网的端口转发等配置，确保用户能够连接本地搭建的 WebSocket 服务端。

### 📌（备选）采用连接远程 WebSocket 服务端的方法

修改 nonebot 目录下的 `.env` 文件，参考如下：

```dotenv
# 是否连接到远程 WebSocket 服务端
DG_LAB_PLAY__WS_SERVER__REMOTE_SERVER=True
# 远程服务端 URI
DG_LAB_PLAY__WS_SERVER__REMOTE_SERVER_URI="ws://my-server.net:8080"
```

## 🎉 开始使用

默认情况下，向机器人发送 `/郊狼玩法` 以查看完整帮助信息

命令和回复文本均可自定义，具体可参考
[`CommandTextConfig`](https://dg-lab-play.readthedocs.io/zh-cn/latest/config/command-text/#nonebot_plugin_dg_lab_play.config.CommandTextConfig), 
[`ReplyTextConfig`](https://dg-lab-play.readthedocs.io/zh-cn/latest/config/reply-text/#nonebot_plugin_dg_lab_play.config.ReplyTextConfig)

## 💡 更多

PyPI: https://pypi.org/project/nonebot-plugin-dg-lab-play/

### 是如何实现的郊狼控制？

本插件使用 [PyDGLab-WS](https://github.com/Ljzd-PRO/PyDGLab-WS) 创建服务端和终端以实现对 DG-Lab App 的控制

### 更多郊狼玩法？

- 专门适配郊狼的 buttplug 协议分支：[buttplug-dg-lab](https://github.com/Ljzd-PRO/buttplug-dg-lab)
- 恐怖游戏 DeppartPrototype Mod：[HentaiPlayMode](https://github.com/Ljzd-PRO/DeppartPrototypeHentaiPlayMod)
    - 可搭配上面专门适配的分支软件使用
