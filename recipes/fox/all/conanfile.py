from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.apple import fix_apple_shared_install_name
from conan.tools.build import check_min_cppstd, cross_building
from conan.tools.env import Environment, VirtualRunEnv
from conan.tools.files import apply_conandata_patches, copy, export_conandata_patches, get, rm, rmdir
from conan.tools.gnu import Autotools, AutotoolsDeps, AutotoolsToolchain, PkgConfigDeps
from conan.tools.layout import basic_layout
from conan.tools.microsoft import is_msvc, unix_path
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
    topics = ("GUI")
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
        export_conandata_patches(self)

    def layout(self):
        basic_layout(self, src_folder="src")

    def requirements(self):
        # Prefer self.requirements() method instead of self.requires attribute.
        # self.requires("dependency/0.8.1")
        if self.options.with_jpeg:
            self.requires("libjpeg/9f")
        # Some dependencies on CCI are allowed to use version ranges.
        # See https://github.com/conan-io/conan-center-index/blob/master/docs/adding_packages/dependencies.md#version-ranges
        # self.requires("openssl/[>=1.1 <4]")

    def validate(self):
        # Always comment the reason including the upstream issue.
        # INFO: Upstream only support Unix systems. See <URL>
        if self.settings.os not in ["Linux", "FreeBSD", "Macos"]:
            raise ConanInvalidConfiguration(f"{self.ref} is not supported on {self.settings.os}.")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        # apply patches listed in conandata.yml
        # Using patches is always the last resort to fix issues. If possible, try to fix the issue in the upstream project.
        apply_conandata_patches(self)

    def generate(self):
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
        autotools = Autotools(self)
        autotools.configure()
        autotools.make()

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
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
        self.cpp_info.libs = ["package_lib"]

        # if the package provides a pkgconfig file (package.pc, usually installed in <prefix>/lib/pkgconfig/)
        self.cpp_info.set_property("pkg_config_name", "package")

        # If they are needed on Linux, m, pthread and dl are usually needed on FreeBSD too
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs.extend(["dl", "m", "pthread"])
