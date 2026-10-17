#!/usr/bin/env python3
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGES_DIR = REPO_ROOT / "packages"

CONANFILE_TEMPLATE = '''\
from conan import ConanFile


class {class_name}Conan(ConanFile):
    name = "{package_name}"
    version = "{version}"
    package_type = "library"
    use_git_version = False
    python_requires = "rp_externals_base/[>=0.1.0 <0.2.0, include_prerelease]"
    python_requires_extend = "rp_externals_base.RpExternalsBase"

    settings = "os", "arch", "compiler", "build_type"
    exports_sources = "*", "!conanfile.py", "!build/*", "!__pycache__/*"

    rp_depends = {depends_tuple}
    rp_includedirs = {includedirs_tuple}
'''

# 获取库名和版本号
def extract_version_from_folder(folder_name: str) -> tuple[str, str]:
    match = re.fullmatch(r"(.+?)-(\d+\.\d+(?:\.\d+)*)", folder_name)
    if not match:
        raise ValueError(f"文件夹名不是 name-version 格式: {folder_name}")
    return match.group(1), match.group(2)


def scan_packages(packages_dir: Path = PACKAGES_DIR) -> dict[str, Path]:
    if not packages_dir.is_dir():
        raise FileNotFoundError(f"packages 目录不存在: {packages_dir}")

    packages = {}
    for folder in sorted(packages_dir.iterdir()):
        if not folder.is_dir():
            continue
        try:
            name, version = extract_version_from_folder(folder.name)
        except ValueError as exc:
            print(f"⚠ 跳过: {exc}")
            continue

        reference = f"{name}/{version}"
        packages[reference] = folder

    return packages


def parse_package_list(text: str, suffix: str, default: tuple[str, ...] = ()) -> tuple[str, ...]:
    match = re.search(
        r'set\s*\(\s*\$\{\s*package_name\s*\}_' + suffix
        + r'\s+((?:"[^"\n]*"|[^)])*)\)', text, re.IGNORECASE,
    )
    if match is None:
        return default
    values = re.findall(r'"([^"\n]*)"', match.group(1))
    if re.sub(r'"[^"\n]*"', "", match.group(1)).strip():
        raise ValueError(f"{suffix} 必须使用带双引号的字面量")
    return tuple(item for value in values for item in value.split(";") if item)


def parse_recipe_cmake(recipe_file: Path) -> tuple[str | None, list[str], tuple[str, ...]]:
    text = recipe_file.read_text(encoding="utf-8")
    # 只解析约定的元数据；去掉注释时保留引号内的内容。
    text = re.sub(
        r'"[^"\n]*"|#\[(=*)\[.*?\]\1\]|#[^\n]*',
        lambda match: "\n" if match.group().startswith("#") else match.group(),
        text, flags=re.DOTALL,
    )
    match = re.search(r'set\s*\(\s*package_name\s+"([^"\n]+)"\s*\)', text, re.IGNORECASE)
    name = match.group(1) if match else None
    depends = list(parse_package_list(text, "DEPEND_PACKAGES"))
    includedirs = parse_package_list(text, "INCLUDEDIRS", ("include",))
    return name, depends, includedirs


def format_depends_tuple(depends: list[str], packages: dict[str, Path], owner: str) -> str:
    missing = [reference for reference in depends if reference not in packages]
    if missing:
        raise ValueError(f"{owner}: 依赖 {', '.join(missing)} 在 packages/ 中不存在")
    return repr(tuple(depends))


def generate(packages: dict[str, Path]) -> int:
    failed = []
    for reference, folder in packages.items():
        try:
            name, version = reference.split("/", 1)
            recipe_name, depends, includedirs = parse_recipe_cmake(
                folder / "recipe.cmake"
            )
            if recipe_name and recipe_name != name:
                print(
                    f"⚠ {folder.name}: recipe.cmake 中包名为 {recipe_name}，"
                    "以文件夹名为准"
                )

            content = CONANFILE_TEMPLATE.format(
                class_name="".join(
                    word.capitalize() for word in re.split(r"[-_]", name)
                ),
                package_name=name,
                version=version,
                depends_tuple=format_depends_tuple(depends, packages, reference),
                includedirs_tuple=repr(includedirs),
            )
            (folder / "conanfile.py").write_text(content, encoding="utf-8")
        except (ValueError, OSError) as exc:
            print(f"❌ {reference}: {exc}")
            failed.append(reference)
            continue

        suffix = f" 依赖: {', '.join(depends)}" if depends else ""
        print(f"✓ {reference}{suffix}")

    if failed:
        print(f"\n❌ 失败: {', '.join(failed)}")
        return 1

    print(f"\n✅ 生成 {len(packages)} 个 conanfile.py")
    return 0


def main() -> int:
    try:
        packages = scan_packages()
        if not packages:
            raise ValueError("packages/ 下没有有效的库目录")
        return generate(packages)
    except (ValueError, OSError) as exc:
        print(f"❌ {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
