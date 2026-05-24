# -*- coding: utf-8 -*-
"""
Update Checker for NVDA Add-on
Checks for new versions on GitHub releases at NVDA startup.
Downloads and installs updates automatically.
"""

import threading
import json
import re
import os
import tempfile
import shutil
import gc
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

try:
    import wx
    import gui
    import ui
    import core
    import globalVars
    from logHandler import log
    WX_AVAILABLE = True
except ImportError:
    WX_AVAILABLE = False
    import logging
    log = logging.getLogger(__name__)

import addonHandler
addonHandler.initTranslation()

GITHUB_API_URL = "https://api.github.com/repos/JoaoDEVWHADS/nvda-smart-captcha-solver/releases/latest"
USER_AGENT = "NVDA-SmartCaptchaSolver-UpdateChecker/1.0"
ADDON_NAME = "smartCaptchaSolver"
ADDON_FRIENDLY_NAME = "Smart Captcha Solver"

try:
    CURRENT_VERSION = addonHandler.getCodeAddon().manifest.get('version', '2026.01.12')
except Exception:
    CURRENT_VERSION = "2026.01.12"


def parse_version(version_string: str) -> tuple:
    """
    Parse version string into comparable tuple.
    """
    match = re.search(r'(\d{4})[\.\-](\d{1,2})[\.\-](\d{1,2})(?:[\.\-_](\d+))?', version_string)
    if match:
        parts = []
        for x in match.groups():
            if x is not None:
                parts.append(int(x))
        return tuple(parts)

    match = re.search(r'(\d+)\.(\d+)\.(\d+)(?:\.(\d+))?', version_string)
    if match:
        parts = []
        for x in match.groups():
            if x is not None:
                parts.append(int(x))
        return tuple(parts)

    numbers = re.findall(r'\d+', version_string)
    if len(numbers) >= 3:
        return tuple(int(x) for x in numbers[:4])

    return (0, 0, 0)


def compare_versions(current: str, remote: str) -> int:
    current_tuple = parse_version(current)
    remote_tuple = parse_version(remote)

    if current_tuple < remote_tuple:
        return -1
    elif current_tuple > remote_tuple:
        return 1
    return 0


def fetch_latest_release() -> dict:
    try:
        log.info(f"{ADDON_FRIENDLY_NAME}: Checking for updates from GitHub...")

        request = Request(GITHUB_API_URL, headers={'User-Agent': USER_AGENT})

        with urlopen(request, timeout=15) as response:
            data = json.loads(response.read().decode('utf-8'))

        download_url = None
        version = None
        asset_name = None
        found_assets = []

        if 'assets' not in data or not data['assets']:
            log.warning(f"{ADDON_FRIENDLY_NAME}: Release {data.get('name', 'Unknown')} has NO assets attached. Cannot update.")
            return None

        for asset in data.get('assets', []):
            name = asset.get('name', '')
            found_assets.append(name)
            
            if name.lower().endswith('.nvda-addon'):
                download_url = asset.get('browser_download_url')
                asset_name = name

                version_tuple = parse_version(name)
                if version_tuple[0] >= 2000:
                    if len(version_tuple) >= 4:
                        version = f"{version_tuple[0]}.{version_tuple[1]:02d}.{version_tuple[2]:02d}.{version_tuple[3]}"
                    else:
                        version = f"{version_tuple[0]}.{version_tuple[1]:02d}.{version_tuple[2]:02d}"
                else:
                    if len(version_tuple) >= 4:
                        version = f"{version_tuple[0]}.{version_tuple[1]}.{version_tuple[2]}.{version_tuple[3]}"
                    else:
                        version = f"{version_tuple[0]}.{version_tuple[1]}.{version_tuple[2]}"
                break

        if not download_url:
            log.warning(f"{ADDON_FRIENDLY_NAME}: No .nvda-addon asset found in latest release")
            return None

        return {
            'version': version,
            'download_url': download_url,
            'release_name': data.get('name', 'Unknown'),
            'body': data.get('body', ''),
            'tag_name': data.get('tag_name', ''),
            'asset_name': asset_name
        }

    except HTTPError as e:
        log.error(f"{ADDON_FRIENDLY_NAME}: HTTP error fetching release info: {e.code} {e.reason}")
        return None
    except URLError as e:
        log.error(f"{ADDON_FRIENDLY_NAME}: URL error fetching release info: {e.reason}")
        return None
    except json.JSONDecodeError as e:
        log.error(f"{ADDON_FRIENDLY_NAME}: JSON decode error: {e}")
        return None
    except Exception as e:
        log.error(f"{ADDON_FRIENDLY_NAME}: Unexpected error fetching release info: {e}")
        return None


