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
"""# -*- coding: utf-8 -*-
"""
Created on Tue Sep 17 21:40:45 2013

@author: jkokorian
"""

from scipy import stats
import numpy as np

def makeStatsDescriptionDict(a):
        sd = {}
        sd['size'],(sd['min'],sd['max']),sd['mean'],sd['var'],sd['skew'],sd['kurt'] = stats.describe(a)
        return sd
        
def printStatsDescriptionDict(d):
    sMin = "minimum: %0.2f nm" % d['min']
    sMax = "maximum: %0.2f nm" % d['max']
    sMean = "mean: %0.2f nm" % d['mean']
    sStd = "std.dev: %0.2f nm" % np.sqrt(d['var'])
    sVar = "variance: %0.2f nm^2" % d['var']
    sSkew = "skewness: %0.2f" % d['skew']
    sKurt = "kurtosis: %0.2f" % d['kurt']
    
    return "\n".join([sMin,sMax,sMean,sStd,sVar,sSkew,sKurt])
    
def makeStatsDescriptionString(a):
    d = makeStatsDescriptionDict(a)
    return printStatsDescriptionDict(d)