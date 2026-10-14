#!/usr/bin/env python3
"""按依赖顺序构建第三方库，支持列出库、预览顺序和清理本地 build 目录。"""

import argparse
import shlex
import shutil
import subprocess
from pathlib import Path

from generate_conanfiles import (
    REPO_ROOT,
    parse_recipe_cmake,
    scan_packages,
)


class LibraryGraph:
    def __init__(self) -> None:
        self.folders: dict[str, Path] = {}
        self.depends: dict[str, list[str]] = {}

    def add(self, reference: str, folder: Path, depends: list[str]) -> None:
        self.folders[reference] = folder
        self.depends[reference] = depends

    def resolve(self, targets: list[str] | None = None) -> list[str]:
        order = []
        visited = set()
        visiting = []

        def visit(reference: str) -> None:
            if reference in visiting:
                cycle = visiting[visiting.index(reference):] + [reference]
                raise ValueError(f"循环依赖: {' -> '.join(cycle)}")
            if reference in visited:
                return
            if reference not in self.folders:
                owner = f"{visiting[-1]} 依赖的" if visiting else ""
                raise ValueError(f"{owner}库不存在: {reference}")
            visiting.append(reference)
            for dependency in self.depends[reference]:
                visit(dependency)
            visiting.pop()
            visited.add(reference)
            order.append(reference)

        for target in self.folders if targets is None else targets:
            visit(target)
        return order


def discover_libraries() -> LibraryGraph:
    packages = scan_packages()
    graph = LibraryGraph()

    for reference, folder in packages.items():
        try:
            _, depends, _ = parse_recipe_cmake(folder / "recipe.cmake")
            missing = [
                dependency
                for dependency in depends
                if dependency not in packages
            ]
            if missing:
                raise ValueError(
                    f"依赖不存在或未指定版本: {', '.join(missing)}；"
                    "请使用完整的库名/版本"
                )
        except (ValueError, OSError) as exc:
            raise ValueError(f"{reference}: {exc}") from exc

        graph.add(reference, folder, depends)

    return graph


def build_library(reference: str, graph: LibraryGraph, profile: str, build_profile: str) -> bool:
    folder = graph.folders[reference]
    if not (folder / "conanfile.py").is_file():
        print(f"❌ {reference}: 缺少 conanfile.py，请先运行 scripts/generate_conanfiles.py")
        return False
    command = ["conan", "create", str(folder), "-pr:h", profile, "-pr:b", build_profile]
    print(f"\n构建: {reference}\n命令: {shlex.join(command)}", flush=True)
    try:
        subprocess.run(command, cwd=REPO_ROOT, check=True)
    except (subprocess.CalledProcessError, OSError) as exc:
        print(f"❌ {reference} 构建失败: {exc}")
        return False
    print(f"✓ {reference} 构建成功")
    return True


def cmd_build(
    targets: list[str], graph: LibraryGraph, dry_run: bool, profile: str,
    build_profile: str = "default",
) -> int:
    order = graph.resolve(targets or None)
    print(f"构建顺序: {' -> '.join(order)}", flush=True)
    if dry_run:
        return 0

    failed = set()
    skipped = []
    for reference in order:
        # 失败沿依赖关系传播，独立的库仍然继续构建。
        blocked = [dep for dep in graph.depends[reference] if dep in failed]
        if blocked:
            print(f"⚠ 跳过 {reference}: 依赖构建未成功: {', '.join(blocked)}")
            failed.add(reference)
            skipped.append(reference)
        elif not build_library(reference, graph, profile, build_profile):
            failed.add(reference)

    if failed:
        print(f"\n❌ 未完成: {', '.join(reference for reference in order if reference in failed)}")
        if skipped:
            print(f"其中跳过: {', '.join(skipped)}")
        return 1
    print("\n✅ 全部成功")
    return 0


def cmd_clean(targets: list[str], graph: LibraryGraph) -> int:
    for reference in targets or graph.folders:
        build_dir = graph.folders[reference] / "build"
        if build_dir.is_symlink():
            build_dir.unlink()
            print(f"✓ 清理链接: {build_dir}")
        elif build_dir.exists():
            shutil.rmtree(build_dir)
            print(f"✓ 清理: {build_dir}")
        else:
            print(f"- {reference}: 无构建产物")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="按依赖顺序构建第三方库")
    parser.add_argument("libraries", nargs="*", help="要构建的库名（默认全部）")
    actions = parser.add_mutually_exclusive_group()
    actions.add_argument("--list", action="store_true", help="列出所有库")
    actions.add_argument("--clean", action="store_true", help="清理各库本地 build 目录")
    actions.add_argument("--dry-run", action="store_true", help="只显示构建顺序")
    parser.add_argument("-pr", "-pr:h", "--profile", default="default", help="host profile（默认 default）")
    parser.add_argument("-pr:b", "--build-profile", default="default", help="build profile（默认 default）")
    args = parser.parse_args()

    try:
        graph = discover_libraries()
        if not graph.folders:
            raise ValueError("没有发现任何库")
        unknown = [reference for reference in args.libraries if reference not in graph.folders]
        if unknown:
            raise ValueError(f"库不存在: {', '.join(unknown)}；可用: {', '.join(graph.folders)}")
        if args.list:
            for reference in args.libraries or graph.folders:
                deps = graph.depends[reference]
                suffix = f" (依赖: {', '.join(deps)})" if deps else ""
                print(f"  {reference}{suffix}")
            return 0
        if args.clean:
            return cmd_clean(args.libraries, graph)
        return cmd_build(args.libraries, graph, args.dry_run, args.profile, args.build_profile)
    except (ValueError, OSError) as exc:
        print(f"❌ {exc}")
        return 1
    except KeyboardInterrupt:
        print("\n构建已中断")
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
