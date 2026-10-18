import re
from pathlib import Path
from conan.tools.scm import Git

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import build_jobs, cross_building
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import collect_libs
from conan.tools.gnu import PkgConfigDeps
from conan.tools.meson import MesonToolchain


class RpExternalsBase(ConanFile):
    name = "rp_externals_base"
    package_type = "python-require"
    exports = "CMakeLists.txt"
    use_git_version = True

    settings = "os", "arch", "compiler", "build_type"
    options = {"shared": [True, False]}

    rp_depends = ()
    rp_includedirs = ("include",)

    def requirements(self):
        for ref in self.rp_depends:
            self.requires(ref)

    def set_version(self):
        # 第三方库的版本按releasetag，externals的基类版本按SemVer规范生成，便于区分
        if not self.use_git_version:
            return

        git = Git(self)
        assert self.recipe_folder is not None
        version_file = Path(self.recipe_folder).parent / "VERSION"
        base = version_file.read_text(encoding="utf-8").strip() if version_file.exists() else "0.1.0"
        count = git.run("rev-list --count HEAD")
        git_hash = git.run("rev-parse --short HEAD")
        tags = git.run("tag --points-at HEAD")
        is_rel = any(re.match(r"^(release|main)/", tag) for tag in tags.splitlines())
        is_dirty = git.is_dirty()
        dev = f"-dev.{count}" if is_dirty or not is_rel else ""
        dirty = ".dirty" if is_dirty else ""
        # SemVer规范: https://semver.org/lang/zh-CN/
        # 上述代码生成的版本号示例：
        # 开发版本 0.1.0-dev.1+a1b2c3d4.dirty
        # 发布版本 0.1.0+a1b2c3d4
        self.version = f"{base}{dev}+{git_hash}{dirty}"

    # 单片机只能使用静态库，不能使用动态库
    def configure(self):
        if self.settings.os == "baremetal":
            self.options.shared = False
        else:
            self.options.shared = True

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

        toolchain.variables["MCU_PLATFORM"] = bool(self.settings.os == "baremetal")
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
