#!/usr/bin/env python3
"""Add a portable MiVibe macOS profile without replacing existing presets."""
import json
import plistlib
import subprocess
import sys
import uuid
from pathlib import Path

DOMAIN = "com.mivibe.remote"
FIELDS = ("name", "voiceShortcutProfile", "customVoiceShortcut", "customVoiceTriggerMode",
          "buttonBindings", "buttonShortcuts", "secondaryButtonBindings")
BUTTONS = {"power", "up", "left", "ok", "right", "down", "back", "volume_up",
           "home", "volume_down", "menu", "tv"}
ACTIONS = {"disabled", "escape", "returnKey", "arrowUp", "arrowDown", "arrowLeft",
           "arrowRight", "scrollUp", "scrollDown", "deleteBackward", "showDesktop",
           "contextMenu", "appSwitcher", "volumeUp", "volumeDown", "volumeMute",
           "playPause", "customShortcut", "cyclePreset", "openRemoteMic", "openCodex",
           "openWorkBuddy", "openClaude", "openCmux", "openWeChat", "openCursor",
           "openXcode", "openSlack", "openWeCom", "openNeteaseMusic", "openChrome",
           "openSafari", "openZed"}


def valid_shortcut(value):
    return (isinstance(value, dict) and type(value.get("keyCode")) is int
            and 0 <= value["keyCode"] <= 65535
            and type(value.get("modifierFlagsRawValue")) is int
            and 0 <= value["modifierFlagsRawValue"] < 2**64
            and isinstance(value.get("keyLabel"), str))


def validate_preset(preset):
    if not isinstance(preset, dict) or not all(key in preset for key in FIELDS if key != "customVoiceShortcut"):
        raise ValueError("预设缺少必要字段")
    if (preset["voiceShortcutProfile"] not in ("codex", "workBuddy", "weChat", "custom")
            or preset["customVoiceTriggerMode"] not in ("hold", "toggle")):
        raise ValueError("语音配置无效")
    shortcut = preset.get("customVoiceShortcut")
    if shortcut is not None and not valid_shortcut(shortcut):
        raise ValueError("语音快捷键格式无效")
    bindings, shortcuts, secondary = (preset[key] for key in
                                       ("buttonBindings", "buttonShortcuts", "secondaryButtonBindings"))
    if not all(isinstance(item, dict) for item in (bindings, shortcuts, secondary)):
        raise ValueError("按键配置无效")
    if any(key not in BUTTONS or not isinstance(value, str) or value not in ACTIONS for key, value in bindings.items()):
        raise ValueError("按键动作无效")
    if any(key not in BUTTONS or not valid_shortcut(value) for key, value in shortcuts.items()):
        raise ValueError("按键快捷键无效")
    for key, triggers in secondary.items():
        if key not in BUTTONS or not isinstance(triggers, dict):
            raise ValueError("附加按键配置无效")
        for trigger, binding in triggers.items():
            if (trigger not in {"doubleClick", "longPress"} or not isinstance(binding, dict)
                    or not isinstance(binding.get("action"), str) or binding["action"] not in ACTIONS
                    or (binding.get("shortcut") is not None and not valid_shortcut(binding["shortcut"]))):
                raise ValueError("附加按键动作无效")


def prepare(profile, existing):
    if not isinstance(profile, dict) or profile.get("format") != "mivibe-macos-profile" or profile.get("version") != 1:
        raise ValueError("不支持的配置格式或版本")
    if not all(field in profile for field in FIELDS):
        raise ValueError("配置缺少必要字段")
    validate_preset(profile)
    name = profile["name"]
    if not isinstance(name, str) or not name.strip() or len(name.strip()) > 20:
        raise ValueError("预设名称必须为 1 至 20 个字符")
    if not isinstance(existing, list) or not all(isinstance(item, dict) and isinstance(item.get("name"), str) for item in existing):
        raise ValueError("现有预设格式无法识别，已停止导入")
    for item in existing:
        try:
            uuid.UUID(item["id"])
            validate_preset(item)
        except (KeyError, ValueError, TypeError, AttributeError) as exc:
            raise ValueError("现有预设格式无法识别，已停止导入") from exc
    if any(item["name"].casefold() == name.strip().casefold() for item in existing):
        raise ValueError("已存在同名预设；请先在应用内重命名该预设")
    preset = {key: profile[key] for key in FIELDS}
    preset["name"] = name.strip()
    preset["id"] = str(uuid.uuid4()).upper()
    return existing + [preset]


def main():
    if sys.platform != "darwin":
        raise ValueError("此工具只能在 macOS 上运行")
    running = subprocess.run(["/usr/bin/pgrep", "-x", "RemoteMic"], stdout=subprocess.DEVNULL).returncode
    if running == 0:
        raise ValueError("请先从 MiVibe Remote 的“退出应用”完全退出，再运行导入工具")
    if running != 1:
        raise ValueError("无法确认 MiVibe Remote 是否已退出，已停止导入")
    profile_path = Path(sys.argv[1]) if len(sys.argv) == 2 else Path(__file__).with_name("WQS.json")
    if len(sys.argv) > 2:
        raise ValueError("用法：python3 import-profile.py [配置文件路径]")
    profile = json.loads(profile_path.read_text(encoding="utf-8"))
    result = subprocess.run(["/usr/bin/defaults", "export", DOMAIN, "-"], capture_output=True)
    if result.returncode:
        raise ValueError("无法读取 MiVibe 设置；请先安装并启动一次应用，然后完全退出")
    prefs = plistlib.loads(result.stdout)
    data = prefs.get("localPresets")
    if data is not None and not isinstance(data, bytes):
        raise ValueError("现有预设数据格式无法识别，已停止导入")
    existing = json.loads(data) if data is not None else []
    updated = prepare(profile, existing)
    payload = json.dumps(updated, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    subprocess.run(["/usr/bin/defaults", "write", DOMAIN, "localPresets", "-data", payload.hex()], check=True)
    print("已添加 WQS 预设。请启动 MiVibe Remote，在“按键”页面选择 WQS。")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, json.JSONDecodeError, plistlib.InvalidFileException, subprocess.CalledProcessError) as exc:
        print(f"导入失败：{exc}", file=sys.stderr)
        sys.exit(1)
