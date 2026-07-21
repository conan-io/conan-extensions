import json
import os
import re
import time

from conan.api.conan_api import ConanAPI
from conan.api.model import ListPattern
from conan.api.output import ConanOutput, cli_out_write
from conan.cli.command import conan_command, OnceArgument
from conan.errors import ConanException


# Eviction policies: how to pick which package binaries go first when over the limit.
#   lru     -> least-recently-used first (by the package folder's last-use time). Default
#              and recommended: keeps the packages you actually use.
#   oldest  -> oldest package revision first. NOTE: this sorts by the revision timestamp,
#              which may be a server-side timestamp, not the local install/use time.
#   largest -> biggest first (reclaims space fastest, but may evict a large package you use
#              constantly, forcing a slow re-download).
POLICIES = ("lru", "oldest", "largest")

_GB = 1000 ** 3

# Same units as Conan's own '--lru' time limits (conan remove --lru=5d).
_AGE_UNITS = {"y": 365 * 86400, "M": 30 * 86400, "w": 7 * 86400,
              "d": 86400, "h": 3600, "m": 60, "s": 1}


def _parse_max_size(text):
    """Parse the --max-size value (a number of gigabytes) into bytes."""
    try:
        gb = float(text)
    except (TypeError, ValueError):
        raise ConanException(f"Invalid --max-size '{text}': expected a number of GB, e.g. 10 or 0.5")
    if gb < 0:
        raise ConanException("Invalid --max-size: it cannot be negative")
    return int(gb * _GB)


def _parse_age(text):
    """Parse an age like '30d', '4w', '2h' into seconds (units y, M, w, d, h, m, s)."""
    match = re.fullmatch(r"\s*([0-9]+)\s*([yMwdhms])\s*", str(text))
    if not match:
        raise ConanException(f"Invalid age '{text}'. Use e.g. 30d, 4w, 2h "
                             f"(units: {', '.join(_AGE_UNITS)})")
    value, unit = match.groups()
    return int(value) * _AGE_UNITS[unit]


def _human_size(num_bytes):
    """Render a byte count as a short human-readable string (decimal units)."""
    size = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1000 or unit == "TB":
            return f"{int(size)}B" if unit == "B" else f"{size:.1f}{unit}"
        size /= 1000


def _folder_size(path):
    """Total size in bytes of all files under a folder (0 if it does not exist)."""
    total = 0
    for root, _dirs, files in os.walk(path):
        for name in files:
            try:
                total += os.path.getsize(os.path.join(root, name))
            except OSError:
                pass  # file vanished or not accessible, ignore
    return total


def _collect(conan_api):
    """Enumerate the cache. Returns (packages, recipes_size).

    packages: list of dicts {pref, size, created, lru} for every package binary.
    recipes_size: total bytes used by recipe folders (exports + cached sources).
    """
    pkglist = conan_api.list.select(ListPattern("*:*", rrev="*", prev="*"))

    packages = []
    recipes_size = 0
    for ref, prefs in pkglist.items():
        try:
            recipes_size += _folder_size(os.path.dirname(conan_api.cache.export_path(ref)))
        except ConanException:
            pass
        for pref, _info in prefs.items():
            try:
                base = os.path.dirname(conan_api.cache.package_path(pref))
            except ConanException:
                continue
            packages.append({
                "pref": pref,
                # Revision timestamp: note it may be a server-side timestamp, not the local
                # install time. Only used by the 'oldest' policy.
                "created": pref.timestamp or 0,
                "size": _folder_size(base),
                # Conan's own '--lru' recency is the base folder's mtime (see
                # PkgCache.get_package_lru); reuse the same signal, no DB access needed.
                "lru": os.path.getmtime(base),
            })
    return packages, recipes_size


def _sorted_for_eviction(packages, policy):
    """Order packages so the ones to evict first come first."""
    if policy == "largest":
        return sorted(packages, key=lambda p: p["size"], reverse=True)
    if policy == "oldest":
        return sorted(packages, key=lambda p: p["created"])
    # lru (default): least-recently-used first
    return sorted(packages, key=lambda p: p["lru"])


