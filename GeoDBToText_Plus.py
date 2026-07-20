# ---------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------

import arcpy
import os
import csv
from arcpy import metadata as md



# ---------------------------------------------------------------------
# Input parameters
# ---------------------------------------------------------------------

GeoDB = arcpy.GetParameterAsText(0)

# DefaultContact = arcpy.GetParameterAsText(1)
Delimiter = "|"

# Set workspace
arcpy.env.workspace = GeoDB



# ---------------------------------------------------------------------
# Export Feature Class to JSON
# ---------------------------------------------------------------------

def ExportJSON(FeatureClass):

    desc = arcpy.Describe(FeatureClass)

    JsonFile = os.path.join(
        os.path.dirname(arcpy.env.workspace),
        desc.baseName + ".json"
    )

    arcpy.AddMessage(f"Input: {FeatureClass}")
    arcpy.AddMessage(f"Output: {JsonFile}")

    arcpy.conversion.FeaturesToJSON(
        FeatureClass,
        JsonFile,
        "NOT_FORMATTED"
    )


# def ExportJSON(FeatureClass):

#     try:

#         JsonFile = os.path.join(os.path.dirname(arcpy.env.workspace),
#                                 FeatureClass + ".json")

#         if os.path.exists(JsonFile):
#             arcpy.AddMessage("File exists: " + JsonFile + ". Deleted")
#             os.remove(JsonFile)

#         arcpy.AddMessage("Exporting " + JsonFile)

#         arcpy.FeaturesToJSON_conversion(
#             FeatureClass,
#             JsonFile,
#             "NOT_FORMATTED"
#         )

#     except Exception as e:
#         arcpy.AddMessage(
#             "Export failed for FeatureClass: {} {}".format(
#                 FeatureClass, str(e)
#             )
#         )


# ---------------------------------------------------------------------
# Function to clean HTML tags from meatadata
# ---------------------------------------------------------------------
import re
from html import unescape

def clean_metadata(text):
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", "", text)
    return unescape(text).strip()



# ---------------------------------------------------------------------
# Export Metadata from GeoDatabase and Feature Dataset
# ---------------------------------------------------------------------

def ExportMetadata(InputObject, OutputFolder):

    try:

        meta = md.Metadata(InputObject)

        desc = arcpy.Describe(InputObject)

        ObjectName = os.path.basename(InputObject)

        CSVPath = os.path.join(
            OutputFolder,
            ObjectName + "_metadata.csv"
        )

        if os.path.exists(CSVPath):
            arcpy.AddMessage("File exists: " + CSVPath + ". Deleted")
            os.remove(CSVPath)

        with open(CSVPath, "w", encoding="utf-8", newline="") as f:

            CSVFile = csv.writer(f)

            CSVFile.writerow([f"{desc.dataType} Metadata"])
            CSVFile.writerow([])

            CSVFile.writerow(["Title", meta.title])
            CSVFile.writerow(["Tags", meta.tags])
            CSVFile.writerow(["Summary", clean_metadata(meta.summary)])
            CSVFile.writerow(["Description", clean_metadata(meta.description)])
            CSVFile.writerow(["Credits", clean_metadata(meta.credits)])
            CSVFile.writerow(["Use Limitations", clean_metadata(meta.accessConstraints)])

        #CSVFile.close()

    except Exception as e:
        arcpy.AddMessage(
            "Metadata export failed: " + str(e)
        )



# ---------------------------------------------------------------------
# Export Feature Class to CSV
# ---------------------------------------------------------------------

