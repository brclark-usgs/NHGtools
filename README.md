# NHGtools

Introduction
--------------------------------------------

The purpose of the National Hydrgeologic Grid (NHG) is to define a consistent spatial extent and resolution as the foundation for a National Hydrogeologic Database (NHGD).

The NHG extent was designed to include the area simulated by the [National Water Model (NWM)](http://water.noaa.gov/about/nwm) though the individual grid cells do not align with the NWM grid because of differing spatial projections. Additionally, the NHG position was created to align with the USGS [National Land Cover Database (NLCD)](https://www.mrlc.gov/index.php). The NLCD grid contains cells at a spatial resolution of 30 meters. Therefore, the NHG cells (1 km spatial resolution) aligns with the NLCD at intervals of 3 km in the north-south and east-west directions. It is envisioned that applications requiring finer resolution than 1-km would be based on multiples of the NHG cell sizes (such as 250 meter or 500 meter cells), and would be developed to align with the NHG cells

<!-- Documentation -->

<!-- The NHG is documented through a USGS Data Release at:  -->

Examples
--------------------------------------------

#### [jupyter notebook exmple](examples/makeLocalGrid.ipynb)

Installation
--------------------------------------------

**Python versions:**

NHGtools has been tested with  **Python** 3.6

**Dependencies:**

NHGtools requires at least:
**GDAL** 2.2
**NumPy** 1.13

Documentation
--------------------------------------------

The NHG and associated GIS data is available at [https://doi.org/10.5066/F7P84B24](https://doi.org/10.5066/F7P84B24) 

<!-- **For base Python distributions:** -->

<!-- To install NHGtools from the git repository type: -->

--------------------------------------------

*This software is preliminary or provisional and is subject to revision. It is being provided to meet the need for timely best science. The software has not received final approval by the U.S. Geological Survey (USGS). No warranty, expressed or implied, is made by the USGS or the U.S. Government as to the functionality of the software and related material nor shall the fact of release constitute any such warranty. The software is provided on the condition that neither the USGS nor the U.S. Government shall be held liable for any damages resulting from the authorized or unauthorized use of the software.*


 
