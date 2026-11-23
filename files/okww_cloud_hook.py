"""Enable ok-ww's built-in cloud (云鸣潮) capture on Windows 10.

Loaded by okww_cloud.pth from the bundled Python's site-packages, so every launch
path (desktop shortcut, Start menu, ok-ww.cmd) gets the patch without editing the
git-tracked app files. Delete okww_cloud.pth to disable.

What it changes at runtime:
  * ok.util.window.windows_graphics_available() accepts Windows 10 build 19041+
    instead of requiring 20348 (Win11 22H2), which is what hid the cloud device.
  * config['browser']['resolution'] becomes the largest 16:9 size the screen can
    actually hold, so the capture geometry check passes.
"""
import builtins
import ctypes
import os
import sys
import time
from ctypes import wintypes

_APP_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
_LOG = os.path.join(_APP_DIR, "cloud", "hook.log")


def _log(msg):
    try:
        os.makedirs(os.path.dirname(_LOG), exist_ok=True)
        with open(_LOG, "a", encoding="utf-8") as f:
            f.write(msg + "\n")
    except Exception:
        pass


def _work_area():
    try:
        rect = wintypes.RECT()
        ctypes.windll.user32.SystemParametersInfoW(0x0030, 0, ctypes.byref(rect), 0)
        return rect.right - rect.left, rect.bottom - rect.top
    except Exception:
        return 1920, 1040


def _pick_resolution(candidates):
    work_w, work_h = _work_area()
    for width, height in candidates:
        if width + 40 <= work_w and height + 130 <= work_h:
            return width, height
    return candidates[-1]


def _install_window_patch(module):
    if getattr(module, "_okww_cloud_patched", False):
        return
    build = getattr(module, "WINDOWS_BUILD_NUMBER", None)
    min_build = getattr(module, "WGC_MIN_BUILD", None)
    if build is None or min_build is None or not hasattr(module, "windows_graphics_available"):
        return  # module is still executing its import

    def windows_graphics_available():
        if build < min_build:
            return False
        try:
            from ok.rotypes.roapi import GetActivationFactory
            from ok.rotypes.Windows.Graphics.Capture import IGraphicsCaptureItemInterop
            GetActivationFactory("Windows.Graphics.Capture.GraphicsCaptureItem").astype(
                IGraphicsCaptureItemInterop)
            return True
        except Exception as error:
            _log(f"WGC activation failed: {error}")
            return False

    module.windows_graphics_available = windows_graphics_available
    module._okww_cloud_patched = True
    _log(f"patched ok.util.window build={build} min={min_build}")

    for name in ("ok.device.capture_methods.browser",
                 "ok.device.DeviceManager",
                 "ok.device.capture_methods.update"):
        loaded = sys.modules.get(name)
        if loaded is not None and hasattr(loaded, "windows_graphics_available"):
            loaded.windows_graphics_available = windows_graphics_available
            _log(f"patched {name}")

    _install_config_patch(sys.modules.get("config"))


def _install_config_patch(module):
    if module is None or getattr(module, "_okww_cloud_patched", False):
        return
    conf = getattr(module, "config", None)
    if not isinstance(conf, dict):
        return
    browser = conf.get("browser")
    if isinstance(browser, dict):
        candidates = conf.get("supported_resolution", {}).get("resize_to") or [(1600, 900), (1280, 720)]
        width, height = _pick_resolution(list(candidates))
        browser["resolution"] = (width, height)
        browser["nick"] = "云游戏 (Cloud)"
        # The --no-sandbox infobar Chromium shows for Playwright shifts the renderer
        # down ~47px. Dismissing it moves the viewport again, which changes ok-ww's
        # capture signature and tears down WGC mid-task. --test-type hides that bar.
        args = browser.get("args")
        if isinstance(args, list) and "--test-type" not in args:
            args.append("--test-type")
        _log(f"browser resolution -> {width}x{height}")
    module._okww_cloud_patched = True


