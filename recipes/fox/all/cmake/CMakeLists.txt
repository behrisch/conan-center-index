# The CMakeLists.txt here and in the subdirectories are an adapted copy of
# https://github.com/devinsmith/fox/tree/release/1.6
# Currently they are only used for the windows build.

# Here are the steps to get conan up and running:
# git clone https://github.com/behrisch/conan-center-index
# python -m venv conan_env
# . conan_env/bin/activate
# pip install conan
# mkdir local_repo
# conan remote add local_repo "$PWD/local_repo" --type=local-recipes-index --allowed-packages="fox/*"
# conan profile detect
# conan create recipes/fox/all --version=1.6.59 --build=missing

cmake_minimum_required(VERSION 3.0.2)

project(fox-toolkit VERSION 1.6.59)

add_subdirectory(src)
add_subdirectory(utils)
