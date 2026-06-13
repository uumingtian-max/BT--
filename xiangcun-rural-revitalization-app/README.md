# 乡村振兴聊天 App + 后台管理系统（可运行测试版）

## 默认账号
- 最高后台账号：`admin`
- 默认密码：`admin123456`

## 启动
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn backend.app:app --reload --host 0.0.0.0 --port 8000
```

访问：`http://127.0.0.1:8000/docs`

## 已实现模块
- 用户实名注册、登录、会话 token
- 后台最高管理员
- 后台创建用户端管理账号
- 管理账号无需实名
- 管理账号可发红包，不可抢红包
- 后台给用户/管理账号充值余额
- 用户管理列表
- 禁言：禁言后不能发消息，但可以收消息
- 封禁：账号不能登录；同身份证不能再次注册
- 聊天消息/群聊房间
- 全体公告、单人通知
- 红包发送、领取、防重复领取
- IP 黑名单
- 设备指纹封禁
- 操作审计日志
- 数据备份
- 推送通知模拟接口
- 语音转文字本地模拟接口
- 视频房间 token 模拟接口

## 说明
推送、语音转文字、视频通话已做成可测试本地接口；正式上线时只需要把 provider 换成真实厂商 SDK/服务，不影响业务流程测试。
