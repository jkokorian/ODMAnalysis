"""
    Copyright (C) 2014 Delft University of Technology, The Netherlands

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""from setuptools import setup

setup(name='odmanalysis',
      version='0.5',
      description='Toolkit for analyzing optical displacement measurements with subpixel accuracy.',
      url='http://github.com/jkokorian/odmanalysis',
      author='J. Kokorian',
      author_email='J.Kokorian@TUDelft.nl',
      license='GPL',
      packages=[
          'odmanalysis',
          'odmanalysis.gui',
          'odmanalysis.plots',
          'odmanalysis.fitfunctions',
          'odmanalysis.stats',
          'odmanalysis.chunkhandling',
          'odmanalysis.scripts'
          ],
      install_requires=[
          'numpy',
          'scipy',
          'pandas',
          'matplotlib',
          'watchdog'
          ],
      entry_points={
          'console_scripts': [
              'odm_analyze=odmanalysis.scripts.AnalyzeRawODMData:main',
              'odm_plot=odmanalysis.scripts.MakeODMPlots:main',
              'odm_fit=odmanalysis.scripts.FitRawODMData:main',
              'odm_fitfast=odmanalysis.scripts.FitFastRawODMData:main',
              'odm_noise=odmanalysis.scripts.AnalyzeDisplacementCurveNoise:main',
              'odm_watch=odmanalysis.scripts.ODMWatchdog:main',
              'odm_clean_data=odmanalysis.scripts.RemoveUnitsFromRawData:main'
          ]},
      zip_safe=False)