def download_addon(download_url: str, asset_name: str = None) -> str:
    try:
        log.info(f"{ADDON_FRIENDLY_NAME}: Downloading update from {download_url}")

        temp_dir = tempfile.mkdtemp(prefix="nvda_addon_update_")

        if not asset_name:
            asset_name = download_url.split('/')[-1]
        if not asset_name.endswith('.nvda-addon'):
            asset_name = f"{ADDON_NAME}.nvda-addon"

        download_path = os.path.join(temp_dir, asset_name)

        request = Request(download_url, headers={'User-Agent': USER_AGENT})

        with urlopen(request, timeout=120) as response:
            with open(download_path, 'wb') as f:
                total_size = int(response.headers.get('Content-Length', 0))
                downloaded = 0
                chunk_size = 8192

                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)

        log.info(f"{ADDON_FRIENDLY_NAME}: Download complete: {download_path} ({downloaded} bytes)")
        return download_path

    except Exception as e:
        log.error(f"{ADDON_FRIENDLY_NAME}: Failed to download update: {e}")
        return None


def install_addon(addon_path: str) -> bool:
    try:
        log.info(f"{ADDON_FRIENDLY_NAME}: Installing update from {addon_path}")

        import addonHandler

        bundle = addonHandler.AddonBundle(addon_path)

        gc.collect()

        try:
            for addon in addonHandler.getAvailableAddons():
                if addon.name == ADDON_NAME:
                    log.info(f"{ADDON_FRIENDLY_NAME}: Requesting removal of existing version {addon.version}")
                    if not addon.isPendingRemove:
                        addon.requestRemove()
                    break
        except Exception as e:
            log.warning(f"{ADDON_FRIENDLY_NAME}: Failed to check/remove existing addon: {e}")

        import gui

        gui.ExecAndPump(addonHandler.installAddonBundle, bundle)

        log.info(f"{ADDON_FRIENDLY_NAME}: Add-on installed successfully. NVDA restart required.")

        def cleanup():
            try:
                temp_dir = os.path.dirname(addon_path)
                if temp_dir and os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir, ignore_errors=True)
            except:
                pass

        threading.Timer(5.0, cleanup).start()

        return True

    except Exception as e:
        log.error(f"{ADDON_FRIENDLY_NAME}: Failed to install update: {e}")
        error_msg = str(e)
        if WX_AVAILABLE and ("[WinError 5]" in error_msg or "PermissionError" in error_msg or "Access is denied" in error_msg):
            message = _(
                "Update failed because files are in use.\n\n"
                "Please RESTART NVDA and try updating immediately,\n"
                "WITHOUT opening the add-on settings."
            )
            wx.CallAfter(wx.MessageBox, message, _("Update Failed - Files Locked"), wx.OK | wx.ICON_ERROR)
        return False


class UpdateChecker:
    def __init__(self, on_update_available_callback=None):
        self.callback = on_update_available_callback
        self._check_lock = threading.Lock()
        self._checked = False

    def start(self):
        if not WX_AVAILABLE:
            log.warning(f"{ADDON_FRIENDLY_NAME}: wx not available, update checker disabled")
            return

        if self._checked:
            log.debug(f"{ADDON_FRIENDLY_NAME}: Update already checked this session")
            return

        wx.CallLater(5000, self._start_check)

        log.info(f"{ADDON_FRIENDLY_NAME}: Update checker initialized (will check in 5 seconds)")

    def stop(self):
        log.debug(f"{ADDON_FRIENDLY_NAME}: Update checker stopped")

    def _start_check(self):
        thread = threading.Thread(target=self._do_check, daemon=True)
        thread.start()

    def _do_check(self):
        with self._check_lock:
            if self._checked:
                return
            self._checked = True

            log.info(f"{ADDON_FRIENDLY_NAME}: Checking for updates...")

            release_info = fetch_latest_release()

            if not release_info:
                log.info(f"{ADDON_FRIENDLY_NAME}: Could not fetch release info from GitHub")
                return

            remote_version = release_info['version']
            comparison = compare_versions(CURRENT_VERSION, remote_version)

            if comparison < 0:
                log.info(f"{ADDON_FRIENDLY_NAME}: UPDATE AVAILABLE! Current: {CURRENT_VERSION} -> New: {remote_version}")
                log.info(f"{ADDON_FRIENDLY_NAME}: Release: {release_info.get('release_name', 'Unknown')}")
                log.info(f"{ADDON_FRIENDLY_NAME}: Download URL: {release_info['download_url']}")

                if self.callback:
                    wx.CallAfter(
                        self.callback,
                        remote_version,
                        release_info['download_url'],
                        release_info
                    )
            else:
                log.info(f"{ADDON_FRIENDLY_NAME}: No update available. Current version ({CURRENT_VERSION}) is up to date.")


