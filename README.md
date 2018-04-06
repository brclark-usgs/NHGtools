# NGHtools

Introduction
--------------------------------------------

The purpose of the NHG is to define a consistent spatial extent and resolution as the foundation for a National Hydrogeologic Framework (NHF).

The NHG extent was designed to include the area simulated by the National Water Model (NWM) though the individual grid cells do not align with the NWM grid because of differing spatial projections. Additionally, the NHG position was created to align with the USGS National Land Cover Database (NLCD). The NLCD grid contains cells at a spatial resolution of 30 meters. Therefore, the NHG cells (1 km spatial resolution) aligns with the NLCD at intervals of 3 km in the north-south and east-west directions. It is envisioned that applications requiring finer resolution than 1-km would be based on multiples of the NHG cell sizes (such as 250 meter or 500 meter cells), and would be developed to align with the NHG cells

Documentation
--------------------------------------------

The NHG is documented through a USGS Data Release at: 

Examples
-------------------------------------------

#### [jupyter notebook exmples](examples/makeLocalGrid.ipynb)

Installation
------------------------------------------

**Python versions:**

NHGtools has been tested with  **Python** 3.6

**Dependencies:**

NHGtools requires:
**GDAL** 2.
**NumPy** 1.

<!-- **For base Python distributions:** -->

<!-- To install NHGtools from the git repository type: -->

    <!-- pip install https://github.com/brclark-usgs/NHGtools -->



 
