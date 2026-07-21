## Cache commands

Commands to help manage the local Conan cache.

#### [Clean by size](cmd_clean_size.py)

Prunes the local Conan cache down to a maximum size by evicting package binaries.

This is the "clean by size" counterpart to the built-in [`conan cache clean`](https://docs.conan.io/2/reference/commands/cache.html)
(which only removes source/build/download temp folders): here, whole package binaries are removed
until the cache fits within `--max-size`. Removal is always explicit through this command — nothing
is ever evicted automatically as a side effect of `conan install` or other commands.

It is a prototype of the idea discussed in [conan#20157](https://github.com/conan-io/conan/issues/20157).

**Parameters**
- `--max-size` _Required_: Target maximum cache size, e.g. `10GB`, `500MiB`, `2g`, or a plain byte
  count. Decimal suffixes (`kb`, `mb`, `gb`, `tb`) use 1000; binary suffixes (`kib`/`k`, `mib`/`m`,
  `gib`/`g`, `tib`/`t`) use 1024. The cache is pruned until it fits within this size. A bare number
  is bytes, but a suspiciously small bare number (below 1 MiB) is rejected as a likely forgotten
  unit — e.g. `--max-size 10` errors and suggests `10MB`/`10GB` (or `10B` if you truly mean bytes).
  To wipe the cache entirely, use `conan remove "*:*"` instead.
- `--policy` _Optional_: Eviction order when the cache is over the limit. One of:
  - `lru` (default): least-recently-used first. Keeps the packages you actually use and evicts the
    ones gathering dust — the recommended policy.
  - `oldest`: oldest revision first (creation order / FIFO).
  - `largest`: biggest first. Reclaims space fastest, but may evict a large package you use often,
    forcing a slow re-download.
- `--older-than` _Optional_: Only evict packages not used for at least this long, e.g. `30d`, `4w`,
  `2h` (units: `y`, `M`, `w`, `d`, `h`, `m`, `s`, same as `conan remove --lru`). Recently-used
  packages are kept even if the cache is over the limit, which avoids thrashing (re-downloading a
  package right after evicting it). Combine it with `--max-size` for a "size **and** age" policy.
- `--dry-run` _Optional_: Only report what would be removed, without deleting anything.
- `-c, --confirm` _Optional_: Remove without asking for confirmation. Without it (and outside
  `core:non_interactive` mode) the command prints what it will remove and asks first, like
  `conan remove`.
- `-f, --format` _Optional_: `json` for machine-readable output.

**Notes**
- The eviction unit is a package binary (a package revision). Recipe and cached-source folders are
  counted towards the reported cache size but are not removed. If package binaries alone cannot bring
  the cache under the limit, the command warns and suggests `conan cache clean`.
- The least-recently-used signal is the package folder's modification time — exactly what Conan
  itself uses for `conan remove --lru` / `conan list --lru` (`PkgCache.get_package_lru`). Using a
  package (e.g. installing it as a dependency) refreshes it, so actively-used packages survive.

Usage:

```shellSession
$ conan cache:clean-size --max-size 10GB
Remove 3 package binaries (3.8GiB) to bring the cache under 9.3GiB? (yes/no): yes
Cache size:  12.4GiB (13314398208 B)
Size limit:  9.3GiB (10000000000 B)  [policy: lru]
Removed 3 package binaries:
  boost/1.83.0:da39a3ee5e6b4b0d3255bfef95601890afd80709  (1.8GiB)
  qt/6.6.1:a1b2c3...  (1.1GiB)
  llvm/17.0.6:d4e5f6...  (0.9GiB)
Freed:       3.8GiB
New size:    8.6GiB
```

```shellSession
# Preview only; combine a size cap with an age safe-harbor (keep anything used in the last 2 weeks)
$ conan cache:clean-size --max-size 500MB --older-than 2w --dry-run
```
