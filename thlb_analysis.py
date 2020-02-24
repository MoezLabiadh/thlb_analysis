'''
This script generates generate Timber harvest metrics, mainly areas and volumes, for a specific area of interest (AOI). The AOI can be either a Timber supply Area, an Operating area or other ( FN claimed area,?). Tha main steps are:
    1) Clip the input layers to the AOI extent (VRI, OGMA, THLB,...). Other input layers can be added depending on the scope of the analysis
    2) Perform a spatial overlay of the clipped input layers
    3) Add and populate fields based on defined rules: mature timber, merchantability, areas with harvest constraints..
    4) Calculate THLB areas and volumes
    5) Generate metrics by Licensee or Operating area (summary statistics)

'''
import os
import arcpy
from arcpy import env

arcpy.env.overwriteOutput = True
spatialRef = arcpy.SpatialReference(3005)

#Create variables for input layers

BCGWcon = r'Database Connections\BCGW.sde'
VRI = os.path.join (BCGWcon, "WHSE_FOREST_VEGETATION.VEG_COMP_LYR_R1_POLY")
OGMA = os.path.join (BCGWcon, "WHSE_LAND_USE_PLANNING.RMP_OGMA_LEGAL_ALL_SVW")
Licensees = os.path.join (BCGWcon, "REG_LAND_AND_NATURAL_RESOURCE.FOREST_LICENSEE_OPER_SP")

##VRI = r'\\bctsdata.bcgov\data\tko_root\GIS_WORKSPACE\MLABIADH\PyMe\thlb_analysis\data\thlb_analysis.gdb\test\vri_tko'
##OGMA = r'\\bctsdata.bcgov\data\tko_root\GIS_WORKSPACE\MLABIADH\PyMe\thlb_analysis\data\thlb_analysis.gdb\test\OGMA_tko'
##Licensees = r'\\bctsdata.bcgov\data\tko_root\GIS_WORKSPACE\MLABIADH\PyMe\thlb_analysis\data\thlb_analysis.gdb\test\licensees_tko'

THLB = r'\\spatialfiles2.bcgov\archive\FOR\VIC\HTS\FAIB_DATA_FOR_DISTRIBUTION\THLB\Consolidated_THLB.gdb\SIR\THLB_data_SIR'
BEC_HLP = r'\\bctsdata.bcgov\data\tko_root\GIS_WORKSPACE\Tools\DrilldownTKO\Supporting Data\AdditionalDatasetsTKO.gdb\BEC_HLP_FTBO'

WorkGDB = r'\\bctsdata.bcgov\data\tko_root\GIS_WORKSPACE\MLABIADH\PyMe\thlb_analysis\data\thlb_analysis.gdb'
AOI = r'\\bctsdata.bcgov\data\tko_root\GIS_WORKSPACE\MLABIADH\PyMe\thlb_analysis\data\thlb_analysis.gdb\Boundary_TSA' # this layer will be specified by the user

#Clip the input layers to the AOI extent

toClip = arcpy.CreateFeatureDataset_management(WorkGDB, "inputs", spatialRef)
inputsPath = os.path.join(WorkGDB,str(toClip))

FCs = [VRI,OGMA,Licensees,THLB,BEC_HLP]

for FC in FCs:
    filePref = os.path.basename(AOI)
    fileName = os.path.basename(FC)
    print("Preparing input layers. Clipping", fileName)
    arcpy.Clip_analysis(FC, AOI, os.path.join (inputsPath, (filePref + "_" + fileName)))

#Spatial overlay (union) of input layers

arcpy.env.workspace = inputsPath
unionInputs = arcpy.ListFeatureClasses()
print ("Creating the THLB analysis Resultant...spatial overlay (union) in progress.")
thlb_analysis_resultant = os.path.join (WorkGDB, "thlb_analysis_resultant")
arcpy.Union_analysis (unionInputs, thlb_analysis_resultant , "ALL")
arcpy.DeleteIdentical_management (thlb_analysis_resultant, "GEOMETRY")

