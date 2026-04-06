# 账号堡垒机系统 - 功能说明

## 已实现的核心功能

### 1. 账号管理 ✅
- 集中存储 Google、Reddit、GitHub 等平台账号
- 密码加密存储（Fernet 对称加密）
- 支持账号增删改查
- 2FA 密钥管理
- 备注/说明功能

### 2. 自动化登录 ✅
- 一键生成 Playwright 登录脚本
- 支持直接 Google 登录
- 支持通过 Google OAuth 登录 Reddit
- 自动处理 2FA 验证码（调用 https://2fa.run/ API）
- 验证码手动输入场景支持

### 3. 堡垒机特性 ✅

#### 3.1 操作审计
- **审计日志（Audit Logs）**
  - 记录所有账号操作（创建、读取、更新、删除）
  - 记录敏感操作（解密密码、下载脚本）
  - 记录操作时间、用户、IP 地址
  - 支持按操作类型、资源类型筛选
  - API: `GET /api/audit/audit-logs`

- **访问日志（Access Logs）**
  - 记录账号访问历史
  - 记录脚本下载、登录尝试
  - 记录操作成功/失败状态
  - 支持按账号、平台、操作类型筛选
  - API: `GET /api/audit/access-logs`

#### 3.2 统计分析
- 系统统计信息
  - 总账号数
  - 总审计日志数
  - 总访问日志数
  - 按平台统计账号分布
  - 最近 7 天访问统计
  - API: `GET /api/audit/stats`

#### 3.3 安全特性
- 密码加密存储
- 独立加密密钥管理
- 操作 IP 地址记录
- 敏感操作审计追踪
- 访问权限控制（可扩展）

## API 接口

### 账号管理
```
POST   /api/accounts/           # 创建账号
GET    /api/accounts/           # 获取所有账号
GET    /api/accounts/{id}       # 获取单个账号
PUT    /api/accounts/{id}       # 更新账号
DELETE /api/accounts/{id}       # 删除账号
GET    /api/accounts/{id}/password  # 获取解密密码（敏感操作）
```

### 脚本生成
```
GET    /api/scripts/login-script/{id}  # 下载登录脚本
```

### 审计查询
```
GET    /api/audit/audit-logs     # 获取审计日志
GET    /api/audit/access-logs    # 获取访问日志
GET    /api/audit/stats          # 获取统计信息
```

## 数据库结构

### accounts 表
```sql
- id: 主键
- platform: 平台名称（google/reddit/github）
- username: 用户名/邮箱
- password: 加密后的密码
- two_factor_secret: 2FA 密钥
- notes: 备注
- created_at: 创建时间
- updated_at: 更新时间
```

### audit_logs 表
```sql
- id: 主键
- action: 操作类型（create/read/update/delete/download/decrypt_password）
- resource_type: 资源类型（account/script）
- resource_id: 资源ID
- user: 操作用户
- details: 操作详情（JSON格式）
- ip_address: 操作IP地址
- created_at: 创建时间
```

### access_logs 表
```sql
- id: 主键
- account_id: 账号ID
- platform: 平台名称
- username: 用户名
- action: 操作类型（script_download/login_attempt）
- success: 是否成功（success/failed）
- error_message: 错误信息
- user: 操作用户
- ip_address: 操作IP地址
- created_at: 创建时间
```

## 使用示例

### 添加账号
```bash
curl -X POST http://localhost:8080/api/accounts/ \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "google",
    "username": "example@gmail.com",
    "password": "yourpassword",
    "two_factor_secret": "yoursecret",
    "notes": "工作账号"
  }'
```

### 下载登录脚本
```bash
curl http://localhost:8080/api/scripts/login-script/1 \
  -o login_script.py
```

### 查看审计日志
```bash
curl http://localhost:8080/api/audit/audit-logs
```

### 查看统计信息
```bash
curl http://localhost:8080/api/audit/stats
```

## 未来扩展功能

### 1. 用户认证系统
- 用户注册/登录
- JWT Token 认证
- 角色权限管理（管理员/普通用户）
- 多因素认证（MFA）

### 2. 高级审计
- 实时日志监控
- 告警通知（异常操作检测）
- 报表生成
- 数据导出

### 3. 访问控制
- IP 白名单/黑名单
- 时间段访问限制
- 操作频率限制
- 账号使用配额

### 4. 自动化增强
- 定时任务调度
- 批量操作
- Webhook 通知
- 账号健康检查

### 5. 更多平台
- Twitter/X
- Facebook
- LinkedIn
- 更多 SaaS 平台

## 安全建议

1. **部署环境**
   - 建议部署在内网环境
   - 使用 HTTPS 访问
   - 配置防火墙规则

2. **密钥管理**
   - 妥善保管 `encryption_key.key`
   - 定期更换加密密钥
   - 备份密钥文件

3. **访问控制**
   - 启用用户认证
   - 设置权限管理
   - 定期审计访问日志

4. **监控告警**
   - 监控异常登录行为
   - 设置告警规则
   - 定期检查审计日志

## 技术架构

```
前端 (React + TypeScript + Ant Design)
    ↓ HTTP API
后端 (Python + FastAPI)
    ↓
数据库 (SQLite)
    ├── accounts (账号信息)
    ├── audit_logs (审计日志)
    └── access_logs (访问日志)
```
