# Windows 本机接管说明

## 必须保留

- `backend/`、`pyfeatlive_core/`、`frontend/`、`sidecar/`、`tauri/`、`vendor/`
- `tests/`、`docs/`
- 根目录中的 `requirements*.txt`、许可证、计划文档
- `build-windows.ps1`

## 不要从 Linux 携带

这些内容与操作系统或本机路径绑定，应在 Windows 重新生成：

- `.git/`（除非还需要版本历史）
- `frontend/node_modules/`
- `tauri/node_modules/`
- `tauri/src-tauri/target/`
- `.venv/`、`__pycache__/`、`.pytest_cache/`
- `tauri/dist/`

## Windows 前置软件

1. Node.js 20
2. pnpm 9：管理员 PowerShell 执行 `corepack enable` 和 `corepack prepare pnpm@9 --activate`
3. Rust stable（rustup，MSVC 工具链）
4. Visual Studio Build Tools 2022：勾选“使用 C++ 的桌面开发”和 Windows 10/11 SDK
5. WebView2 Runtime（Windows 10/11 通常已安装）

## 构建

在解压目录打开 PowerShell：

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\build-windows.ps1
```

生成的安装包位于：

```text
tauri\src-tauri\target\release\bundle\nsis\*.exe
```

首次启动需要联网。应用会通过内置 `uv.exe` 创建 Python 环境并安装 Py-Feat、PyTorch 等依赖；随后还可能下载模型权重。建议预留数 GB 磁盘空间。

## Windows 验收顺序

1. 安装并启动应用，允许摄像头权限和本机回环网络访问。
2. 选择 CPU 与 Detectorv2，确认摄像头画面和人脸框。
3. 打开 `Behavior indices`，确认显示 valence、activation、confidence 和构型证据。
4. 录制约 30 秒，停止后进入 Viewer，确认相同面板可以回放。
5. 断网重启一次，确认已缓存的运行环境和模型仍可使用。
6. 记录 CPU 型号、内存、检测 FPS；低于可接受速度时再评估 ONNX/DirectML。

## 科学与许可边界

界面结果只能称为“观察到的面部动作/表情构型证据”，不能称为真实心情、心理诊断、测谎或意图判断。应用源代码可继续开发，但预训练模型权重可能受研究用途或非商业许可限制，商业发布前必须重新核查各模型许可证。
