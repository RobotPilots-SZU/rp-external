from conan import ConanFile


class NanopbConan(ConanFile):
    name = "nanopb"
    version = "0.4.9.2"
    package_type = "library"
    python_requires = "rp_externals_base/[>=0.1.0 <0.2.0]"
    python_requires_extend = "rp_externals_base.RpExternalsBase"

    settings = "os", "arch", "compiler", "build_type"
    exports_sources = "*", "!conanfile.py", "!build/*", "!__pycache__/*"

    rp_depends = ()
    rp_includedirs = ('include/nanopb',)
