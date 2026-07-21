## Cache commands

Commands to help manage the local Conan cache.

#### [Clean by size](cmd_clean_size.py)

Prunes the local Conan cache down to a maximum size by removing package binaries.

This is a different operation from the built-in [`conan cache clean`](https://docs.conan.io/2/reference/commands/cache.html),
which frees the source/build/download temp folders of cached packages: here, whole package
binaries are removed until the cache fits within `--max-size`. Removal only happens when you
explicitly run this command.

It is a prototype of the idea discussed in [conan#20157](https://github.com/conan-io/conan/issues/20157).

**Parameters**
- `--max-size` _Required_: Maximum cache size in **GB**, e.g. `10` (10 GB) or `0.5`. The cache is
  pruned until it fits within this size.
- `--policy` _Optional_: Eviction order when the cache is over the limit. One of:
  - `lru` (default): least-recently-used first. Keeps the packages you actually use and evicts the
    ones gathering dust — the recommended policy.
  - `oldest`: oldest package revision first. Note this sorts by the revision timestamp, which may
    be a server-side timestamp rather than the local install/use time.
  - `largest`: biggest first. Reclaims space fastest, but may evict a large package you use often,
    forcing a slow re-download.
- `--older-than` _Optional_: Only evict packages not used for at least this long, e.g. `30d`, `4w`,
  `2h` (units: `y`, `M`, `w`, `d`, `h`, `m`, `s`, same as `conan remove --lru`). Recently-used
  packages are kept even if the cache is over the limit, which avoids thrashing (re-downloading a
  package right after evicting it). Combine it with `--max-size` for a "size **and** age" policy.
- `-f, --format` _Optional_: `json` for machine-readable output.

**Notes**
- The eviction unit is a package binary (a package revision). Recipe and cached-source folders are
  counted towards the reported cache size but are never removed. If package binaries alone cannot
  bring the cache under the limit, the command warns and suggests `conan cache clean`.
- The least-recently-used signal is the package folder's modification time — exactly what Conan
  itself uses for `conan remove --lru` / `conan list --lru` (`PkgCache.get_package_lru`). Using a
  package (e.g. installing it as a dependency) refreshes it, so actively-used packages survive.

Usage:

```shellSession
$ conan cache:clean-size --max-size 10
Cache size:  12.4GB (12400000000 B)
Size limit:  10.0GB (10000000000 B)  [policy: lru]
Removed 3 package binaries:
  boost/1.83.0:da39a3ee5e6b4b0d3255bfef95601890afd80709  (1.8GB)
  qt/6.6.1:a1b2c3...  (1.1GB)
  llvm/17.0.6:d4e5f6...  (0.9GB)
Freed:       3.8GB
New size:    8.6GB
```

```shellSession
# Prune to 5 GB, but keep anything used in the last 2 weeks
$ conan cache:clean-size --max-size 5 --older-than 2w
```
