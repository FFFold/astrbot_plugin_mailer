from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from types import SimpleNamespace
from types import ModuleType

import pytest

from astrbot_plugin_mailer.mailer.models import MailRequest


def _install_astrbot_stubs() -> None:
    if "astrbot.api" in sys.modules:
        return

    astrbot_module = ModuleType("astrbot")
    api_module = ModuleType("astrbot.api")
    event_module = ModuleType("astrbot.api.event")
    star_module = ModuleType("astrbot.api.star")

    class _Logger:
        def info(self, *_args, **_kwargs) -> None:
            return None

        def exception(self, *_args, **_kwargs) -> None:
            return None

    class _FunctionTool:
        def __init__(self, **kwargs) -> None:
            self.__dict__.update(kwargs)

    class _Filter:
        class PermissionType:
            ADMIN = "admin"

        @staticmethod
        def command(_name):
            def decorator(func):
                return func

            return decorator

        @staticmethod
        def permission_type(_permission_type):
            def decorator(func):
                return func

            return decorator

    class _Star:
        def __init__(self, context) -> None:
            self.context = context

    class _StarTools:
        @staticmethod
        def get_data_dir(_name: str) -> Path:
            raise RuntimeError(
                "StarTools.get_data_dir should not be used in unit tests"
            )

    api_module.AstrBotConfig = dict
    api_module.FunctionTool = _FunctionTool
    api_module.logger = _Logger()
    event_module.AstrMessageEvent = object
    event_module.filter = _Filter()
    star_module.Context = object
    star_module.Star = _Star
    star_module.StarTools = _StarTools

    sys.modules["astrbot"] = astrbot_module
    sys.modules["astrbot.api"] = api_module
    sys.modules["astrbot.api.event"] = event_module
    sys.modules["astrbot.api.star"] = star_module


_install_astrbot_stubs()

from astrbot_plugin_mailer.main import MailerPlugin


class DummyContext:
    def __init__(self) -> None:
        self.tools = []

    def add_llm_tools(self, *tools) -> None:
        self.tools.extend(tools)


def build_plugin(tmp_path: Path, **overrides) -> MailerPlugin:
    config = {
        "smtp": {
            "host": "smtp.example.com",
            "port": 465,
            "use_tls": True,
            "use_starttls": False,
            "username": "bot@example.com",
            "password": "secret",
            "from_name": "AstrBot Mailer",
            "from_email": "bot@example.com",
            "default_reply_to": "",
            "subject_prefix": "",
        },
        "tool": {
            "enable_llm_tool": True,
            "require_tool_confirmation": False,
        },
        "security": {
            "allowed_sender_ids": [],
            "allowed_domains": [],
            "blocked_domains": [],
            "allowed_attachment_roots": [str(tmp_path.resolve())],
            "allow_unsafe_all_attachment_paths": False,
            "max_attachment_size_mb": 2,
            "max_total_attachment_size_mb": 4,
            "max_html_length": 10000,
        },
    }
    for key, value in overrides.items():
        if key in config and isinstance(config[key], dict) and isinstance(value, dict):
            config[key].update(value)
        else:
            config[key] = value

    plugin = MailerPlugin.__new__(MailerPlugin)
    plugin.context = DummyContext()
    plugin.config = config
    plugin.data_dir = tmp_path
    plugin.attachments_dir = tmp_path
    return plugin


def test_recipient_policy_blocks_disallowed_domains(tmp_path: Path) -> None:
    plugin = build_plugin(tmp_path, security={"allowed_domains": ["example.com"]})
    request = MailRequest.from_payload(
        {
            "to": ["alice@other.com"],
            "subject": "Blocked",
            "text_body": "Hello",
        }
    )

    with pytest.raises(ValueError, match="不在白名单"):
        plugin._check_recipient_policy(request)