def _text_output(result):
    # Everything goes through cli_out_write (stdout) so the report keeps its order; the
    # trailing hint uses ConanOutput().warning() as it is supplementary (stderr).
    before = result["cache_size"]
    policy_desc = f"policy: {result['policy']}"
    if result["older_than"]:
        policy_desc += f", older-than: {result['older_than']}"
    lines = [
        f"Cache size:  {_human_size(before)} ({before} B)",
        f"Size limit:  {_human_size(result['max_size'])} ({result['max_size']} B)  [{policy_desc}]",
    ]

    removed = result["removed"]
    if not removed:
        if not result["over_limit"]:
            lines.append("Cache is within the size limit, nothing to remove.")
        elif result["protected"]:
            lines.append(f"Over the size limit, but all {result['protected']} eviction "
                         f"candidate(s) are protected by --older-than={result['older_than']}; "
                         f"nothing removed.")
        else:
            lines.append("Over the size limit, but there are no package binaries to evict "
                         "(only recipe/source folders remain). Try 'conan cache clean'.")
        cli_out_write("\n".join(lines))
        return

    lines.append(f"Removed {len(removed)} package binaries:")
    lines += [f"  {item['pref']}  ({_human_size(item['size'])})" for item in removed]
    after = result["size_after"]
    lines.append(f"Freed:       {_human_size(before - after)}")
    lines.append(f"New size:    {_human_size(after)}")
    cli_out_write("\n".join(lines))

    if result["over_limit"]:
        if result["protected"]:
            ConanOutput().warning(
                f"Could not get below the limit: {result['protected']} package(s) are protected "
                f"by --older-than={result['older_than']} (used too recently). Lower --older-than "
                f"or the size limit to evict more.")
        else:
            ConanOutput().warning(
                f"Could not get below the limit: package binaries alone are exhausted but "
                f"recipe/source folders still use {_human_size(result['recipes_size'])}. "
                f"Run 'conan cache clean' to drop cached sources/builds, or remove recipes.")


def _json_output(result):
    payload = {
        "cache_size": result["cache_size"],
        "max_size": result["max_size"],
        "size_after": result["size_after"],
        "policy": result["policy"],
        "older_than": result["older_than"],
        "over_limit": result["over_limit"],
        "protected": result["protected"],
        "recipes_size": result["recipes_size"],
        "removed": [{"ref": str(i["pref"]), "size": i["size"]} for i in result["removed"]],
    }
    cli_out_write(json.dumps(payload, indent=2))


@conan_command(group="Custom commands",
               formatters={"text": _text_output, "json": _json_output})
def clean_size(conan_api: ConanAPI, parser, *args):
    """
    Prune the local Conan cache down to a maximum size by removing package binaries.

    Package binaries are removed (least-recently-used first) until the cache fits within
    --max-size. This is a different operation from 'conan cache clean', which instead frees the
    source/build/download temp folders of cached packages; here, whole package binaries are
    removed. Removal only happens when you explicitly run this command.
    """
    parser.add_argument("--max-size", action=OnceArgument, required=True,
                        help="Maximum cache size in GB, e.g. 10 or 0.5. The cache is pruned until "
                             "it fits within this size.")
    parser.add_argument("--policy", action=OnceArgument, default="lru", choices=POLICIES,
                        help="Eviction order when over the limit (default: lru). lru=least-recently-"
                             "used first; oldest=oldest package revision first (by revision "
                             "timestamp, which may be server-side rather than local install time); "
                             "largest=biggest first.")
    parser.add_argument("--older-than", action=OnceArgument, default=None,
                        help="Only evict packages not used for at least this long, e.g. 30d, 4w, "
                             "2h (units: y, M, w, d, h, m, s). Recently-used packages are kept even "
                             "if the cache is over the limit, to avoid re-downloading them.")
    args = parser.parse_args(*args)

    max_size = _parse_max_size(args.max_size)
    # A package is protected (never evicted) if it was last used more recently than this cutoff.
    cutoff = time.time() - _parse_age(args.older_than) if args.older_than else None

    packages, recipes_size = _collect(conan_api)
    cache_size = recipes_size + sum(p["size"] for p in packages)

    removed = []
    protected = 0
    current = cache_size
    for item in _sorted_for_eviction(packages, args.policy):
        if current <= max_size:  # stop as soon as we are under the limit
            break
        if cutoff is not None and item["lru"] > cutoff:
            protected += 1  # used too recently, keep it
            continue
        try:
            conan_api.remove.package(item["pref"])
        except ConanException as e:
            # e.g. a folder locked by another process (common on Windows): skip it and keep
            # going, and keep size_after honest by not crediting the space.
            ConanOutput().warning(f"Could not remove {item['pref']}: {e}")
            continue
        removed.append(item)
        current -= item["size"]

    return {
        "cache_size": cache_size,
        "max_size": max_size,
        "size_after": current,
        "policy": args.policy,
        "older_than": args.older_than,
        "recipes_size": recipes_size,
        "protected": protected,
        "over_limit": current > max_size,
        "removed": removed,
    }
