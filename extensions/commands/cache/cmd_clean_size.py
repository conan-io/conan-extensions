import json
import os
import re
import time

from conan.api.conan_api import ConanAPI
from conan.api.input import UserInput
from conan.api.model import ListPattern
from conan.api.output import ConanOutput, cli_out_write
from conan.cli.command import conan_command, OnceArgument
from conan.errors import ConanException
from conan.internal.util.files import human_size


# Eviction policies: how to pick which package binaries go first when the cache
# is over the size limit.
#   lru     -> least-recently-used first (by last-access time). Default and recommended:
#              keeps the packages you actually use, evicts the ones gathering dust.
#   oldest  -> oldest first (by revision creation time, i.e. FIFO).
#   largest -> biggest first (reclaims space fastest, but may evict a large package
#              you use constantly, forcing a slow re-download).
POLICIES = ("lru", "oldest", "largest")

_SIZE_UNITS = {
    "": 1, "b": 1,
    "kb": 1000, "mb": 1000 ** 2, "gb": 1000 ** 3, "tb": 1000 ** 4,
    "k": 1024, "m": 1024 ** 2, "g": 1024 ** 3, "t": 1024 ** 4,
    "kib": 1024, "mib": 1024 ** 2, "gib": 1024 ** 3, "tib": 1024 ** 4,
}

# A unit-less number smaller than this is almost certainly a forgotten unit (e.g. '10'
# meaning 10GB, not 10 bytes). Since such a tiny limit would evict basically the whole
# cache, we refuse it: clearing the cache is what 'conan remove "*:*"' is for.
_MIN_UNITLESS_BYTES = 1024 ** 2


def _parse_size(text):
    """Parse a human size like '10GB', '500MiB', '2g' or a plain byte count into bytes.

    Decimal suffixes (kb, mb, gb, tb) use 1000; binary suffixes (kib/k, mib/m, ...) use 1024.
    A bare number is bytes, but a suspiciously small bare number is rejected as a likely typo.
    """
    match = re.fullmatch(r"\s*([0-9]*\.?[0-9]+)\s*([a-zA-Z]*)\s*", str(text))
    if not match:
        raise ConanException(f"Invalid size '{text}'. Use e.g. 10GB, 500MiB, 2g or a byte count")
    number, unit = match.groups()
    factor = _SIZE_UNITS.get(unit.lower())
    if factor is None:
        raise ConanException(f"Unknown size unit '{unit}'. Valid units: "
                             f"{', '.join(u for u in _SIZE_UNITS if u)}")
    size = int(float(number) * factor)
    if not unit and size < _MIN_UNITLESS_BYTES:
        raise ConanException(
            f"'{text}' looks like a forgotten unit: as bytes it is a tiny limit that would evict "
            f"almost the whole cache. Add a unit, e.g. '{number}MB' or '{number}GB' (use "
            f"'{number}B' if you really do mean bytes). To clear the cache, use "
            f"'conan remove \"*:*\"'.")
    return size


# Same units as Conan's own '--lru' time limits (conan remove --lru=5d).
_AGE_UNITS = {"y": 365 * 86400, "M": 30 * 86400, "w": 7 * 86400,
              "d": 86400, "h": 3600, "m": 60, "s": 1}


def _parse_age(text):
    """Parse an age like '30d', '4w', '2h' into seconds (units y, M, w, d, h, m, s)."""
    match = re.fullmatch(r"\s*([0-9]+)\s*([yMwdhms])\s*", str(text))
    if not match:
        raise ConanException(f"Invalid age '{text}'. Use e.g. 30d, 4w, 2h "
                             f"(units: {', '.join(_AGE_UNITS)})")
    value, unit = match.groups()
    return int(value) * _AGE_UNITS[unit]


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
                "size": _folder_size(base),
                "created": pref.timestamp or 0,
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
        f"Cache size:  {human_size(before)} ({before} B)",
        f"Size limit:  {human_size(result['max_size'])} ({result['max_size']} B)"
        f"  [{policy_desc}]",
    ]

    if result["cancelled"]:
        lines.append("Cancelled, nothing removed.")
        cli_out_write("\n".join(lines))
        return

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

    verb = "Would remove" if result["dry_run"] else "Removed"
    lines.append(f"{verb} {len(removed)} package binaries:")
    lines += [f"  {item['pref']}  ({human_size(item['size'])})" for item in removed]

    after = result["size_after"]
    lines.append(f"Freed:       {human_size(before - after)}")
    lines.append(f"New size:    {human_size(after)}"
                 f"{' (dry-run, nothing deleted)' if result['dry_run'] else ''}")
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
                f"recipe/source folders still use {human_size(result['recipes_size'])}. "
                f"Run 'conan cache clean' to drop cached sources/builds, or remove recipes.")


