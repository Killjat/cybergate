# ⚡ CyberGate

**数字骑兵工厂。**

---

互联网上最有价值的情报，藏在登录墙后面。匿名访问者永远看不到。

CyberGate 解决的不是"如何采集情报"，而是更底层的问题：

**如何批量制造可以穿透登录墙的数字身份。**

---

## 我们做什么

CyberGate 是一条流水线。

输入：一批 Google 账号、密码、2FA 密钥。

输出：一批**活的、已登录的、可以立刻投入使用的数字骑兵**。

每一个骑兵都是一个完整的 Chrome Profile —— 包含 Google session、Reddit session、以及所有用这个 Google 账号登录过的平台的 session。打包成一个文件夹，可以在任意机器上复活，30 秒内激活。

CyberGate 的职责到这里就结束了。

骑兵交付之后去哪、做什么、看什么、采集什么 —— 那是情报系统的事，不是我们的事。

---

## 为什么需要这个

直接用账号密码登录行不行？

不行。Google 的风控系统每天拦截数百万次机器人登录。直接访问登录 URL、机器速度填表、没有浏览历史、没有鼠标轨迹 —— 这些特征会立刻触发封号。

CyberGate 的登录引擎完全不同：

- 从空白地址栏开始，手动输入 `google.com`
- 在主页随机停留、滚动，模拟真实用户节奏
- 逐字符输入账号密码，带随机停顿
- 鼠标自然移动，悬停后点击
- 全程真实 Chrome，无 WebDriver 特征

对 Google 来说，这就是一个普通用户在登录。

---

## 骑兵的生命周期

```
[CyberGate]
  账号录入 → 反检测登录 → Session 固化为 Profile
                                    ↓
                             打包 tar.gz
                                    ↓
              ┌─────────────────────┼─────────────────────┐
              ↓                     ↓                     ↓
         Server A              Server B              Server C
      [骑兵1 寄生]           [骑兵2 寄生]           [骑兵3 寄生]
      Google + Reddit        Google + Reddit        Google + Reddit
              ↓                     ↓                     ↓
         情报采集              情报采集              情报采集
```

每台服务器上的骑兵是独立的。它们看到的内容不同，行为轨迹不同，对平台来说是完全不同的用户。

CyberGate 不知道它们在做什么。这是设计，不是缺陷。

---

## 一个 Profile 能登录多少平台

理论上无限。

只要是支持"用 Google 账号登录"的平台，都可以用同一个 Profile 完成登录，session 全部存在同一个文件夹里。

目前支持：
- Google（原生）
- Reddit（Continue with Google）
- 更多平台持续扩展中

---

## API

情报系统通过 API 与 CyberGate 交互：

```
POST /api/start-auto-login/{account_id}   # 触发自动登录
POST /api/open-browser/{account_id}       # 用已有 session 打开浏览器
GET  /api/profiles                        # 查询所有骑兵状态
GET  /api/profiles/{account_id}/export   # 下载打包好的 Profile
POST /api/logout                          # 退出，关闭所有浏览器实例
```

---

## 快速开始

```bash
# 依赖：Python 3.10+，Node.js 16+，PinchTab
pinchtab server          # 启动浏览器控制层
cd backend && python3 main.py   # 启动后端
cd frontend && npm start        # 启动前端
```

访问 `http://localhost:3000`，第一个注册的账号自动成为管理员。

---

## 安全边界

- CyberGate 只负责制造骑兵，不记录骑兵的行动
- Profile 目录包含完整 session，安全级别等同于密码
- PinchTab 默认只监听本地，不对外暴露
- 骑兵部署到远程服务器后，CyberGate 与其完全断开

---

*CyberGate — 我们只管造兵，不管打仗。*
