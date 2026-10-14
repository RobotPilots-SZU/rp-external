# rp-external

## 1. 系统环境准备
1. python3.12及以上,camke 3.24及以上，arm-none-eabi-gcc 11.0及以上
2. 创建虚拟环境 `python -m .venv ./.venv`
3. 进入虚拟环境： `source ./.venv/bin/activate`
4. 安装`conan pip install conan`。确保conan版本在2.0以上

## 2. 基本使用方法
1. 创建rp_externals_base包
~~~shell
cd ./rp_externals_base
conan create . -pr XXX
conan list # 查看是否有构建出来的包
~~~
2. 构建外部库
~~~shell
python ./scripts/generate_conanfiles.py # 给所有的外部库生成conanfile
python ./scripts/build_externals.py # 默认构建所有外部库
~~~
