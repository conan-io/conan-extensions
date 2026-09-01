import os, json
from conan import ConanFile
from conan.tools.files import copy

class WafConanTestProjectFlatbuffers(ConanFile):
    name = "waf_conan_test_flatbuffers"
    version = "1.0"
    settings = "os", "compiler", "build_type", "arch"

    requires = "flatbuffers/23.5.26"

    #ensure 'flatc' is available in build environment
    tool_requires = "flatbuffers/23.5.26"

    generators = ['Waf']
    # python_requires = "wafgenerator/0.1"
    # def generate(self):
    #     gen = self.python_requires["wafgenerator"].module.Waf(self)
    #     gen.generate()