def _json_output(result):
    payload = {
        "cache_size": result["cache_size"],
        "max_size": result["max_size"],
        "size_after": result["size_after"],
        "policy": result["policy"],
        "older_than": result["older_than"],
        "dry_run": result["dry_run"],
        "cancelled": result["cancelled"],
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
    Prune the local Conan cache down to a maximum size, evicting package binaries by a policy.

    This is the "clean by size" counterpart to the built-in 'conan cache clean' (which only
    wipes source/build/download temp folders). Here, whole package binaries are removed until
    the cache fits within --max-size. Removal is always explicit (this command), never automatic.
    """
    parser.add_argument("--max-size", action=OnceArgument, required=True,
                        help="Target maximum cache size, e.g. 10GB, 500MiB, 2g. The cache is "
                             "pruned until it fits within this size. A unit is expected; a bare "
                             "number is bytes, and a tiny bare number is rejected as a likely typo.")
    parser.add_argument("--policy", action=OnceArgument, default="lru", choices=POLICIES,
                        help="Eviction order when over the limit (default: lru). "
                             "lru=least-recently-used first, oldest=creation order (fifo), "
                             "largest=biggest first.")
    parser.add_argument("--older-than", action=OnceArgument, default=None,
                        help="Only evict packages not used for at least this long, e.g. 30d, 4w, "
                             "2h (units: y, M, w, d, h, m, s). Recently-used packages are kept "
                             "even if the cache is over the limit, to avoid re-downloading them.")
    parser.add_argument("--dry-run", action="store_true", default=False,
                        help="Only report what would be removed, without deleting anything.")
    parser.add_argument("-c", "--confirm", action="store_true", default=False,
                        help="Remove without asking for confirmation.")
    args = parser.parse_args(*args)

    max_size = _parse_size(args.max_size)
    # A package is protected (never evicted) if it was last used more recently than this cutoff.
    cutoff = time.time() - _parse_age(args.older_than) if args.older_than else None

    packages, recipes_size = _collect(conan_api)
    cache_size = recipes_size + sum(p["size"] for p in packages)

    # Plan: decide which package binaries to evict, honoring the policy and the age safe-harbor.
    to_remove = []
    protected = 0
    current = cache_size
    for item in _sorted_for_eviction(packages, args.policy):
        if current <= max_size:
            break
        if cutoff is not None and item["lru"] > cutoff:
            protected += 1  # used too recently, keep it
            continue
        to_remove.append(item)
        current -= item["size"]

    result = {
        "cache_size": cache_size,
        "max_size": max_size,
        "size_after": current,
        "policy": args.policy,
        "older_than": args.older_than,
        "dry_run": args.dry_run,
        "cancelled": False,
        "recipes_size": recipes_size,
        "protected": protected,
        "over_limit": current > max_size,
        "removed": to_remove,  # for dry-run this is the plan; overwritten below when executing
    }

    if args.dry_run or not to_remove:
        return result

    # Confirm before deleting (matches 'conan remove'; --confirm / core:non_interactive skip it).
    total = sum(i["size"] for i in to_remove)
    message = (f"Remove {len(to_remove)} package binaries ({human_size(total)}) to bring the "
               f"cache under {human_size(max_size)}?")
    ui = UserInput(conan_api.config.get("core:non_interactive"))
    if not (args.confirm or ui.request_boolean(message)):
        result["cancelled"] = True
        result["size_after"] = cache_size
        result["over_limit"] = cache_size > max_size
        result["removed"] = []
        return result

    # Execute: a single failed removal (e.g. a folder locked on Windows) is skipped, not fatal,
    # and size_after stays honest by only crediting space actually freed.
    removed = []
    freed = 0
    for item in to_remove:
        try:
            conan_api.remove.package(item["pref"])
        except ConanException as e:
            ConanOutput().warning(f"Could not remove {item['pref']}: {e}")
            continue
        removed.append(item)
        freed += item["size"]

    result["removed"] = removed
    result["size_after"] = cache_size - freed
    result["over_limit"] = (cache_size - freed) > max_size
    return result
