from conan import ConanFile
from conan.tools.apple import fix_apple_shared_install_name
from conan.tools.build import cross_building
from conan.tools.env import VirtualRunEnv
from conan.tools.files import apply_conandata_patches, copy, get, rm, rmdir
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.gnu import Autotools, AutotoolsDeps, AutotoolsToolchain
from conan.tools.layout import basic_layout
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
        if self.settings.os == "Windows":
            cmake_layout(self)
        else:
            basic_layout(self, src_folder="src")

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
        # apply patches listed in conandata.yml
        # Using patches is always the last resort to fix issues. If possible, try to fix the issue in the upstream project.
        apply_conandata_patches(self)

    def generate(self):
        if self.settings.os == "Windows":
            CMakeToolchain(self).generate()
            CMakeDeps(self).generate()
            return
        # inject required env vars into the build scope
        # it's required in case of native build when there is AutotoolsDeps & at least one dependency which might be shared, because configure tries to run a test executable
        if not cross_building(self):
            VirtualRunEnv(self).generate(scope="build")
        # --fpic is automatically managed when 'fPIC' option is declared
        # --enable/disable-shared is automatically managed when 'shared' option is declared
        tc = AutotoolsToolchain(self)
        # autotools usually uses 'yes' and 'no' to enable/disable options
        def yes_no(v): return "yes" if v else "no"
        tc.configure_args.extend([
            f"--enable-jpeg={yes_no(self.options.with_jpeg)}",
        ])
        tc.generate()
        # generate dependencies for autotools
        # some recipes might require a workaround for MSVC (https://github.com/conan-io/conan/issues/12784):
        # https://github.com/conan-io/conan-center-index/blob/00ce907b910d0d772f1c73bb699971c141c423c1/recipes/xapian-core/all/conanfile.py#L106-L135
        deps = AutotoolsDeps(self)
        deps.generate()

    def build(self):
        if self.settings.os == "Windows":
            for dir in (".", "src", "utils"):
                copy(self, "CMakeLists.txt", os.path.join(self.export_sources_folder, dir),
                     os.path.join(self.source_folder, dir))
            cmake = CMake(self)
            cmake.configure()
            cmake.build()
        else:
            autotools = Autotools(self)
            autotools.configure()
            autotools.make()

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        if self.settings.os == "Windows":
            cmake = CMake(self)
            cmake.install()
            return

        autotools = Autotools(self)
        autotools.install()

        # Some files extensions and folders are not allowed. Please, read the FAQs to get informed.
        rm(self, "*.la", os.path.join(self.package_folder, "lib"))
        # Consider disabling these at first to verify that the package_info() output matches the info exported by the project.
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rmdir(self, os.path.join(self.package_folder, "share"))

        # In shared lib/executable files, autotools set install_name (macOS) to lib dir absolute path instead of @rpath, it's not relocatable, so fix it
        fix_apple_shared_install_name(self)

    def package_info(self):
        self.cpp_info.libs = ["FOX-1.6"]              # libFOX-1.6.so / FOX-1.6.lib
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
