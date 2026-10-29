"""Portable named Windows mappings, without Bluetooth or local runtime state."""
import copy
import math

from .xiaomi_config import BUTTONS, resolve_hotkey_virtual_keys, hotkey_injection_method


def validate_profile(value: dict) -> dict:
    if not isinstance(value, dict) or value.get("format") != "mivibe-windows-profile" or value.get("version") != 1:
        raise ValueError("请选择 MiVibe Windows 配置文件（版本 1）")
    name = value.get("name")
    if not isinstance(name, str) or not 1 <= len(name.strip()) <= 20:
        raise ValueError("配置名称应为 1–20 个字符")
    voice = value.get("voice", {})
    if not isinstance(voice, dict) or voice.get("trigger_mode") not in {"hold", "toggle"}:
        raise ValueError("语音触发方式无效")
    gain = float(voice.get("gain_db", 10))
    if not math.isfinite(gain) or not -12 <= gain <= 30:
        raise ValueError("增益应在 -12 到 30 dB 之间")
    bindings = value.get("button_bindings")
    if not isinstance(bindings, dict) or set(bindings) != {key for key, _ in BUTTONS}:
        raise ValueError("配置必须包含全部遥控器按键")
    clean = {}
    for button, actions in bindings.items():
        if not isinstance(actions, list) or len(actions) > 8:
            raise ValueError("按键动作格式无效")
        clean[button] = []
        for action in actions:
            if not isinstance(action, dict):
                raise ValueError("按键动作格式无效")
            kind = action.get("type")
            if kind == "hotkey":
                keys = action.get("keys")
                if not isinstance(keys, list) or not all(isinstance(key, str) for key in keys):
                    raise ValueError("快捷键格式无效")
                resolve_hotkey_virtual_keys(keys)
                entry = {"type": kind, "keys": keys[:], "injection": hotkey_injection_method(keys)}
                if "hold_ms" in action:
                    hold = int(action["hold_ms"])
                    if not 0 <= hold <= 5000:
                        raise ValueError("按键持续时间无效")
                    entry["hold_ms"] = hold
            elif kind in {"open_codex", "preset_cycle"}:
                entry = {"type": kind}
            elif kind == "mouse_wheel":
                delta = int(action.get("delta", 0))
                if not 0 < abs(delta) <= 1200:
                    raise ValueError("滚轮步长无效")
                entry = {"type": kind, "delta": delta}
            else:
                raise ValueError("便携配置仅支持快捷键、滚轮、打开 Codex 和切换预设；程序命令请在本机设置")
            clean[button].append(entry)
    enabled = voice.get("enabled", True)
    if not isinstance(enabled, bool):
        raise ValueError("语音启用状态无效")
    if enabled and (not clean["mic"] or clean["mic"][0]["type"] != "hotkey"):
        raise ValueError("启用语音时必须为麦克风键设置快捷键")
    return {"format": "mivibe-windows-profile", "version": 1, "name": name.strip(),
            "voice": {"enabled": enabled, "trigger_mode": voice["trigger_mode"], "gain_db": gain},
            "button_bindings": copy.deepcopy(clean)}