# Add new fields to the resultant and populate them

resutantFields = arcpy.ListFields (thlb_analysis_resultant)
newFieldsTXT = ["OGMA", "MATURE", "MARCHENTABILITY"]
newFieldsFLOAT = ["new_AREA_ha", "THLB_area_ha", "THLB_volume_m3"]

for field in newFieldsTXT:
    if field not in resutantFields:
        print ("Adding field", field)
        arcpy.AddField_management(thlb_analysis_resultant, field, "TEXT", "", "", 5)
    else:
        pass

for field2 in newFieldsFLOAT:
    if field2 not in resutantFields:
        print ("Adding field", field2)
        arcpy.AddField_management(thlb_analysis_resultant, field2, "DOUBLE")
    else:
        pass

UpdateFields = newFieldsTXT + newFieldsFLOAT + ["NON_LEGAL_OGMA_PROVID", "MATURE_YRS", "PROJ_AGE_1", "LIVE_STAND_VOLUME_125","THLB_FACT", "GEOMETRY_Area"]

#Populate the new fields

##arcpy.CalculateField_management (thlb_analysis_resultant,"new_AREA_ha",'!shape.area!@hectares','PYTHON')
##arcpy.CalculateGeometryAttributes_management (thlb_analysis_resultant, ["new_AREA_ha", "AREA"], "" , "HECTARES")

print ("Populating new fields...in progress")

with arcpy.da.UpdateCursor(thlb_analysis_resultant, UpdateFields) as cursor:
  for row in cursor:
    if row [6] != "" or row [6] is None:
        row[0] = "Y"
    else:
        row[0] = "N"

    if (row [7] == ">100" and row [8] > 100) or (row [7] == ">120" and row [8] > 120):
        row[1] = "Y"
    else:
        row[1] = "N"

    if row [9] > 100:
        row[2] = "Y"
    else:
        row[2] = "N"

    row[3] = row[11]/10000

    row[4] = row[3]* row[10]

    if row[9] is None:
        row[9] = 0

    row[5] = row[4] * row[9]

    cursor.updateRow(row)

print ("New fields populated")

# Compute summary statistics and export to dbf
print ("Computing summary statistics")

AllStats = os.path.join (WorkGDB, "AllStats")
whereClauseAllLicencees =""" "OGMA" = 'N' """ + 'and' + """ "MATURE" = 'Y' """ + 'and' + """ "MARCHENTABILITY" = 'Y' """
lyr_all = arcpy.MakeFeatureLayer_management (thlb_analysis_resultant, "lyr_all")
arcpy.SelectLayerByAttribute_management (lyr_all, "NEW_SELECTION", whereClauseAllLicencees)
arcpy.Statistics_analysis(lyr_all, AllStats, [["THLB_area_ha", "SUM"], ["THLB_volume_m3", "SUM"] ], "LICENSEE_OPER_AREAS_NAME")
arcpy.Delete_management(lyr_all)
print ("Created summary statistics for All Licensees")

BCTSStats = os.path.join (WorkGDB, "BCTSStats")
whereClauseBCTSonly =""" "OGMA" = 'N' """ + 'and' + """ "MATURE" = 'Y' """ + 'and' + """ "MARCHENTABILITY" = 'Y' """ + 'and' + """ "LICENSEE_OPER_AREAS_NAME" = 'BC Timber Sales - Kootenay' """
lyr_BCTS = arcpy.MakeFeatureLayer_management (thlb_analysis_resultant, "lyr_BCTS")
arcpy.SelectLayerByAttribute_management (lyr_BCTS, "NEW_SELECTION", whereClauseBCTSonly)
arcpy.Statistics_analysis(lyr_BCTS, BCTSStats, [["THLB_area_ha", "SUM"], ["THLB_volume_m3", "SUM"] ], "LICENSEE_OPER_AREAS_TENURE")
arcpy.Delete_management(lyr_BCTS)
print ("Created summary statistics for ABCTS Op Areas")

print ("THLB analysis completed successfully")