class UpdateNotificationDialog(wx.Dialog):
    def __init__(self, parent, current_version: str, new_version: str,
                 download_url: str, release_info: dict = None):
        super().__init__(
            parent,
            title=_("Update Available - Smart Captcha Solver"),
            style=wx.DEFAULT_DIALOG_STYLE | wx.STAY_ON_TOP
        )

        self.download_url = download_url
        self.new_version = new_version
        self.release_info = release_info
        self.current_version = current_version

        self._init_ui(current_version, new_version, release_info)
        self.CenterOnScreen()

    def _init_ui(self, current_version: str, new_version: str, release_info: dict):
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        message = _(
            "A new version of Smart Captcha Solver is available!\n\n"
            "Current version: {current}\n"
            "New version: {new}\n\n"
            "Click 'Download and Install' to update automatically."
        ).format(current=current_version, new=new_version)

        message_label = wx.StaticText(self, label=message)
        message_label.Wrap(400)
        main_sizer.Add(message_label, flag=wx.ALL, border=15)

        if release_info and release_info.get('release_name'):
            release_name = wx.StaticText(
                self,
                label=_("Release: {}").format(release_info['release_name'])
            )
            main_sizer.Add(release_name, flag=wx.LEFT | wx.RIGHT, border=15)

        button_sizer = wx.BoxSizer(wx.HORIZONTAL)

        download_btn = wx.Button(self, label=_("&Download and Install"))
        download_btn.Bind(wx.EVT_BUTTON, self._on_download_install)
        download_btn.SetDefault()
        button_sizer.Add(download_btn, flag=wx.RIGHT, border=10)

        close_btn = wx.Button(self, wx.ID_CLOSE, _("&Close"))
        close_btn.Bind(wx.EVT_BUTTON, lambda e: self.Close())
        button_sizer.Add(close_btn)

        main_sizer.Add(button_sizer, flag=wx.ALL | wx.ALIGN_CENTER, border=15)

        self.SetSizer(main_sizer)
        self.Fit()

    def _on_download_install(self, event):
        self.Close()

        ui.message(_("Downloading update... Please wait."))
        log.info(f"{ADDON_FRIENDLY_NAME}: User initiated download and install")

        thread = threading.Thread(
            target=self._do_download_install,
            daemon=True
        )
        thread.start()

    def _do_download_install(self):
        try:
            asset_name = self.release_info.get('asset_name') if self.release_info else None
            download_path = download_addon(self.download_url, asset_name)

            if not download_path:
                wx.CallAfter(ui.message, _("Error: Failed to download update"))
                return

            success = install_addon(download_path)

            if success:
                wx.CallAfter(self._prompt_restart)
            else:
                wx.CallAfter(ui.message, _("Error: Failed to install update"))

        except Exception as e:
            log.error(f"{ADDON_FRIENDLY_NAME}: Download/install failed: {e}")
            wx.CallAfter(ui.message, _("Error: Update failed. Check NVDA log for details."))

    def _prompt_restart(self):
        ui.message(_("Update installed successfully! NVDA needs to restart."))

        result = gui.messageBox(
            _("Smart Captcha Solver has been updated to version {version}.\n\n"
              "NVDA must be restarted for the update to take effect.\n\n"
              "Restart NVDA now?").format(version=self.new_version),
            _("Update Installed"),
            wx.YES_NO | wx.ICON_QUESTION
        )

        if result == wx.YES:
            log.info(f"{ADDON_FRIENDLY_NAME}: Restarting NVDA after update")
            core.restart()


def show_update_dialog(current_version: str, new_version: str,
                       download_url: str, release_info: dict = None):
    if not WX_AVAILABLE:
        return

    try:
        dialog = UpdateNotificationDialog(
            gui.mainFrame,
            current_version,
            new_version,
            download_url,
            release_info
        )
        gui.mainFrame.prePopup()
        dialog.ShowModal()
        dialog.Destroy()
        gui.mainFrame.postPopup()
    except Exception as e:
        log.error(f"{ADDON_FRIENDLY_NAME}: Error showing update dialog: {e}")
