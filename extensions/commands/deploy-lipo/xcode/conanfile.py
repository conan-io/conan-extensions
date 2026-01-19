from conan import ConanFile
from conan.tools.apple import XcodeBuild


class UniversalRecipe(ConanFile):
    # Note that we don't depend on arch
    settings = "os", "compiler", "build_type"
    requires = ("libtiff/4.5.0",)

    def build(self):
        # xcodebuild = XcodeBuild(self)
        # Don't use XcodeBuild because it passes a single -arch flag
        build_type = self.settings.get_safe("build_type")
        project = 'example.xcodeproj'
        self.run('xcodebuild -configuration {} -project {} -alltargets'.format(build_type, project))
