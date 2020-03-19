#!/usr/bin/env python

# Copyright (c) 2017-present, Facebook, Inc.
# All rights reserved.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.
#

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext
from pathlib import Path
import sys
import setuptools
import os
import subprocess
import platform
import io

__version__ = '0.1'
# JIEBA_DICT_ROOT = "dict"
JIEBA_SRC_ROOT = "include"
JIEBA_DEPS_SRC_ROOT = "deps"

# Based on https://github.com/facebookresearch/fastText

class get_pybind_include(object):
    """Helper class to determine the pybind11 include path

    The purpose of this class is to postpone importing pybind11
    until it is actually installed, so that the ``get_include()``
    method can be invoked. """

    def __init__(self, user=False):
        try:
            import pybind11
        except ImportError:
            if subprocess.call([sys.executable, '-m', 'pip', 'install', 'pybind11']):
                raise RuntimeError('pybind11 install failed.')

        self.user = user

    def __str__(self):
        import pybind11
        return pybind11.get_include(self.user)

try:
    coverage_index = sys.argv.index('--coverage')
except ValueError:
    coverage = False
else:
    del sys.argv[coverage_index]
    coverage = True


# jieba_dict_path = Path(JIEBA_DICT_ROOT)
# jieba_dict_files = list(map(str, jieba_dict_path.glob('*.utf8')))
# jieba_pos_dict_path = Path(JIEBA_DICT_ROOT) / "pos_dict"
# jieba_pos_dict_files = list(map(str, jieba_pos_dict_path.glob('*.utf8')))

jieba_src_path = Path(JIEBA_SRC_ROOT) / "cppjieba"
jieba_src_files = list(map(str, jieba_src_path.glob('*.hpp')))

jieba_deps_path = Path(JIEBA_DEPS_SRC_ROOT) / "limonp"
jieba_deps_src_files = list(map(str, jieba_deps_path.glob('*.hpp')))


ext_modules = [
    Extension(
        "cppjieba_pybind",
        [
            "python/cppjieba_module/cppjieba/pybind/cppjieba_pybind.cc",
        ], # + jieba_src_cc,
        include_dirs=[
            # Path to pybind11 headers
            get_pybind_include(),
            get_pybind_include(user=True),
            # Path to cppjieba source code
            JIEBA_SRC_ROOT,
            JIEBA_DEPS_SRC_ROOT,
        ],
        language='c++',
        extra_compile_args=["-O0 -fno-inline -fprofile-arcs -pthread -march=native" if coverage else
                            "-O3 -funroll-loops -pthread -march=native"],
    ),
]


# As of Python 3.6, CCompiler has a `has_flag` method.
# cf http://bugs.python.org/issue26689
def has_flag(compiler, flags):
    """Return a boolean indicating whether a flag name is supported on
    the specified compiler.
    """
    import tempfile
    with tempfile.NamedTemporaryFile('w', suffix='.cpp') as f:
        f.write('int main (int argc, char **argv) { return 0; }')
        try:
            compiler.compile([f.name], extra_postargs=flags)
        except setuptools.distutils.errors.CompileError:
            return False
    return True


def cpp_flag(compiler):
    """Return the -std=c++[0x/11/14] compiler flag.
    The c++14 is preferred over c++0x/11 (when it is available).
    """
    standards = ['-std=c++14', '-std=c++11', '-std=c++0x']
    for standard in standards:
        if has_flag(compiler, [standard]):
            return standard
    raise RuntimeError(
        'Unsupported compiler -- at least C++0x support '
        'is needed!'
    )


class BuildExt(build_ext):
    """A custom build extension for adding compiler-specific options."""
    c_opts = {
        'msvc': ['/EHsc'],
        'unix': [],
    }

    def build_extensions(self):
        if sys.platform == 'darwin':
            mac_osx_version = float('.'.join(platform.mac_ver()[0].split('.')[:2]))
            os.environ['MACOSX_DEPLOYMENT_TARGET'] = str(mac_osx_version)
            all_flags = ['-stdlib=libc++', '-mmacosx-version-min=10.7']
            if has_flag(self.compiler, [all_flags[0]]):
                self.c_opts['unix'] += [all_flags[0]]
            elif has_flag(self.compiler, all_flags):
                self.c_opts['unix'] += all_flags
            else:
                raise RuntimeError(
                    'libc++ is needed! Failed to compile with {} and {}.'.
                    format(" ".join(all_flags), all_flags[0])
                )
        ct = self.compiler.compiler_type
        opts = self.c_opts.get(ct, [])
        extra_link_args = []

        if coverage:
            coverage_option = '--coverage'
            opts.append(coverage_option)
            extra_link_args.append(coverage_option)

        if ct == 'unix':
            opts.append('-DVERSION_INFO="%s"' % self.distribution.get_version())
            opts.append(cpp_flag(self.compiler))
            if has_flag(self.compiler, ['-fvisibility=hidden']):
                opts.append('-fvisibility=hidden')
        elif ct == 'msvc':
            opts.append(
                '/DVERSION_INFO=\\"%s\\"' % self.distribution.get_version()
            )
        for ext in self.extensions:
            ext.extra_compile_args = opts
            ext.extra_link_args = extra_link_args
        build_ext.build_extensions(self)


def _get_readme():
    """
    Use pandoc to generate rst from md.
    pandoc --from=markdown --to=rst --output=python/README.rst python/README.md
    """
    with io.open("python/README.md", encoding='utf-8') as fid:
        return fid.read()


setup(
    name='cppjieba',
    version=__version__,
    author='Yam',
    author_email='haoshaochun@gmail.com',
    description='cppjieba Python bindings',
    long_description_content_type='text/markdown',
    long_description=_get_readme(),
    ext_modules=ext_modules,
    url='https://github.com/hscspring/cppjieba',
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Software Development',
        'Topic :: Scientific/Engineering',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX',
        'Operating System :: Unix',
        'Operating System :: MacOS',
    ],
    include_package_data=True,
    install_requires=['pybind11>=2.2', "setuptools >= 0.7.0"],
    cmdclass={'build_ext': BuildExt},
    packages=[
        "cppjieba",
    ],
    package_dir={"": "python/cppjieba_module"},
    # use MANIFEST.in
    # package_data={
    #     'cppjieba': ["dict/*", "dict/pos_dict/*"],
    # },
    # data_files=[
    #     ('cppjieba/include/cppjieba', jieba_src_files),
    #     ('cppjieba/deps/limonp', jieba_deps_src_files),
    # ],
    zip_safe=False,
)
