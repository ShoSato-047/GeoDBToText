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

# Optional fallback values if metadata is missing
DefaultTitle = arcpy.GetParameterAsText(1)
DefaultTags = arcpy.GetParameterAsText(2)
DefaultSummary = arcpy.GetParameterAsText(3)
DefaultDescription = arcpy.GetParameterAsText(4)
DefaultCredits = arcpy.GetParameterAsText(5)
DefaultUseLimitations = arcpy.GetParameterAsText(6)
DefaultContact = arcpy.GetParameterAsText(7)
Delimiter = arcpy.GetParameterAsText(8)

# Set workspace
arcpy.env.workspace = GeoDB



# ---------------------------------------------------------------------
# Export Feature Class to JSON
# ---------------------------------------------------------------------

def ExportJSON(FeatureClass):

    try:

        JsonFile = os.path.join(os.path.dirname(arcpy.env.workspace),
                                FeatureClass + ".json")

        if os.path.exists(JsonFile):
            arcpy.AddMessage("File exists: " + JsonFile + ". Deleted")
            os.remove(JsonFile)

        arcpy.AddMessage("Exporting " + JsonFile)

        arcpy.FeaturesToJSON_conversion(
            FeatureClass,
            JsonFile,
            "NOT_FORMATTED"
        )

    except Exception as e:
        arcpy.AddMessage(
            "Export failed for FeatureClass: {} {}".format(
                FeatureClass, str(e)
            )
        )



# ---------------------------------------------------------------------
# Export Feature Class to CSV
# ---------------------------------------------------------------------

def ExportCSV(FeatureClass):

    try:

        # Read metadata from the feature class
        meta = md.Metadata(FeatureClass)

        DatasetTitle = meta.title or DefaultTitle
        Tags = meta.tags or DefaultTags
        Summary = meta.summary or DefaultSummary
        Description = meta.description or DefaultDescription
        Credits = meta.credits or DefaultCredits
        UseLimitations = meta.accessConstraints or DefaultUseLimitations
        DatasetContact = DefaultContact

        CSVPath = os.path.join(
            os.path.dirname(arcpy.env.workspace),
            FeatureClass + ".csv"
        )

        if os.path.exists(CSVPath):
            arcpy.AddMessage("File exists: " + CSVPath + ". Deleted")
            os.remove(CSVPath)

        CSVFile = open(CSVPath, "a", encoding="utf-8")

        fields = arcpy.ListFields(FeatureClass)

        field_names = [field.name for field in fields]
        cursor_fields = ["Shape@WKT"] + field_names

        CSVFile.write(f"Title:\n{DatasetTitle}\n\n")
        CSVFile.write(f"Tags:\n{Tags}\n\n")
        CSVFile.write(f"Summary:\n{Summary}\n\n")
        CSVFile.write(f"Description:\n{Description}\n\n")
        CSVFile.write(f"Credits:\n{Credits}\n\n")
        CSVFile.write(f"Use Limitations:\n{UseLimitations}\n\n")
        CSVFile.write(f"Dataset Contact:\n{DatasetContact}\n\n")
        
        spatial_ref = arcpy.Describe(FeatureClass).spatialReference
        CSVFile.write("Spatial Reference:\n"
                      f"Name: {spatial_ref.name}\n"
                      f"WKID: {spatial_ref.factoryCode}\n\n"
                      "Well-Known Text (WKT):\n"
                      f"{spatial_ref.exportToString()}\n\n"
                      )

        CSVFile.write("Purpose:\n"
                      "This file is a human and machine readable equivalent of the layer\n"
                      f">>>{FeatureClass}\n"
                      "exported from the ESRI personal geodatabase\n"
                      f">>>{os.path.basename(GeoDB)}\n"
                      "and was generated to back up and archive the parent dataset\n"
                      "for posterity in a non-proprietary text format.\n\n"
                      )

        CSVFile.write("Note:\n"
                      "Row field values are separated by a pipe character |"
                      "to avoid confusion with commas in WKT geometry.\n\n"
                      )

        CSVFile.write(Delimiter.join(cursor_fields) + "\n")

        with arcpy.da.SearchCursor(FeatureClass, cursor_fields) as cursor:
            for row in cursor:
                CSVFile.write(
                    Delimiter.join("" if v is None else str(v) for v in row)
                )
                CSVFile.write("\n")

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

try:

    FeatureClasses = arcpy.ListFeatureClasses()

    for FeatureClass in FeatureClasses:

        arcpy.AddMessage("Processing " + FeatureClass)

        ExportCSV(FeatureClass)
        ExportJSON(FeatureClass)

except Exception as e:

    arcpy.AddMessage("Error: " + str(e))