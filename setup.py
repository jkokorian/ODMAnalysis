from setuptools import setup

setup(name='odmanalysis',
      version='0.3',
      description='Toolkit for analyzing optical displacement measurements with subpixel accuracy.',
      url='http://github.com/jkokorian/odmanalysis',
      author='J. Kokorian',
      author_email='J.Kokorian@TUDelft.nl',
      licence='GPL',
      packages=[
          'odmanalysis',
          'odmanalysis.gui',
          'odmanalysis.plots',
          'odmanalysis.fitfunctions',
          'odmanalysis.stats'
          ],
      install_requires=[
          'numpy',
          'scipy',
          'pandas',
          'matplotlib'
          ],
      entry_points={
          'console_scripts': [
              'odm_analyze=odmanalysis.AnalyzeRawODMData:main',
              'odm_plot=odmanalysis.MakeODMPlots:main',
              'odm_fit=odmanalysis.FitRawODMData:main',
              'odm_noise=odmanalysis.AnalyzeDisplacementCurveNoise:main'
          ]},
      zip_safe=False)