def test_file_limits_resolve_paths_inside_allowed_roots(tmp_path: Path) -> None:
    plugin = build_plugin(tmp_path)
    attachment = tmp_path / "safe.txt"
    attachment.write_text("payload", encoding="utf-8")
    request = MailRequest.from_payload(
        {
            "to": ["alice@example.com"],
            "subject": "Safe",
            "text_body": "Hello",
            "attachments": [{"path": str(attachment)}],
        }
    )

    plugin._check_file_limits(request)
    assert request.attachments[0].path == attachment.resolve()


def test_file_limits_reject_paths_outside_allowed_roots(tmp_path: Path) -> None:
    plugin = build_plugin(tmp_path)
    outside = tmp_path.parent / "outside.txt"
    outside.write_text("payload", encoding="utf-8")
    request = MailRequest.from_payload(
        {
            "to": ["alice@example.com"],
            "subject": "Unsafe",
            "text_body": "Hello",
            "attachments": [{"path": str(outside)}],
        }
    )

    with pytest.raises(ValueError, match="不在允许的附件目录内"):
        plugin._check_file_limits(request)


def test_file_limits_allow_any_path_when_unsafe_switch_enabled(tmp_path: Path) -> None:
    plugin = build_plugin(
        tmp_path,
        security={"allow_unsafe_all_attachment_paths": True},
    )
    outside = tmp_path.parent / "outside-unsafe.txt"
    outside.write_text("payload", encoding="utf-8")
    request = MailRequest.from_payload(
        {
            "to": ["alice@example.com"],
            "subject": "Unsafe allowed",
            "text_body": "Hello",
            "attachments": [{"path": str(outside)}],
        }
    )

    plugin._check_file_limits(request)
    assert request.attachments[0].path == outside.resolve()


def test_sender_allowlist_blocks_unknown_sender(tmp_path: Path) -> None:
    plugin = build_plugin(tmp_path, security={"allowed_sender_ids": ["user-1"]})
    event = SimpleNamespace(get_sender_id=lambda: "user-2")

    with pytest.raises(PermissionError, match="没有权限"):
        plugin._check_sender_allowed(event)


def test_smtp_settings_reject_tls_and_starttls_together(tmp_path: Path) -> None:
    plugin = build_plugin(
        tmp_path,
        smtp={
            "use_tls": True,
            "use_starttls": True,
        },
    )

    with pytest.raises(ValueError, match="不能同时开启"):
        plugin._smtp_settings()


def test_tool_handler_accepts_runtime_payload_dict(tmp_path: Path) -> None:
    plugin = build_plugin(tmp_path)
    captured = {}

    async def fake_send_email_tool(event, **payload):
        captured["event"] = event
        captured["payload"] = payload
        return "ok"

    plugin.send_email_tool = fake_send_email_tool
    event = SimpleNamespace(get_sender_id=lambda: "user-1")
    payload = {
        "to": ["alice@example.com"],
        "subject": "Test",
        "text_body": "Hello",
    }

    result = asyncio.run(plugin._send_email_tool_handler(event, payload))

    assert result == "ok"
    assert captured["event"] is event
    assert captured["payload"] == payload


def test_tool_handler_works_after_star_manager_partial_binding(tmp_path: Path) -> None:
    plugin = build_plugin(tmp_path)
    captured = {}

    async def fake_send_email_tool(event, **payload):
        captured["event"] = event
        captured["payload"] = payload
        return "ok"

    plugin.send_email_tool = fake_send_email_tool
    event = SimpleNamespace(get_sender_id=lambda: "user-1")
    payload = {
        "to": ["alice@example.com"],
        "subject": "Test",
        "text_body": "Hello",
    }

    bound_handler = MailerPlugin._send_email_tool_handler.__get__(plugin, MailerPlugin)
    result = asyncio.run(bound_handler(event, payload))

    assert result == "ok"
    assert captured["event"] is event
    assert captured["payload"] == payload


def test_tool_description_encourages_html_email(tmp_path: Path) -> None:
    plugin = build_plugin(tmp_path)
    tool = plugin._build_send_email_tool()

    assert "优先使用 html_body" in tool.description
    assert "inline_images" in tool.description
