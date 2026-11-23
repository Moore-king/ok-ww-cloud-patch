# ok-ww 云·鸣潮补丁（Windows 10）

让 [ok-ww](https://github.com/ok-oldking/ok-wuthering-waves) 在 **Windows 10** 上启用内置的「网页云游戏」模式，支持对**云·鸣潮**（`mc.kurogames.com/cloud`）截图并跑自动化。

> 不改 ok-ww 任何源码，只在它自带的 Python 里放两个文件；ok-ww 的 git 增量更新不会冲突。

## 一、解决什么问题

ok-ww 从 v3.8.4 起重新支持了网页云游戏（Playwright 启动 Edge + Windows Graphics Capture 截屏），但在 Windows 10 上：

1. **设备列表里根本没有「云游戏」这一项。**
   原因是 `ok/util/window.py` 里 `windows_graphics_available()` 只在系统 build ≥ **20348**（Win11 22H2 / Server 2022）时返回 True，Win10 19044 直接被判为不支持，`DeviceManager.update_browser_device()` 整段被跳过。
   而 WGC 实际从 Win10 1809（17134）就能用。

2. **即使强制开启，也抓不到画面。**
   云窗口写的视口是 1920×1080，但浏览器标题栏 + 工具栏约占 130px，1080p 屏幕可用高度只有 1040px，Chromium 会把窗口压小，渲染区只剩 1916×961；ok-ww 的几何校验要求视口完整落在客户区内，于是永远返回失败，`wgc_capture` 建不起来。

3. **运行中途抓帧会被销毁，任务卡死。**
   Chromium 因 `--no-sandbox` 会显示一条红色提示条，用户点掉它会让渲染区上移，ok-ww 判定「抓帧目标变了」→ 销毁 WGC → 任务永远等画面，后续任务全部排队。

4. **Edge 内置鼠标手势会把页面导航走。**
   该手势在浏览器 UI 进程实现，页面脚本拦不住；一次右键左滑就把云游戏页面带回 `about:blank`。

## 二、补丁做了什么

| # | 改动 | 说明 |
|---|---|---|
| 1 | WGC 门槛 `20348` → `19041` | 让 Win10 能识别云游戏设备（仍会做真实的 WGC 激活检测） |
| 2 | 云窗口视口自适应 | 从 ok-ww 自带的 `supported_resolution.resize_to` 里挑最大的、能完整放进屏幕的 16:9（1080p 屏 → 1600×900；2K/4K → 1920×1080） |
| 3 | 追加 `--test-type` | 去掉 `--no-sandbox` 提示条，渲染区偏移恒定，不再触发抓帧重建 |
| 4 | 关闭 Edge 内置鼠标手势 | 合并进 `--disable-features=...`，**只作用于 ok-ww 启动的浏览器进程**，不影响你日常 Edge |
| 5 | 抓帧看门狗 | 连续 10 秒没有新帧就销毁并重建 WGC（30 秒限流），避免任务静默卡死 |

没有改动的：战斗逻辑、任务逻辑、识别阈值、输入方式，全部是 ok-ww 原版行为。

## 三、安装

1. 下载本仓库（`Code → Download ZIP`，或 `git clone`）
2. 双击 `install.cmd`
   - 会自动在 `D:\ok-ww`、`%USERPROFILE%\ok-ww`、`C:\ok-ww` 里找安装目录
   - 也可以手动指定：`install.cmd D:\ok-ww`
3. 脚本会打印验证结果（`WGC 可用: True` / `云窗口尺寸: (1600, 900)`）
4. **重启 ok-ww**，左上角设备下拉里选 **「云游戏 (Cloud)」**
5. 首次会弹出一个 1600×900 的 Edge 窗口，在里面登录通行证 → 点「进入游戏」，之后即可跑任务

登录态保存在 `working\cache\playwright`，下次不用重复登录。

## 四、卸载

```bat
uninstall.cmd D:\ok-ww
```

或手动删除：

```
<ok-ww>\data\apps\ok-ww\python\Lib\site-packages\okww_cloud.pth
<ok-ww>\data\apps\ok-ww\python\Lib\site-packages\okww_cloud_hook.py
```

删掉 `.pth` 就恢复原版行为，`okww_cloud_hook.py` 不加载不生效。

## 五、原理

```
<ok-ww>\data\apps\ok-ww\python\Lib\site-packages\
    okww_cloud.pth        ← 一行：import okww_cloud_hook
    okww_cloud_hook.py    ← 钩子本体
```

`.pth` 是 Python 的启动钩子：这个解释器每次启动都会执行它，从而在 `ok.util.window` / `config` / `ok.device.capture_methods.browser` 被导入后替换对应函数与配置值。

`.pth` 位于 `python\`（运行时目录），不在 ok-ww 的 git 工作区 `working\` 里，所以**版本更新不会覆盖**。整包重装（重新解压 7z）会丢，重跑一次 `install.cmd` 即可。

诊断日志：`<ok-ww>\data\apps\ok-ww\cloud\hook.log`

## 六、兼容性与限制

- 测试环境：ok-ww **v3.8.13** / Windows 10 **19044** / Edge 最新稳定版
- 需要系统支持 **Windows Graphics Capture**（Win10 1809+）并已安装 Edge
- 1080p 屏幕只能跑 1600×900，这是「窗口化 + 浏览器边框」的物理限制；要原生 1080p 只能用 kiosk 独占全屏，那与 ok-ww 的 Playwright 视口管理冲突，本补丁不做
- **不能**接管你自己通过 Edge 安装的「云·鸣潮」PWA 窗口：ok-ww 用的是自己启动的 Playwright 窗口（独立配置目录，需要单独登录一次）
- 第 4 项依赖 Edge 的特性名 `msEdgeMouseGestureSupported` / `msEdgeMouseGestureDefaultEnabled`，若微软改名则该条失效（其余不受影响）
- 请勿把这个窗口最大化：会破坏固定视口，导致抓帧失败

## 七、免责声明

- 本项目与 ok-ww 官方无关，仅提供运行时补丁，**不包含 ok-ww 的任何源码**
- 使用第三方自动化工具存在账号风险，请自行评估并遵守游戏用户协议
- 因使用本补丁造成的任何问题，作者不承担责任

## 八、许可

本仓库代码采用 MIT 许可证，详见 [LICENSE](LICENSE)。
