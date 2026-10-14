from pathlib import Path

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import build_jobs, cross_building
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import collect_libs
from conan.tools.gnu import PkgConfigDeps
from conan.tools.meson import MesonToolchain


class RpExternalsBase(ConanFile):
    name = "rp_externals_base"
    version = "0.1.0"
    package_type = "python-require"
    exports = "CMakeLists.txt"

    settings = "os", "arch", "compiler", "build_type"
    options = {"shared": [True, False]}
    default_options = {"shared": True}

    rp_depends = ()
    rp_includedirs = ("include",)

    def requirements(self):
        for ref in self.rp_depends:
            self.requires(ref)

    # 单片机只能使用静态库，不能使用动态库
    def validate(self):
        if self.settings.os == "baremetal" and self.options.shared:
            raise ConanInvalidConfiguration("Bare-metal packages require shared=False")

    def layout(self):
        cmake_layout(self)

    def generate(self):
        CMakeDeps(self).generate()
        PkgConfigDeps(self).generate()

        meson = MesonToolchain(self)
        meson.binaries["pkg-config"] = "pkg-config"
        meson.generate()
        meson_file = (
            "conan_meson_cross.ini" if cross_building(self) else "conan_meson_native.ini"
        )

        generators = Path(self.generators_folder)
        toolchain = CMakeToolchain(self)
        toolchain.user_presets_path = False
        toolchain.blocks.remove("output_dirs")
        # 获取外部库的recipe
        toolchain.variables["RP_EXTERNALS_RECIPE"] = (
            Path(self.source_folder) / "recipe.cmake"
        ).as_posix()

        toolchain.variables["RP_EXTERNALS_STAGE_DIR"] = (
            Path(self.build_folder) / "staging"
        ).as_posix()

        toolchain.variables["RP_EXTERNALS_SHARED"] = bool(self.options.shared)
        toolchain.variables["RP_CMAKE_TOOLCHAIN_FILE"] = (
            generators / toolchain.filename
        ).as_posix()

        toolchain.variables["RP_MESON_FILE"] = (generators / meson_file).as_posix()
        toolchain.variables["RP_MESON_IS_CROSS"] = cross_building(self)
        toolchain.variables["RP_PKG_CONFIG_DIR"] = generators.as_posix()

        if self.settings.os == "baremetal":
            toolchain.variables["CMAKE_TRY_COMPILE_TARGET_TYPE"] = "STATIC_LIBRARY"
        toolchain.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure(
            build_script_folder=self.python_requires["rp_externals_base"].path
        )
        cmake.build()

    def package(self):
        CMake(self).install()

    def package_info(self):
        self.cpp_info.includedirs = list(self.rp_includedirs)
        self.cpp_info.libs = collect_libs(self)
