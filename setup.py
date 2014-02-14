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
      scripts=[
          'scripts/AnalyzeRawODMData.py',
          'scripts/MakeODMPlots.py',
          'scripts/FitRawODMData.py',
          'scripts/AnalyzeDisplacementCurveNoise.py'
          ],
      zip_safe=False)