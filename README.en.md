# ok-ww Cloud Patch (Windows 10)

[![platform](https://img.shields.io/badge/platform-Windows%2010%2B-blue)](https://github.com/Moore-king/okww-cloud-patch)
[![ok-ww](https://img.shields.io/badge/ok--ww-v3.8.13-informational)](https://github.com/ok-oldking/ok-wuthering-waves)
[![license](https://img.shields.io/badge/license-MIT-green)](LICENSE)

Enables the built-in **cloud gaming** mode of [ok-ww](https://github.com/ok-oldking/ok-wuthering-waves)
on **Windows 10**, so it can capture and automate the browser version of
**Wuthering Waves Cloud** (`mc.kurogames.com/cloud`).

> No ok-ww source file is modified — two files are dropped into its bundled Python.
> ok-ww's git-based updates keep working.

中文说明见 [README.md](README.md)。

## The problem

ok-ww's cloud mode (Playwright + Windows Graphics Capture) has three blockers on Windows 10:

1. **The cloud device never appears.**
   `windows_graphics_available()` only returns `True` when the OS build is ≥ **20348**
   (Win11 22H2 / Server 2022). On Win10 the check fails, and
   `DeviceManager.update_browser_device()` is skipped entirely.

2. **Even when forced on, no frames arrive.**
   The cloud viewport is hard-coded to 1920×1080, but a browser window needs ~130px of
   chrome, which does not fit a 1080p screen. Chromium shrinks the window, the renderer
   ends up 1916×961, and ok-ww's geometry check rejects it forever.

3. **Capture dies mid-task.**
   Chromium shows an "unsupported command-line flag: --no-sandbox" infobar; dismissing it
   shifts the renderer, ok-ww sees a changed capture target, tears down WGC, and the task
   hangs waiting for frames that never come.

## What the patch changes

| # | Change | Why |
|---|---|---|
| 1 | WGC gate `20348` → `19041` | WGC itself works on Win10 1809+; 19041 is ok-ww's own `WGC_MIN_BUILD` |
| 2 | Cloud viewport auto-fit | Picks the largest 16:9 that fits the screen (1600×900 on 1080p) |
| 3 | Adds `--test-type` | Removes the `--no-sandbox` infobar, so the renderer offset stays constant |
| 4 | Disables Edge mouse gestures | Gestures run in the browser UI process and would navigate the page away; scoped to the browser process ok-ww starts |
| 5 | Capture watchdog | Rebuilds WGC after 10s without frames (30s rate limit) instead of hanging |
| 6 | Liberation check by cooldown | The original check waits for the portrait to vanish, which is unreliable on compressed video; a started cooldown is a hard signal |

Nothing else is touched: combat logic, tasks, thresholds and input stay stock.

## Why Windows 10 works

Windows Graphics Capture exists since Windows 10 1803 (17134). ok-ww defines two constants:

```python
WGC_MIN_BUILD = 19041            # minimum for WGC itself
WGC_NO_BORDER_MIN_BUILD = 20348  # minimum for IsBorderRequired (no capture border)
```

`windows_graphics_available()` uses the second one, so on Win10 the function returns `False`.
Measured on Windows 10 19044 with Edge and Wuthering Waves Cloud:

- WGC captures the Edge window including the WebRTC video, complete frames
- The only visible difference is a system-drawn yellow capture border around the window
- ok-ww crops to the renderer rect, so the border falls outside the capture and does not affect recognition

## Install

1. Download this repository (`Code → Download ZIP` or `git clone`)
2. Run `install.cmd`
   - It looks for ok-ww in `D:\ok-ww`, `%USERPROFILE%\ok-ww`, `C:\ok-ww`
   - Or pass the path: `install.cmd D:\ok-ww`
3. The script prints a verification result (`WGC available: True`, `cloud viewport: (1600, 900)`)
4. **Restart ok-ww**, then choose **"Cloud"** in the device dropdown
5. A 1600×900 Edge window opens — log in once and click the play button

## Uninstall

```bat
uninstall.cmd D:\ok-ww
```

Deleting `okww_cloud.pth` alone is enough to disable the patch.

## FAQ

- **Device shows Disconnected** — expected; the browser starts when you begin a task.
- **Login every time?** — no, the session lives in `working\cache\playwright`.
- **Lost after an ok-ww update?** — no, the patch lives in `python\Lib\site-packages`;
  only a full re-extract of the 7z package removes it. Re-run `install.cmd`.
- **Native 1080p?** — not in windowed mode; 1600×900 on a 1080p screen, 1920×1080 on 2K/4K.
- **Logs** — `working\logs\ok-script.log` and `data\apps\ok-ww\cloud\hook.log`.

## Disclaimer

Not affiliated with ok-ww. Contains no ok-ww source code. Using automation tools may put
your game account at risk — evaluate that yourself and follow the game's terms.

## License

MIT, see [LICENSE](LICENSE).
