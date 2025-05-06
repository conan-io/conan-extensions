import json
import subprocess
import os
import tempfile

from conan.api.conan_api import ConanAPI
from conan.api.output import ConanOutput
from conan.cli.command import conan_command
from conan.internal.util.files import chdir

def output_json(msg):
    return json.dumps({"greet": msg})


@conan_command(group="utils", formatters={"json": output_json})
def check_diff(conan_api: ConanAPI, parser, *args):
    """
    Command to get the diff between versions
    """
    parser.add_argument("path", help="Path to the conanfile")
    parser.add_argument("-o", "--old", help="Old version")
    parser.add_argument("-n", "--new", help="New version")
    parser.add_argument("-s", "--split_diff", action="store_true")
    parser.add_argument("--encoding", default="utf-8", help="Encoding to read diff")
    args = parser.parse_args(*args)

    cwd = os.getcwd()
    path = conan_api.local.get_conanfile_path(args.path, cwd, py=True)
    enabled_remotes = conan_api.remotes.list()
    if not os.path.exists(f"diff{args.old}-{args.new}.patch"):
        t = tempfile.mkdtemp(suffix='conans')

        old_folder = os.path.join(t, "old")
        new_folder = os.path.join(t, "new")
        os.mkdir(old_folder)
        os.mkdir(new_folder)

        ConanOutput().info("old_folder: " + old_folder)
        ConanOutput().info("new_folder: " + new_folder)

        with chdir(old_folder):
            conan_api.local.source(path, version=args.old, remotes=enabled_remotes)

        with chdir(new_folder):
            conan_api.local.source(path, version=args.new, remotes=enabled_remotes)

        with open(f"diff{args.old}-{args.new}.patch", "w") as f:
            subprocess.run(["git", "diff", old_folder, new_folder], stdout=f, check=True)

        ConanOutput().info(f"diff in diff{args.old}-{args.new}.patch")

    with open(f"diff{args.old}-{args.new}.patch", "r", encoding=args.encoding) as file:
        diff_text = file.read()
        ConanOutput().info(f"diff ready")
    name = f"{args.old}-{args.new}"

    if args.split_diff:
        diff_to_multi_html(name, diff_text)
    else:
        diff_to_single_html(name, diff_text)
    subprocess.run(["open", os.path.join(cwd, f"diff_{args.old}-{args.new}.html")])

def diff_to_multi_html(name, diff_text):
    file_diffs = {}
    current_file = None
    current_lines = []

    for line in diff_text.splitlines():
        if line.startswith("diff --git"):
            if current_file and current_lines:
                file_diffs[current_file] = list(current_lines)
            parts = line.split()
            current_file = parts[2][2:]
            current_lines = [line]
        elif current_file:
            current_lines.append(line)

    if current_file and current_lines:
        file_diffs[current_file] = current_lines

    # Generate small html files
    output_dir = "html_diffs"
    subprocess.run(["mkdir", output_dir])
    for file_name, lines in file_diffs.items():
        output_path = os.path.join(output_dir, f"{file_name.replace('/', '_')}.html")
        html_lines = [
            f"<html><head><title>{name}</title><style>",
            ".container { display: flex; height: 100%; }",
            ".content { flex-grow: 1; padding: 20px; background: #fff; overflow-y: auto; }",
            ".add { background-color: #76ffbb; }",
            ".del { background-color: #fdb9c1; }",
            ".context { background-color: #f8f8f8; }",
            ".filename { background-color: #ceffff; }",
            "body{ font-family: monospace; white-space: pre; margin: 0px}",
            "</style></head><body>"
        ]
        for line in lines:
            if line.startswith('+++') or line.startswith('---') or line.startswith('index'):
                pass
            elif line.startswith('+'):
                html_lines.append(f'<span class="add">{line}</span>')
            elif line.startswith('-'):
                html_lines.append(f'<span class="del">{line}</span>')
            elif line.startswith('diff --git'):
                _name = line.split(" ")[2][2:]
                html_lines.append(f'<h1 id="{_name}" class="filename">{_name}</h1>')
            else:
                html_lines.append(f'<span class="context">{line}</span>')
        html_lines.append("</div></body></html>")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write('\n'.join(html_lines))

    # Generate the main html
    with open(f"diff_{name}.html", "w", encoding="utf-8") as f:

        f.write(f"<html><head><title>{name}</title>")
        f.write("""<style>
            .container { display: flex; height: 100%; }
            .sidebar { width: 300px; padding: 10px; background: #f4f4f4; overflow-y: auto; border-right: 1px solid #ccc; }
            .content { flex-grow: 1; padding: 20px; background: #fff; overflow-y: auto; display: flex}
            .add { background-color: #76ffbb; }
            .del { background-color: #fdb9c1; }
            .context { background-color: #f8f8f8; }
            .filename { background-color: #ceffff; }
            iframe { flex-grow: 1; border: 0px}
            body { font-family: monospace; white-space: pre; margin: 0px }
            </style></head><body><pre><div class="container"><div class="sidebar">""")
        f.write(f"<h2>{name}</h2><h2>File list:</h2><ul>")
        # Table of content
        for file_name in file_diffs:
            safe_name = file_name.replace('/', '_')
            f.write(f'<li><a href="{output_dir}/{safe_name}.html" target="diff-frame">{file_name}</a></li>\n')

        f.write("""
                </ul>
            </div>
            <div class="content">
                <iframe name="diff-frame" src=""></iframe>
            </div>
            </div></pre></body></html>
        """)


def diff_to_single_html(name, diff_text):
    html_lines = [
        f"<html><head><title>{name}</title><style>",
        ".container { display: flex; height: 100%; }",
        ".sidebar { width: 300px; padding: 10px; background: #f4f4f4; overflow-y: auto; border-right: 1px solid #ccc; }",
        ".content { flex-grow: 1; padding: 20px; background: #fff; overflow-y: auto; }",
        ".add { background-color: #76ffbb; }",
        ".del { background-color: #fdb9c1; }",
        ".context { background-color: #f8f8f8; }",
        ".filename { background-color: #ceffff; }",
        "body { font-family: monospace; white-space: pre; margin: 0px}",
        "</style></head><body><pre>"
    ]

    file_names = [line.split()[2][2:] for line in diff_text.splitlines() if line.startswith("diff --git")]

    html_lines.append(f"<div class='container'><div class='sidebar'><h2>{name}</h2><h2>File list:</h2><ul>")
    for file in sorted(file_names):
        html_lines.append(f'<li><a href="#{file}">{file}</a></li>')
    html_lines.append("</ul></div><div class='content'>")

    for line in diff_text.splitlines():
        if line.startswith('+++') or line.startswith('---') or line.startswith('index'):
            pass
        elif line.startswith('+'):
            html_lines.append(f'<span class="add">{line}</span>')
        elif line.startswith('-'):
            html_lines.append(f'<span class="del">{line}</span>')
        elif line.startswith('diff --git'):
            _name = line.split(" ")[2][2:]
            html_lines.append(f'<hr/>')
            html_lines.append(f'<h1 id="{_name}" class="filename">{_name}</h1>')
        else:
            html_lines.append(f'<span class="context">{line}</span>')
    html_lines.append(f'<hr/></div></div>')

    html_lines.append("</pre></body></html>")

    with open(f"diff_{name}.html", "w", encoding="utf-8") as f:
        f.write('\n'.join(html_lines))
        ConanOutput().info(f"html generated")