def _install_browser_patch(module):
    cls = getattr(module, "BrowserCaptureMethod", None)
    if cls is None or not hasattr(module, "BrowserWGC") or getattr(cls, "_okww_watchdog", False):
        return

    # Edge's built-in mouse gestures run in the browser UI process, so page
    # scripts cannot block the right-drag. Turn the feature off for this browser
    # process only (the user's own Edge profiles are untouched) by folding the
    # gesture feature names into the single --disable-features switch.
    try:
        from playwright.async_api import BrowserType
        if not getattr(BrowserType, "_okww_args_patch", False):
            original_launch = BrowserType.launch_persistent_context

            async def launch_persistent_context(self, *args, **kwargs):
                raw = list(kwargs.get("args") or [])
                features = []
                kept = []
                for arg in raw:
                    if arg.startswith("--disable-features="):
                        features.extend(arg.split("=", 1)[1].split(","))
                    else:
                        kept.append(arg)
                for name in ("msEdgeMouseGestureSupported", "msEdgeMouseGestureDefaultEnabled"):
                    if name not in features:
                        features.append(name)
                kept.append("--disable-features=" + ",".join(dict.fromkeys(features)))
                kwargs["args"] = kept
                _log(f"browser args -> {kept[-1]}")
                return await original_launch(self, *args, **kwargs)

            BrowserType.launch_persistent_context = launch_persistent_context
            BrowserType._okww_args_patch = True
            _log("patched playwright launch args (edge mouse gestures disabled)")
    except Exception as error:
        _log(f"args patch failed: {error}")

    original = cls.do_get_frame_wait
    state = {"last": time.time(), "last_restart": 0.0}

    def do_get_frame_wait(self, timeout):
        frame = original(self, timeout)
        now = time.time()
        if frame is not None:
            state["last"] = now
            return frame
        page = getattr(self, "page", None)
        hwnd = getattr(self, "hwnd", 0)
        if not page or not hwnd:
            state["last"] = now
            return frame
        if now - state["last"] < 10 or now - state["last_restart"] < 30:
            return frame
        state["last_restart"] = now
        state["last"] = now
        try:
            if getattr(self, "wgc_capture", None) is not None:
                self.wgc_capture.close()
                self.wgc_capture = None
            self.wgc_capture = module.BrowserWGC(self)
            _log("watchdog: rebuilt WGC capture after 10s without frames")
        except Exception as error:
            _log(f"watchdog rebuild failed: {error}")
        return frame

    cls.do_get_frame_wait = do_get_frame_wait
    cls._okww_watchdog = True
    _log("patched BrowserCaptureMethod watchdog")


def _install_liberation_patch(module):
    """Treat a started liberation cooldown as a successful cast.

    BaseChar.click_liberation() confirms the ultimate by waiting 0.4s for the
    character's portrait text to vanish from the team bar (in_team()). On a
    streamed client at 1600x900 that template often keeps matching, so every cast
    is reported as "clicked liberation but no effect" and the character stands
    still retrying. A started cooldown is a far more reliable signal.
    """
    cls = getattr(module, "BaseChar", None)
    if cls is None or not hasattr(cls, "click_liberation") or getattr(cls, "_okww_liberation_fix", False):
        return
    original = cls.click_liberation

    def click_liberation(self, *args, **kwargs):
        result = original(self, *args, **kwargs)
        if result:
            return result
        try:
            if self.task.has_cd("liberation", self.index):
                self.task.in_liberation = True
                _log("liberation: cooldown started after click, treated as success")
                return True
        except Exception as error:
            _log(f"liberation fallback failed: {error}")
        return result

    cls.click_liberation = click_liberation
    cls._okww_liberation_fix = True
    _log("patched BaseChar.click_liberation (cooldown counts as success)")


def _apply_all():
    """Patch every relevant module that is currently loaded.

    __import__ returns the top-level package for plain ``import a.b.c``, so the
    leaf module has to be looked up in sys.modules instead of the return value.
    """
    for name, loaded in list(sys.modules.items()):
        if loaded is None:
            continue
        if name == "ok.util.window":
            _install_window_patch(loaded)
        elif name == "ok.device.capture_methods.browser":
            _install_browser_patch(loaded)
        elif name == "config":
            _install_config_patch(loaded)
        elif name == "src.char.BaseChar":
            _install_liberation_patch(loaded)


_real_import = builtins.__import__


def _patched_import(name, globals=None, locals=None, fromlist=(), level=0):
    module = _real_import(name, globals, locals, fromlist, level)
    try:
        if name == "config" or name == "ok" or name.startswith("ok.") or name.startswith("src."):
            _apply_all()
    except Exception as error:
        _log(f"patch error for {name}: {error}")
    return module


builtins.__import__ = _patched_import
