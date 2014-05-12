ODM Analysis package for Python
===============================

Summary
-------

The 'odmanalysis' package for python is a comprehensive toolkit for the semi-automated analysis of optical-displacement measurements in MEMS devices as published by [Kokorian et al][Kokorian2014a]. It takes a data.csv input file that contains a series of captured intensity profiles at different actuator voltages and and analyzes the displacement of a peak in the intensity profile with respect the the position of the peak in the first intensity profile.


Requirements
------------

ODMAnalysis can be used on any computer with python 2.7x and distutils installed. We used python xy for development, but any other distribution should do. ODMAnalysis does not yet work on python 3.x.


Input data formats
------------------

ODMAnalysis currently supports only a single input data format at present, which is a comma-separated-values file with at least the following columns:

* Timestamp: date/time formatted as mm:dd:YYYY HH:MM:ss.sss
* Actuator Voltage (V): number
* Intensity Profile: a semicolon-separated list of integers, bounded by <>. Like: 

```
<18754;9829387;8723409;...;98238>
```

The intensity profile number array should have the same length for the entire csv file, or be completely empty: <>.

We are working on including tools to extract this kind of data from movie files and such, but for now you will have to cook-up the csv file yourself. We use LabVIEW to do the actual measurements and write the csv files.


Installation
------------

To install directly from github, run:

```
pip install git+git://github.com/jkokorian/ODMAnalysis/
```

Or download the source code, unzip, open a command prompt in the directory where setup.py is located and run:

```
pip install .
```

Or without pip:
```
python setup.py install
```

Usage
-----

ODMAnalysis can be used in two ways: by running the included scripts from the command line or by importing the module into another python script, interactive python session, IPython session or even notebook and calling its functions.

### Builtin Scripts ###

OMDAnalysis makes the following command line commands available:

command | description
------- | -----------
odm_fit | Opens a raw data file and calculates the displacements of a peak in the intensity profiles.
odm_plot | Creates plots from the output data of 'odm_fit'
odm_fitfast | The same as odm_fit, but faster (odm_fit will be made obsolete soon)
odm_watch | Watches a raw data file for changes. Every time a change is detected the new data is analyzed and written to disk.
odm_analyze | odm_fit and odm_plot in succession.
odm_noise | Analyzes the displacement noise from an output file of odm_fit.
odm_clean_data | Removes all units from numerical values in the raw data file. (This was nescessary to be able to process some old files written by LabVIEW)

All scripts display a gui to facilitate user interactions. 


### IPython notebook or any other python script that you write yourself ###

We use interactive python and the IPython notebook in particular to 'play around' with the data that we get. Under the hood, ODMAnalysis relies heavily on 'pandas', a fantastic tool for doing just that. ODMAnalysis contains many functions to easily produce pandas DataFrame objects from the raw input data or from the processed data.

Example for doing something with the analyzed data:
```python
import odmanalysis as odm
import pandas as pd
import matplotlib.pyplot as plt

#load analyzed displacements into pandas dataframe
df = odm.readAnalysisData('odmanalysis.csv')

#plot the displacement versus the actuator voltage of the first measurement cycle only
df1 = df[df.cycleNumber == 1]
plt.plot(df1.actuatorVoltage,df1.displacement)
plt.show()
```

Example for doing something with the raw data:
```python
import odmanalysis as odm
import pandas as pd
import matplotlib.pyplot as plt

#load raw data into dataframe
df = odm.readODMData('data.csv')

#plot the first and last intensity profiles
plt.plot(df.intensityProfile.iloc[0],label='first')
plt.plot(df.intensityProfile.iloc[-1],label='last')
plt.legend()
```

Scientific publications
-----------------------

When you use this code for research and it contributes to a publication, please give the authors credit by citing:

J. Kokorian, F. Buja, U. Staufer and W.M. van Spengen
**"An optical in-plane displacement measurement technique with sub-nanometer accuracy based on curve-fitting"**, 2014, _Proceedings of the IEEE 27th International Conference on Micro Electro Mechanical Systems (MEMS), 2014_, pages 580-583
http://dx.doi.org/10.1109/MEMSYS.2014.6765707


Licence
-------

Copyright (C) 2014 Delft University of Technology

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with this program.  If not, see http://www.gnu.org/licenses/.

[Kokorian2014a]: http://dx.doi.org/10.1109/MEMSYS.2014.6765707  "An optical in-plane displacement measurement technique with sub-nanometer accuracy based on curve-fitting"
