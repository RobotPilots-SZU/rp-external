from conan import ConanFile


class EtlConan(ConanFile):
    name = "etl"
    version = "20.49.0"
    package_type = "header-library"
    use_git_version = False
    python_requires = "rp_externals_base/[>=0.1.0 <0.2.0, include_prerelease]"
    python_requires_extend = "rp_externals_base.RpExternalsBase"

    settings = "os", "arch", "compiler", "build_type"
    exports_sources = "*", "!conanfile.py", "!build/*", "!__pycache__/*"

    rp_depends = ()
    rp_includedirs = ('include',)
