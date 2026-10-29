# macOS WQS 配置

`WQS.json` 保存本机当前的按键和语音预设，不包含蓝牙设备标识、音频设备 ID、账号或日志。此预设独立于 Windows 配置，不能使用 Windows 客户端的导入功能。

## 在另一台 Mac 上使用

1. 安装并启动 MiVibe Remote，完成遥控器蓝牙配对和虚拟麦克风安装，再从应用左侧点击「退出应用」完全退出。
2. 将本目录复制到目标 Mac，在终端进入该目录后运行：

   ```bash
   python3 import-profile.py
   ```

   需要 macOS 的 Python 3；如提示缺少，请先安装 Apple Command Line Tools 或 Python 3。脚本只添加一个命名预设，不替换已有预设；若已有同名预设，会停止并提示先重命名。
3. 打开 MiVibe Remote，在「按键」页面选择 **WQS**。在 Codex 选择 `MiRemoteV 2ch`，并确认按住听写快捷键为 `Control + Shift + D`。在目标 Mac 上重新授予蓝牙、输入监控、辅助功能及所需的麦克风权限。
4. 实际测试遥控器语音和按键。本机当前使用默认增益 10 dB；音频增益、麦克风路由、设备配对和权限由目标 Mac 单独设置，不随预设导入。

当前快照：电源打开 Codex，方向键移动光标，确认发送，返回退格，主页显示桌面；音量加为 Command + `[`，音量减为 Command + `]`，TV 为 Command + N。语音为按住 `Control + Shift + D`。菜单键为 Command + Tab，点击一次切换到最近使用的另一个应用。主页键依赖 macOS 的「键盘 → 键盘快捷键 → 调度中心 → 显示桌面」快捷键（F11）已启用；该系统设置需在每台 Mac 单独开启。

原生 macOS 客户端目前没有文件导入界面，此脚本通过 macOS 用户偏好设置添加与应用一致的命名预设。退出应用是为了避免运行中的设置覆盖导入结果。
