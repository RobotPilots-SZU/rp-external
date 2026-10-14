import os
import re
import subprocess
from pathlib import Path
from typing import Any, cast

from conan import ConanFile
from conan.errors import ConanException
from conan.tools.build import cross_building
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import copy
from conan.tools.meson import MesonToolchain
from conan.tools.scm import Git

def extract_version_from_folder(floder_path: str) -> tuple[str, str]:


class RpExternalsConan(ConanFile):
    name = "rp-external"
    package_type = "shared-library"

    settings = "os", "arch", "compiler", "build_type", "rp"
    exports_sources = (
        "CMakeLists.txt",
        "VERSION",
        "packages/*",
        "profiles/*",
    )

    def set_version(self):
        git = Git(self)
        assert self.recipe_folder is not None
        version_file = Path(self.recipe_folder) / "VERSION"
        base = version_file.read_text(encoding="utf-8").strip() if version_file.exists() else "0.1.0"
        count = git.run("rev-list --count HEAD")
        hash = git.run("rev-parse --short HEAD")
        tags = git.run("tag --points-at HEAD")
        is_rel = any(re.match(r"^(release|main)/", tag) for tag in tags.splitlines())
        is_dirty = git.is_dirty()
        dev = f"-dev.{count}" if is_dirty or not is_rel else ""
        dirty = ".dirty" if is_dirty else ""
        # SemVer规范: https://semver.org/lang/zh-CN/
        # 上述代码生成的版本号示例：
        # 开发版本 0.1.0-dev.1+a1b2c3d4.dirty
        # 发布版本 0.1.0+a1b2c3d4
        self.version = f"{base}{dev}+{hash}{dirty}"

    def compatibility(self):
        platform = self.settings.get_safe("robotpilots.platform")
        if platform not in (None, "stm32"):
            return [{
                "settings": [
                    ("robotpilots.platform", "stm32"),
                ]
            }]
        return []

    # def requirements(self):
    #     self.requires("mamo-cmake/[>=0.1 <1.0, include_prerelease]")

    def layout(self):
        cmake_layout(self)

    def generate(self):
        meson_tc = MesonToolchain(self)
        meson_tc.binaries["pkg-config"] = "pkg-config"
        meson_tc.generate()

        meson_ini_name = (
            "conan_meson_cross.ini" if cross_building(self) else "conan_meson_native.ini"
        )
        meson_ini = os.path.join(self.generators_folder, meson_ini_name)

        tc = CMakeToolchain(self)
        tc.blocks["find_paths"].values["find_package_prefer_config"] = "OFF"
        tc.variables["RP_MESON_FILE"] = meson_ini
        tc.variables["RP_MESON_IS_CROSS"] = "ON" if cross_building(self) else "OFF"
        tc.generate()

        deps = CMakeDeps(self)
        deps.generate()

    def build(self):
        variables = {
            "RP_PLATFORM": self._rp_platform
        }

        cmake = CMake(self)
        cmake.configure(variables=variables)

        log_dir = os.environ.get("CONAN_BUILD_LOG_DIR", self.build_folder)
        os.makedirs(f"{log_dir}", exist_ok=True)
        log_file = os.path.join(f"{log_dir}", "conan_build.log")
        with open(log_file, "w") as log:
            self.run(
                "cmake --build . --parallel 2",
                cwd=self.build_folder,
                stdout=log,
                stderr=log,
                quiet=True,
            )

    def package(self):
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.includedirs = ["include"]
        self.cpp_info.libdirs = ["lib"]
        self.cpp_info.bindirs = ["bin"]
        self.cpp_info.builddirs = ["."]
        self.cpp_info.set_property("cmake_find_mode", "none")

    @property
    def _stage_dir(self):
        return os.path.join(str(self.build_folder), "staging")

    @property
    def _rp_platform(self):
        value = self.settings.get_safe("robotpilots.platform")
        if value is not None:
            value = os.environ.get("RP_PLATFORM", "stm32")
        return str(value)

