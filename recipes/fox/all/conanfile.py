from conan import ConanFile
from conan.tools.files import copy, get
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
import os


required_conan_version = ">=2.0.9"

#
# INFO: Please, remove all comments before pushing your PR!
#


class PackageConan(ConanFile):
    name = "fox"
    description = "FOX is a C++ based Toolkit for developing Graphical User Interfaces."
    # Use short name only, conform to SPDX License List: https://spdx.org/licenses/
    # In case not listed there, use "DocumentRef-<license-file-name>:LicenseRef-<package-name>"
    license = "LGPL-2.1-or-later"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "http://fox-toolkit.org"
    # no "conan" and project name in topics. Use topics from the upstream listed on GH
    topics = ("GUI",)
    # package_type should usually be "library", "shared-library" or "static-library"
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_jpeg": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_jpeg": True,
    }
    # In case having config_options() or configure() method, the logic should be moved to the specific methods.
    implements = ["auto_shared_fpic"]

    # no exports_sources attribute, but export_sources(self) method instead
    def export_sources(self):
        for dir in (".", "src", "utils"):
            copy(self, "CMakeLists.txt", os.path.join(self.recipe_folder, "cmake", dir),
                    os.path.join(self.export_sources_folder, dir))

    def layout(self):
        cmake_layout(self)

    def requirements(self):
        # Prefer self.requirements() method instead of self.requires attribute.
        # self.requires("dependency/0.8.1")
        if self.options.with_jpeg:
            self.requires("libjpeg/9f")
        # Some dependencies on CCI are allowed to use version ranges.
        # See https://github.com/conan-io/conan-center-index/blob/master/docs/adding_packages/dependencies.md#version-ranges
        # self.requires("openssl/[>=1.1 <4]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        CMakeToolchain(self).generate()
        CMakeDeps(self).generate()

    def build(self):
        for dir in (".", "src", "utils"):
            copy(self, "CMakeLists.txt", os.path.join(self.export_sources_folder, dir),
                 os.path.join(self.source_folder, dir))
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.libs = ["fox-1.6"]                 # libfox-1.6.so / fox-1.6.lib
        self.cpp_info.includedirs = ["include/fox-1.6"]  # FOX installs headers here, not include/

        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs = [
                "X11", "Xext", "Xft", "Xcursor", "Xrandr", "Xrender",
                "Xfixes", "Xi", "fontconfig", "freetype", "dl", "pthread", "rt",
            ]
            if self.options.get_safe("opengl"):
                self.cpp_info.system_libs += ["GL", "GLU"]
        elif self.settings.os == "Windows":
            self.cpp_info.system_libs = [
                "gdi32", "user32", "comctl32", "ws2_32", "winspool",
                "mpr", "imm32", "shell32", "ole32", "uuid",
            ]
            if self.options.get_safe("opengl"):
                self.cpp_info.system_libs += ["opengl32", "glu32"]
        elif self.settings.os == "Macos":
            self.cpp_info.frameworks = ["CoreFoundation", "Cocoa", "OpenGL"]