def ExportCSV(FeatureClass, OutputFolder):

    try:

        # Read feature class metadata
        metadata = md.Metadata(FeatureClass)

        Title = metadata.title
        Tags = metadata.tags
        Summary = clean_metadata(metadata.summary)
        Description = clean_metadata(metadata.description)
        Credits = clean_metadata(metadata.credits)
        UseLimitations = clean_metadata(metadata.accessConstraints)

        # Determine object type
        desc = arcpy.Describe(FeatureClass)

        arcpy.AddMessage(f"FeatureClass: {FeatureClass}")
        arcpy.AddMessage(f"desc.name: {desc.name}")
        arcpy.AddMessage(f"desc.baseName: {desc.baseName}")
        arcpy.AddMessage(f"desc.dataType: {desc.dataType}")

        CSVPath = os.path.join(
            OutputFolder,
            f"{desc.baseName}.csv"
            )

        if os.path.exists(CSVPath):
            arcpy.AddMessage("File exists: " + CSVPath + ". Deleted")
            os.remove(CSVPath)


        CSVFile = open(CSVPath, "w", encoding="utf-8", newline="")

        writer = csv.writer(CSVFile)


        # Feature class metadata
        writer.writerow(["Feature Class Metadata"])
        writer.writerow([])
        writer.writerow(["Title", Title])
        writer.writerow(["Tags", Tags])
        writer.writerow(["Summary", Summary])
        writer.writerow(["Description", Description])
        writer.writerow(["Credits", Credits])
        writer.writerow(["Use Limitations", UseLimitations])
        writer.writerow([])

        spatial_ref = arcpy.Describe(FeatureClass).spatialReference
        writer.writerow(["Spatial Reference"])
        writer.writerow(["Name", spatial_ref.name])
        writer.writerow(["WKID", spatial_ref.factoryCode])
        writer.writerow(["Well-Known Text (WKT)", spatial_ref.exportToString()])
        writer.writerow([])
        writer.writerow(["Purpose", 
                         f"This file is a human and machine readable equivalent of the layer: "
                         f"{FeatureClass}, "
                         f"exported from the ESRI personal geodatabase: "
                         f"{os.path.basename(GeoDB)}, "
                         f"and was generated to back up and archive the parent dataset "
                         f"for posterity in a non-proprietary text format."])
        writer.writerow(["Note",
                         "Row field values are separated by a pipe character | "
                         "to avoid confusion with commas in WKT geometry."])
        writer.writerow([])
    

        fields = arcpy.ListFields(FeatureClass)
        field_names = [field.name for field in fields]
        cursor_fields = ["Shape@WKT"] + field_names
    
        writer = csv.writer(CSVFile,
                            delimiter="|",
                            quoting=csv.QUOTE_MINIMAL)

        writer.writerow(cursor_fields)

        with arcpy.da.SearchCursor(FeatureClass, cursor_fields) as cursor:
            for row in cursor:
                writer.writerow(["" if v is None else v for v in row])

        CSVFile.close()

    except Exception as e:
        arcpy.AddMessage(
            "Export failed for FeatureClass: {} {}".format(
                FeatureClass, str(e)
            )
        )



# ---------------------------------------------------------------------
# Process all feature classes
# ---------------------------------------------------------------------


arcpy.env.workspace = GeoDB
OutputFolder = os.path.dirname(GeoDB)

ExportMetadata(GeoDB, OutputFolder)


# Root-level feature classes
for FeatureClass in arcpy.ListFeatureClasses() or []:

    FCPath = os.path.join(GeoDB, FeatureClass)

    arcpy.AddMessage("Processing " + FeatureClass)

    ExportCSV(FCPath, OutputFolder)
    ExportJSON(FCPath)


# Feature classes inside feature datasets
for FeatureDataset in arcpy.ListDatasets(feature_type="Feature") or []:

    FDPath = os.path.join(GeoDB, FeatureDataset)
    ExportMetadata(FDPath, OutputFolder)

    for DatasetFC in arcpy.ListFeatureClasses(feature_dataset=FeatureDataset) or []:

        DatasetFCPath = os.path.join(
            GeoDB,
            FeatureDataset,
            DatasetFC
        )

        arcpy.AddMessage("Processing " + DatasetFCPath)

        ExportCSV(DatasetFCPath, OutputFolder)
        ExportJSON(DatasetFCPath)