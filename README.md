# astrbot_plugin_mailer

`astrbot_plugin_mailer` 是一个为 AstrBot 提供 SMTP 发信能力的插件，用来给 LLM 暴露一个受控的邮件发送工具。

它支持：

- 纯文本邮件
- HTML 富文本邮件
- 通过 `cid:` 引用的文中内嵌图片
- 本地文件附件
- 收件人域名白名单/黑名单限制
- 调用者 ID 白名单限制
- 附件目录沙箱限制

## 功能概览

- 向 AstrBot 注册一个 LLM 工具：`send_email`
- 通过 SMTP 发送邮件，支持 TLS 和 STARTTLS
- 自动构造适合文本、HTML、内嵌图片、附件的 MIME 邮件结构
- 通过 `allowed_sender_ids` 限制哪些用户可触发发信
- 通过 `allowed_domains` / `blocked_domains` 限制收件人域名
- 通过 `allowed_attachment_roots` 限制附件来源目录
- 提供 `/mail_test` 和 `/mail_config_check` 用于人工验证

## 目录结构

```text
astrbot_plugin_mailer/
  main.py
  metadata.yaml
  _conf_schema.json
  requirements.txt
  README.md
  mailer/
    models.py
    message_builder.py
    smtp_client.py
  tests/
```

## 安装方式

将插件放到 AstrBot 插件目录：

```text
data/plugins/astrbot_plugin_mailer/
```

AstrBot 会根据 `requirements.txt` 安装运行时依赖：

- `aiosmtplib`

## 配置说明

插件配置通过 `_conf_schema.json` 暴露给 AstrBot WebUI，并已按分组组织，便于在界面中分类查看。

### 1. `smtp` 发信配置

- `host`：SMTP 服务器地址
- `port`：SMTP 服务器端口
- `use_tls`：是否使用隐式 TLS，通常是 465
- `use_starttls`：是否使用 STARTTLS，通常是 587
- `username`：SMTP 用户名
- `password`：SMTP 密码或邮箱授权码
- `from_name`：发件人显示名称
- `from_email`：发件人邮箱地址
- `default_reply_to`：默认回复地址，可留空
- `subject_prefix`：统一添加到所有邮件主题前的前缀，可留空

### 2. `tool` 工具控制

- `enable_llm_tool`：是否向 LLM 暴露 `send_email` 工具
- `require_tool_confirmation`：是否禁止直接工具发送，开启后工具会拒绝直接发信，适合后续接入人工确认流程

### 3. `security` 安全控制

- `allowed_sender_ids`：允许调用邮件功能的 AstrBot 用户 ID 列表，空表示不限制
- `allowed_domains`：允许发送的收件人域名白名单，空表示不限制
- `blocked_domains`：禁止发送的收件人域名黑名单
- `allowed_attachment_roots`：允许作为附件和内嵌图片来源的绝对目录列表
- `max_attachment_size_mb`：单个文件大小上限，单位 MB
- `max_total_attachment_size_mb`：所有附件与内嵌图片总大小上限，单位 MB
- `max_html_length`：HTML 正文最大长度

## 附件路径规则

插件默认始终允许以下目录中的文件作为附件或内嵌图片：

```text
data/plugin_data/astrbot_plugin_mailer/attachments/
```

如果传入的是相对路径，会自动按该目录解析。

例如：

```json
{"path": "report.pdf"}
```

会被解析为：

```text
data/plugin_data/astrbot_plugin_mailer/attachments/report.pdf
```

如果传入绝对路径，则必须位于 `allowed_attachment_roots` 配置的目录之一中，否则会被拒绝。

## LLM 工具说明

插件目前注册一个工具：

### `send_email`

建议的调用参数如下：

```json
{
  "to": ["alice@example.com"],
  "cc": ["bob@example.com"],
  "bcc": ["carol@example.com"],
  "subject": "周报",
  "text_body": "这是纯文本正文",
  "html_body": "<p>你好，见下图：<img src=\"cid:chart-1\"></p>",
  "reply_to": "reply@example.com",
  "attachments": [
    {
      "path": "report.pdf",
      "filename": "Q1-report.pdf"
    }
  ],
  "inline_images": [
    {
      "path": "chart.png",
      "cid": "chart-1"
    }
  ]
}
```

参数约束：

- `to` 必填
- `subject` 必填
- `text_body` 和 `html_body` 至少提供一个
- 使用 `inline_images` 时必须提供 `html_body`
- 所有附件和内嵌图片路径都必须通过目录沙箱检查

## 手动命令

### `/mail_config_check`

检查当前插件 SMTP 配置是否完整，并输出关键运行信息。

### `/mail_test recipient@example.com`

发送一封简单测试邮件，用于验证 SMTP 配置和发信链路。

## 安全建议

这是一个具备实际外发能力的插件，建议上线前至少配置以下项：

- 设置 `security.allowed_sender_ids`
- 设置 `security.allowed_domains`
- 将 `security.allowed_attachment_roots` 控制在尽可能小的范围内
- 使用邮箱授权码，不要直接使用主账号密码
- 如果不希望模型自主发信，可将 `tool.require_tool_confirmation` 设为 `true`

当前版本尚未支持：

- 远程 URL 附件下载
- 远程 URL 图片下载
- 交互式人工确认发送
- 持久化发信审计日志

## 本地测试

插件已经包含针对解析、MIME 构造和安全检查的单元测试。

### 使用 uv 创建测试环境

```powershell
uv venv .venv --python 3.12
uv pip install pytest pytest-asyncio aiosmtplib "pydantic>=2.12.5" "jsonschema>=4.25.1" "mcp>=1.8.0" "deprecated>=1.2.18"
```

### 执行测试

```powershell
.venv\Scripts\python -m pytest tests -q
```

当前通过结果：

```text
11 passed
```

## 开发说明

- `mailer/models.py`：请求数据解析与校验
- `mailer/message_builder.py`：MIME 邮件构造
- `mailer/smtp_client.py`：SMTP 异步发送封装
- `main.py`：AstrBot 插件入口、策略检查、工具注册与命令处理

## 后续建议

接下来比较值得继续补的能力：

1. 增加“发送前确认”工作流
2. 在 `data/plugin_data` 下记录发信审计日志
3. 提供更友好的 HTML 模板辅助能力
4. 增加针对真实 `send_email_tool()` 异步发送路径的 mock 测试
