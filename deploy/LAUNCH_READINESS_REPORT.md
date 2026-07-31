# 上线安全与稳定性检查报告

检查时间：2026-07-31

## 结论

当前服务处于可用状态，后台静态页可访问，核心后台接口未登录鉴权正常，`.env` 未被 Git 跟踪且权限收紧。证书续期和真机验收仍是上线前必须补齐的外部事项。

## 已确认正常

- Git 工作区检查：检查前工作区干净。
- 当前分支：`main`。
- 检查起点提交：`e2bc8fe feat: improve admin news editor`。
- `backend/.env`：存在于服务器本地，权限为 `600`，未输出内容。
- `.env` 忽略规则：`backend/.gitignore` 明确忽略 `.env`、`.env.local`、`.env.production`。
- 后端服务：`buyhouse_api` 由 Supervisor 管理并处于 `RUNNING`。
- 健康检查：`https://api.imlemon.top/health` 返回 `200 OK`。
- 后台页面：`https://api.imlemon.top/admin/` 返回 `200 OK`。
- 后台页面响应头：已看到 `cache-control: no-store`、`referrer-policy: no-referrer`、`x-content-type-options: nosniff`。
- 后台接口鉴权：未登录访问 `/api/v1/admin/dashboard` 返回 `401 Unauthorized`。

## 本轮已修复

- 根目录 `.gitignore` 含有 NUL 字节，被系统识别为二进制文件。已清理为普通文本。
- 清理 NUL 后残留的无意义忽略规则 `nul` 和 `$` 已移除。

## 仍需跟进

1. HTTPS 证书续期

   `api.imlemon.top` 的证书问题之前已经暂停，但上线前必须恢复处理。域名到期和证书到期不是一回事，后续要单独确认证书有效期和自动续期状态。

2. 小程序真机验收

   需要在真机上验证登录、资讯、反馈、收藏、点赞、分享、消息通知和页面样式。该项需要具备微信开发者工具/真机条件后执行。

3. 数据库备份策略

   当前检查未修改数据库，也未创建备份任务。上线前应确认 MySQL 定时备份、备份保留周期和恢复演练方式。

4. Nginx/Supervisor 开机自启

   本轮确认了当前服务运行状态，但未改动系统级开机自启配置。上线前建议再次确认服务器重启后 Nginx、Supervisor、Redis、MySQL 都能自动恢复。

5. 真实业务数据

   当前真实房源、经纪人资料仍未完全补齐。内容不足会影响小程序正式体验。

## 建议下一步

如果继续推进代码侧工作，建议下一轮做“小程序端代码级验收清单与问题修复”：在没有真机条件前，先通过页面路径、接口调用、登录态、空状态和错误提示做一次静态/接口级排查。
