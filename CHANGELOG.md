# Changelog

本项目遵循语义化版本管理。

## 0.1.0 - 2026-04-06

首个可用版本，提供 AstrBot SMTP 邮件发送插件的完整基础能力。

### Added

- 新增 AstrBot 插件入口与标准插件结构
- 新增 `send_email` LLM 工具，可由模型发起邮件发送
- 新增 SMTP 发信能力，支持隐式 TLS 与 STARTTLS
- 新增纯文本邮件发送能力
- 新增 HTML 富文本邮件发送能力
- 新增基于 `cid:` 的内嵌图片发送能力
- 新增本地文件附件发送能力
- 新增 `/mail_test` 管理命令，用于测试 SMTP 发信链路
- 新增 `/mail_config_check` 管理命令，用于检查当前配置
- 新增 WebUI 配置 schema，并按 `smtp`、`tool`、`security` 分组展示
- 新增收件人域名白名单与黑名单限制
- 新增调用者 ID 白名单限制
- 新增附件目录沙箱限制
- 新增单文件大小与总附件大小限制
- 新增 HTML 正文长度限制
- 新增可选高风险开关 `security.allow_unsafe_all_attachment_paths`
- 新增中文 README 文档
- 新增单元测试，覆盖请求解析、MIME 构造、路径安全、工具调用适配和 SMTP 返回格式化

### Changed

- 优化 `send_email` 工具描述，引导 LLM 优先生成富文本邮件而不是纯文本邮件
- 规范化 WebUI 配置项文案，将主标题放入 `description`，说明文字放入 `hint`
- 将 `/mail_test` 与 `/mail_config_check` 调整为默认仅管理员可用
- 优化邮件发送成功后的返回结果格式，避免出现冗余 SMTP 响应对象字符串

### Fixed

- 修复 `FunctionTool.handler` 在 AstrBot 运行时下的绑定兼容问题
- 修复 LLM 调用工具时因 handler 参数错位导致的发送失败问题
- 修复空收件人未被尽早拦截的问题
- 修复 `smtp.use_tls` 与 `smtp.use_starttls` 可同时开启的问题
- 修复测试命令与工具路径在内容限制校验上的行为不一致问题

### Security

- 默认禁止读取任意本地附件路径
- 默认仅允许插件附件目录和显式配置的允许目录中的文件作为附件或内嵌图片
- 文档中补充了危险配置项的风险提示与生产环境使用建议

### Test

- 当前版本测试状态：`17 passed`
