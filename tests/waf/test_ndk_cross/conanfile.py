import os, json
from conan import ConanFile
from conan.tools.files import copy

class WafConanTestProjectNDK(ConanFile):
    settings = "os", "compiler", "build_type", "arch"
    requires = ["flatbuffers/23.5.26"]
    build_requires = ["flatbuffers/23.5.26"]

    generators = ['Waf']
    # python_requires = "wafgenerator/0.1"
    # def generate(self):
    #     gen = self.python_requires["wafgenerator"].module.Waf(self)
    #     gen.generate()