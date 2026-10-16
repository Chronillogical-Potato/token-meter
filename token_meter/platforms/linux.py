"""Linux/XDG path and lifecycle policy."""

import os

from .base import CpuActivity, PlatformPaths, TrashPlan
from .common import PosixPlatformServices, expand_home


POWER_SUPPLY_ROOT = "/sys/class/power_supply"
POWER_SUPPLY_MAX_ENTRIES = 32
PROC_STAT_PATH = "/proc/stat"


def parse_proc_stat(text):
    """Return aggregate CPU ticks from ``/proc/stat`` text, or None."""
    for line in str(text or "").splitlines():
        fields = line.split()
        if not fields or fields[0] != "cpu":
            continue
        try:
            values = [int(value) for value in fields[1:9]]
        except ValueError:
            return None
        if len(values) < 4:
            return None
        values += [0] * (8 - len(values))
        user, nice, system, idle, iowait, irq, softirq, steal = values
        return CpuActivity(
            busy=user + nice + system + irq + softirq + steal,
            idle=idle + iowait,
        )
    return None


def _read_supply_value(root, name, field):
    try:
        with open(os.path.join(root, name, field), encoding="utf-8") as handle:
            return handle.read(64).strip()
    except (OSError, UnicodeDecodeError):
        return ""


class LinuxPlatformServices(PosixPlatformServices):
    platform_id = "linux"

    def resolve_paths(self):
        config_home = self._environment_path("XDG_CONFIG_HOME", "~/.config")
        data_home = self._environment_path("XDG_DATA_HOME", "~/.local/share")
        cache_home = self._environment_path("XDG_CACHE_HOME", "~/.cache")
        return PlatformPaths(
            config_home=config_home,
            data_home=data_home,
            cache_home=cache_home,
            claude_desktop_data_roots=(
                os.path.join(config_home, "Claude"),
                os.path.join(config_home, "Claude-3p"),
            ),
            cursor_state_db=os.path.join(
                config_home, "Cursor", "User", "globalStorage", "state.vscdb"
            ),
            cursor_request_logs=os.path.join(config_home, "Cursor", "logs"),
            opencode_data_root=os.path.join(data_home, "opencode"),
            opencode_cache_root=os.path.join(cache_home, "opencode"),
            default_trash_dir=os.path.join(data_home, "Trash", "files"),
        )

    def trash_plan(self, path, override=None, command_available=False):
        if not override and command_available:
            return TrashPlan(
                supported=True,
                strategy="command",
                destination_label="Trash",
                command=("gio", "trash", str(path)),
            )
        destination_root = (
            expand_home(override, self.home)
            if override
            else self.resolve_paths().default_trash_dir
        )
        return TrashPlan(
            supported=True,
            strategy="move",
            destination_root=destination_root,
            destination_label="Trash",
        )

    def cpu_activity(self, path=PROC_STAT_PATH):
        try:
            with open(path, encoding="utf-8") as handle:
                return parse_proc_stat(handle.read(4096))
        except (OSError, UnicodeDecodeError):
            return None

    def power_constrained(self, root=POWER_SUPPLY_ROOT):
        try:
            names = sorted(os.listdir(root))[:POWER_SUPPLY_MAX_ENTRIES]
        except OSError:
            return None
        mains_offline = mains_online = battery_discharging = False
        for name in names:
            # Peripheral batteries (mice, headsets) report scope "Device".
            if _read_supply_value(root, name, "scope") == "Device":
                continue
            kind = _read_supply_value(root, name, "type")
            online = _read_supply_value(root, name, "online")
            if kind in ("Mains", "USB") and online == "1":
                mains_online = True
            elif kind == "Mains" and online == "0":
                mains_offline = True
            elif kind == "Battery":
                if _read_supply_value(root, name, "status") == "Discharging":
                    battery_discharging = True
        if mains_online:
            return False
        # An offline mains adapter means the host is running from its battery;
        # an idle USB-C port alone says nothing about the host's power source.
        if battery_discharging or mains_offline:
            return True
        return None
