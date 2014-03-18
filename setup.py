from setuptools import setup

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