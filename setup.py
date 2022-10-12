# This file is part of K-edge-swap.
#
#    K-edge-swap is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
#
#    K-edge-swap is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License along with Foobar. If not, see <https://www.gnu.org/licenses/>. 


"""Setup script for the K-edge-swap package"""

import os
import kedgeswap
from setuptools import setup, find_packages

SETUP_DIR = os.path.dirname(os.path.abspath(__file__))
VERSION = kedgeswap.__version__


setup(
    name='kedgeswap',
    version=VERSION,
    packages=find_packages(exclude=['test']),
    zip_safe=True,
    scripts=[],

    # install python dependencies from PyPI
    #install_requires=REQUIREMENTS,

    # include any files in kedgeswap/share
    package_data={'kedgeswap': ['share/*.*']},

    ## define the command-line script to use
    #entry_points={'console_scripts': [
    #    'kedgeswap = kedgeswap.commands.abkhazia_main:main']},

    # metadata for upload to PyPI
    author='Lionel Tabourier, Julien Karadayi etc.. ?',
    description='Perform K-edge swaps on graph to generate randomly uniform graph given conditions.',

    #license='GPLv3',
    #keywords='graph generation MCMC Monte Carlo Markov Chain',
    #url='https://github.com/bootphon/abkhazia',
    long_description=open('README.md').read(),
)
