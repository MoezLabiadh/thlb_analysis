# thlb_analysis
This script generates Timber harvest metrics, mainly areas and volumes, for a specific area of interest (AOI). The AOI can be either a Timber supply Area, an Operating area or other ( FN claimed area,?). Tha main steps are:
    1) Clip the input layers to the AOI extent (VRI, OGMA, THLB,...). Other input layers can be added depending on the scope of the analysis
    2) Perform a spatial overlay of the clipped input layers
    3) Add and populate fields based on defined rules: mature timber, merchantability, areas with harvest constraints..
    4) Calculate THLB areas and volumes
    5) Generate metrics by Licensee or Operating area (summary statistics
