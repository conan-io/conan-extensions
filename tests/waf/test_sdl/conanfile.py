import os, json
from conan import ConanFile
from conan.tools.files import copy

class WafConanTestProject(ConanFile):
    name = "waf_conan_test_sdl"
    version = "1.0"
    settings = "os", "compiler", "build_type", "arch"
    requires = "sdl/2.28.3"

    def configure(self):
        self.options['sdl'].shared = True

    generators = ['Waf']
    # python_requires = "wafgenerator/0.1"
    # def generate(self):
    #     gen = self.python_requires["wafgenerator"].module.Waf(self)
    #     gen.generate()