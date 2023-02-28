import os
import textwrap
from jinja2 import Template
from conan.cli.command import conan_command
from conan.api.output import cli_out_write
from conans.client.loader_txt import ConanFileTextLoader


@conan_command(group="Extension", formatters={"text": cli_out_write})
def convert_txt(conan_api, parser, *args, **kwargs):
    """
    Convert a conanfile.txt to a conanfile.py
    """
    parser.add_argument("path", help="Path to a folder containing a conanfile.txt")
    args = parser.parse_args(*args)

    path = os.path.join(args.path, "conanfile.txt")  if os.path.isdir(args.path) else args.path
    txt = ConanFileTextLoader(open(path, "r").read())
    template = textwrap.dedent("""\
        from conan import ConanFile
        {% if layout == "cmake_layout" %}
        from conan.tools.cmake import cmake_layout
        {% endif %}
        {% if layout == "vs_layout" %}
        from conan.tools.microsoft import vs_layout
        {% endif %}

        class Pkg(ConanFile):
            {% if generators %}
            generators ={% for g in generators %} "{{g}}",{% endfor %}
            {% endif %}

            {% if options %}
            default_options = {{options}}
            {% endif %}

            def requirements(self):
                {% for r in requires %}
                self.requires("{{r}}")
                {% endfor %}
                {% if not requires %}
                pass
                {% endif %}

            def build_requirements(self):
                {% for r in test_requires %}
                self.test_requires("{{r}}")
                {% endfor %}
                {% for r in tool_requires %}
                self.tool_requires("{{r}}")
                {% endfor %}
                {% if not tool_requires and not test_requires%}
                pass
                {% endif %}

            {% if layout %}
            def layout(self):
                {{layout}}(self)
            {% endif %}
            """)
    conanfile = Template(template, trim_blocks=True, lstrip_blocks=True)
    options = {}
    for o in txt.options.splitlines():
        k, v = o.split("=")
        options[k] = v
    conanfile = conanfile.render({"requires": txt.requirements,
                                  "tool_requires": txt.tool_requirements,
                                  "test_requires": txt.test_requirements,
                                  "generators": txt.generators,
                                  "options": options,
                                  "layout": txt.layout})
    return conanfile
