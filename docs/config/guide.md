> nonebot 文档介绍：[dotenv 配置文件](https://nonebot.dev/docs/2.3.0/appendices/config#dotenv-%E9%85%8D%E7%BD%AE%E6%96%87%E4%BB%B6)

!!! warning "注意"
    首次使用，必须更改 WebSocket 服务端配置，否则用户将可能无法连接

- DG-Lab-Play 读取工作目录下的 `.env` 文件 或 环境变量 来设定配置（是否为 `.env.dev` 等取决于您的 nonebot 配置）
- **用 `__` 来指定子选项**，即 `env_nested_delimiter`，例如 `DG_LAB_PLAY__WS_SERVER` 相当于 `dg_lab_play.ws_server`
- 更多配置内容请查看侧边菜单



## 首次使用

有两种配置 DG-Lab WebSocket 服务端的方法，分别为本地搭建和连接远程服务器，默认为本地搭建

### 📌（默认）采用本地搭建 WebSocket 服务端的方法

修改 nonebot 目录下的 `.env` 文件，参考如下：

#### （可选）设置本地服务端监听主机号和端口
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
# SSL 证书密钥路径
# 若使用相对路径，起始位置为机器人项目目录
DG_LAB_PLAY__WS_SERVER__LOCAL_SERVER_SSL_KEY="/path/to/密钥文件"
# SSL 证书密钥密码
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