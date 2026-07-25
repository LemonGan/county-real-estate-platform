# 服务器首次部署与双端开发

## 目标目录

服务器工作目录固定为：

```text
/www/wwwroot/my_work/buyHouse
```

该目录通过 GitHub 仓库同步，不能通过压缩包覆盖。`backend/.env`、日志、上传文件和 Python 虚拟环境均只保留在服务器，不能提交到 Git。

## 首次部署顺序

1. 在服务器确认目标目录不存在，或确认其中没有需要保留的项目。
2. 克隆仓库：

   ```bash
   mkdir -p /www/wwwroot/my_work
   git clone https://github.com/LemonGan/county-real-estate-platform.git /www/wwwroot/my_work/buyHouse
   cd /www/wwwroot/my_work/buyHouse
   ```

3. 创建服务器专用配置。`deploy/production.env` 是模板；复制为 `backend/.env` 后，必须填写数据库连接、Redis 地址、微信凭据、地图凭据以及新的随机 `SECRET_KEY`。
4. 安装 `deploy/supervisor.conf` 到 `/etc/supervisor/conf.d/buyhouse_api.conf`，再执行 `supervisorctl reread` 和 `supervisorctl update`。
5. 在宝塔中按 `deploy/nginx.conf` 创建站点。上线前必须将其中的 `server_name` 和证书路径替换为实际域名及证书路径；不能为公网 IP 申请 Let's Encrypt 证书。
6. 执行 `bash deploy/deploy.sh`。它会创建虚拟环境、安装依赖、初始化目录并重启 `buyhouse_api` 服务。
7. 依次验证：`supervisorctl status buyhouse_api`、`curl http://127.0.0.1:8000/health`，最后通过 HTTPS 域名访问 `/health` 和 `/docs`。

## 每次发布

```bash
cd /www/wwwroot/my_work/buyHouse
git pull --ff-only origin main
bash deploy/deploy.sh
```

只允许在工作区干净时执行 `git pull --ff-only`。若服务器上有未提交修改，应先提交或还原，并追溯修改来源，不能强制覆盖。

## 本地与服务器切换

代码变更必须通过 Git 传递：本地开发后提交并推送；服务器开发后也提交并推送。切换到另一端前执行 `git pull --ff-only`。不要在两个环境同时修改同一个未提交的分支。

## Codex 远端项目

首次克隆完成后，把 `/www/wwwroot/my_work/buyHouse` 添加为 Codex 的远端项目。之后可在本地项目和该远端项目分别创建任务；每次切换前以一个 Git 提交作为边界。这样 Codex 可直接查看服务器日志、运行服务检查和编辑远端代码，同时保留本地开发环境。
