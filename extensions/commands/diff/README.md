## Diff command

> ⚠️ Warning: These custom commands are experimental. They are under development and are subject to breaking changes.

This command generate the difference between upstream versions and generate a `HTML` file to analyze them.

```
conan diff:check-diff ./path/to/conanfile 1.0 2.0
```

If the output difference is substantial, you can use the --split_diff option to generate a simple main page with a table
of contents, along with multiple `HTML` files containing the diffs, making it easier to view the output.

```
conan diff:check-diff ./path/to/conanfile 1.0 2.0 --split_diff
```
