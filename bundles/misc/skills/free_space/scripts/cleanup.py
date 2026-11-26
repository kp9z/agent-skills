"""Clear regenerable caches on the current user's Mac."""
import argparse
import os
from pathlib import Path
import plistlib
import re
import shutil
import subprocess
import sys

GIB = 1024 ** 3
XCODE_CACHES = (
    "ModuleCache.noindex", "CompilationCache.noindex", "Index.noindex",
    "SDKStatCaches.noindex", "SDKExplicitPrecompiledModules",
)
BUSY = {
    "Xcode": ("xcode", "xcodebuild", "xcbuildservice", "xcbbuildservice",
              "xctest", "swift-frontend", "swiftc", "clang", "clang++", "swift-build"),
    "npm": ("npm", "npx", "pnpm", "yarn"),
    "pip": ("pip",),
    "Homebrew": ("brew",),
    "Chrome": ("google chrome",),
    "Brave": ("brave browser",),
}


def owned_dir(path):
    return (path.is_dir() and path.resolve() == path
            and path.stat().st_uid == os.getuid() and not path.is_mount())


def xcode_paths(home, temp):
    default = home / "Library/Developer/Xcode/DerivedData"
    if owned_dir(default):
        yield from (default / name for name in XCODE_CACHES)
    candidates = list(default.glob("*")) if owned_dir(default) else []
    for pattern in ("*-[Dd][Dd]", "[Ss]kin[Ss]ense-*", "InsightsDesign-*"):
        candidates.extend(temp.glob(pattern))
    candidates.extend(temp.glob("skinsense-marathon-*/*/DerivedData"))
    visuals = home / ".codex/visualizations"
    candidates.extend(visuals.glob("*/*/*/*/marathon/output/*/DerivedData"))
    for root in dict.fromkeys(candidates):
        if "worktree-cleanup-preservation" in root.parts or not owned_dir(root):
            continue
        info = root / "info.plist"
        try:
            if not info.is_file() or info.is_symlink() or info.stat().st_size > 65536:
                continue
            with info.open("rb") as f:
                metadata = plistlib.load(f)
        except (OSError, ValueError, plistlib.InvalidFileException):
            continue
        if isinstance(metadata, dict) and metadata.get("WorkspacePath"):
            for name in (*XCODE_CACHES, "Build/Products", "Build/Intermediates.noindex"):
                yield root / name


def cache_paths(home, temp):
    caches = home / "Library/Caches"
    yield "npm", home / ".npm/_cacache"
    for name in ("http", "http-v2", "wheels"):
        yield "pip", caches / "pip" / name
    downloads = caches / "Homebrew/downloads"
    if owned_dir(downloads):
        for file in downloads.iterdir():
            if re.fullmatch(r"[0-9a-f]{64}--.+", file.name) and not file.name.endswith(".incomplete"):
                if file.is_file():
                    yield "Homebrew", file
    for group, folder in (("Chrome", "Google/Chrome"), ("Brave", "BraveSoftware/Brave-Browser")):
        browser = caches / folder
        if owned_dir(browser):
            for profile in browser.iterdir():
                if profile.name == "Default" or re.fullmatch(r"Profile [0-9]+", profile.name):
                    for name in ("Cache", "Code Cache"):
                        yield group, profile / name
    for path in xcode_paths(home, temp):
        yield "Xcode", path


def busy_groups():
    commands = subprocess.check_output(["/bin/ps", "-axo", "comm="], text=True)
    names = {Path(line.strip()).name.lower() for line in commands.splitlines()}
    busy = {group for group, prefixes in BUSY.items()
            if any(name.startswith(prefixes) for name in names)}
    # pip can run through an interpreter whose process name is simply python.
    args = subprocess.check_output(["/bin/ps", "-axo", "args="], text=True)
    if re.search(r"(?:^|\s)(?:-m\s+pip|\S*/pip[\d.]*)\s", args, re.MULTILINE):
        busy.add("pip")
    if re.search(r"(?:^|\s)\S*/(?:npm-cli\.js|npx-cli\.js|pnpm\.c?js|yarn\.js|bin/(?:npm|npx|pnpm|yarn))(?:\s|$)", args, re.MULTILINE):
        busy.add("npm")
    if re.search(r"/(?:Homebrew/Library/Homebrew/|bin/brew(?:\s|$))", args, re.MULTILINE):
        busy.add("Homebrew")
    return busy


def eligible(path):
    return (path.exists() and path.resolve() == path and not path.is_mount()
            and path.stat().st_uid == os.getuid()
            and (path.is_dir() or path.is_file()))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="remove eligible idle caches")
    apply = parser.parse_args().apply
    if sys.platform != "darwin" or os.getuid() == 0:
        parser.error("Run on macOS as the ordinary local user.")
    home = Path.home().resolve()
    before = shutil.disk_usage(home).free
    busy = busy_groups()
    targets = {group: [] for group in BUSY}
    for group, path in cache_paths(home, Path("/private/tmp")):
        if eligible(path):
            targets[group].append(path)
    failed = False
    for group, paths in targets.items():
        if not paths:
            continue
        if group in busy or (apply and group in busy_groups()):
            print(f"Skipped {group}: active process", flush=True)
            continue
        try:
            rows = subprocess.check_output(["/usr/bin/du", "-sk", *map(str, paths)], text=True)
            size = sum(int(row.split("\t", 1)[0]) for row in rows.splitlines()) * 1024
            if apply:
                for path in paths:
                    if eligible(path):
                        if path.is_dir():
                            shutil.rmtree(path)
                        else:
                            path.unlink()
            print(f"{'Cleared' if apply else 'Eligible'} {group}: {size / GIB:.2f} GiB", flush=True)
        except (OSError, subprocess.CalledProcessError) as exc:
            print(f"Incomplete {group}: {exc}", file=sys.stderr)
            failed = True
    after = shutil.disk_usage(home).free
    print(f"Free: {after / GIB:.2f} GiB (change {(after - before) / GIB:+.2f} GiB)")
    return int(failed)


if __name__ == "__main__":
    sys.exit(main())
