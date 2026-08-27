# DockNav 坞导航

深色毛玻璃风格的 Docker 导航页。自动发现宿主机上映射出来的端口，逐个探测哪些在说 HTTP，只把能打开的做成卡片。零 label、零手工配置。

视觉沿用 [Frostcast](../Frostcast) 的同一套设计令牌（visionOS 玻璃 + 深浅双主题）。

## 技术栈
- 后端：FastAPI + uvicorn（无数据库，Docker API 即数据源）
- 前端：React 18 + TypeScript + rsbuild
- 发现：Docker API 列容器 → 并发探测每个已发布端口 → 取最像 Web UI 的那个

## 端口怎么选
1. 只看 tcp、且映射到宿主机的端口
2. 每个端口先试 `http://`，再试 `https://`，回任何状态码就算在说 HTTP
3. 有多个应答时，容器内端口越接近常见 Web 端口（80/443/8080/8000/3000/5000/5001/8096）越优先，同级取小的宿主端口
4. 一个都不应答时退回按容器端口猜（黑名单排掉 5432/1883/6379 这类），卡片上标黄提示这是推断值

## 环境变量
| 变量 | 默认 | 说明 |
|---|---|---|
| `HOST_IP` | `127.0.0.1` | 探测目标 + 生成链接用的宿主机地址。桥接网络下必须设成宿主机真实 IP |
| `DOCKER_SOCK` | `/var/run/docker.sock` | Docker socket 路径 |
| `UNRAID_ICONS` | `/var/lib/docker/unraid/images` | Unraid 图标缓存目录（需以只读方式挂载进容器） |
| `PROBE_TIMEOUT` | `3` | 单端口探测超时（秒） |
| `PROBE_LIMIT` | `16` | 并发探测数 |

扫描结果进程内缓存，只在首次请求时探测；容器有变动点刷新按钮重扫。

图标来源优先级（Unraid 环境）：模板里配的图标 URL → Unraid 缓存的本地图标（经 `/api/icon/` 代理）→ 按 [dashboard-icons](https://github.com/homarr-labs/dashboard-icons) 同名 png 猜 → 前端首字母。

## 本地开发
```bash
cd backend && pip install -r requirements.txt
HOST_IP=127.0.0.1 uvicorn app:app --port 5100 --reload    # 终端 1
cd frontend && bun install && bun run dev                  # 终端 2 → http://localhost:3001
```

## Docker
```bash
docker run -d --name docknav -p 5100:5100 \
  -e HOST_IP=192.168.31.139 \
  -v /var/run/docker.sock:/var/run/docker.sock:ro \
  -v /var/lib/docker/unraid/images:/var/lib/docker/unraid/images:ro \
  wujiyu115/docknav:latest
```
`HOST_IP` 填宿主机在局域网里的地址：容器内的探测和页面上生成的链接都用它，填成 `127.0.0.1` 时链接在别的设备上打不开。自建镜像用 `docker build -t docknav .`。

**安全**：挂 docker socket 等于给容器 root 等价权限，`:ro` 只挡写操作、不挡读全部容器信息。仅在内网跑，不要反代到公网。

## 已知边界
- 走 `br0` / `host` 网络、没有端口映射的容器（如 Home Assistant 独立 IP）不会出现，Docker API 里查不到映射
- 探测在容器内发起，桥接网络访问的是 `HOST_IP:端口`，所以 `HOST_IP` 填错会全部判成离线（仍会按推断值出卡片）
- 图标优先用 Unraid 模板里配置的（远程 URL 或缓存目录里的本地文件），没有模板配置时按 [dashboard-icons](https://github.com/homarr-labs/dashboard-icons) 同名 png 猜，取不到时前端 `onerror` 退回首字母
- 无鉴权
