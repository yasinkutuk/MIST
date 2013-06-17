###############################################################################
# Copyright (C) 2013 Jacob Barhak
# Copyright (C) 2009-2012 The Regents of the University of Michigan
# 
# This file is part of the MIcroSimulation Tool (MIST).
# The MIcroSimulation Tool (MIST) is free software: you
# can redistribute it and/or modify it under the terms of the GNU General
# Public License as published by the Free Software Foundation, either
# version 3 of the License, or (at your option) any later version.
# 
# The MIcroSimulation Tool (MIST) is distributed in the
# hope that it will be useful, but WITHOUT ANY WARRANTY; without even the
# implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
###############################################################################
# 
# ADDITIONAL CLARIFICATION
# 
# The MIcroSimulation Tool (MIST) is distributed in the 
# hope that it will be useful, but "as is" and WITHOUT ANY WARRANTY of any 
# kind, including any warranty that it will not infringe on any property 
# rights of another party or the IMPLIED WARRANTIES OF MERCHANTABILITY or 
# FITNESS FOR A PARTICULAR PURPOSE. THE AUTHORS assume no responsibilities 
# with respect to the use of the MIcroSimulation Tool (MIST).  
# 
# The MIcroSimulation Tool (MIST) was derived from the Indirect Estimation  
# and Simulation Tool (IEST) and uses code distributed under the IEST name.
# The change of the name signifies a split from the original design that 
# focuses on microsimulation. For the sake of completeness, the copyright 
# statement from the original tool developed by the University of Michigan
# is provided below and is also mentioned above.
# 
###############################################################################
############################ Original Copyright ###############################
###############################################################################
################################################################################
# Copyright (C) 2009-2012 The Regents of the University of Michigan
# Initially developed by Jacob Barhak, Morton Brown
#
# This file is part of the Indirect Estimation and Simulation Tool (IEST).
# The Indirect Estimation and Simulation Tool (IEST) is free software: you
# can redistribute it and/or modify it under the terms of the GNU General
# Public License as published by the Free Software Foundation, either
# version 3 of the License, or (at your option) any later version.
#
# The Indirect Estimation and Simulation Tool (IEST) is distributed in the
# hope that it will be useful, but WITHOUT ANY WARRANTY; without even the
# implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
################################################################################
#
# This script transforms a CSV spreadsheet with population formulas and A text
# document with rules into model code.
# The script receives as Input:
# 1) An csv file generated from an Spreadsheet with populations
# 2) A text file generated from a word file with tables containing rules
# 3) An IEST Model file. This can be provided as the zip file or as a python
#    file generated by ConvertDataToCode from an IEST zip model file.
# The script returns the following Outputs:
# 1) A new model zip file
# 2) A new model code file from which the model zip file was created
#
# Notes:
# - The Spreadsheet file should be of a certain format:
#   1) The Spreadsheet should contain only distribution based populations
#      not data populations that can be imported through the GUI
#   2) First column contains the names of parameters and other definitions.
#      That serve as titles for information in the rows.
#   3) The following columns will be in groups of 3 columns, from which only
#      the 2nd column will be imported as it contains distribution expressions. 
#      The first and third columns are user texts that explain the second
#      column. 
#   4) The rows titled as "Group Description" and "Internal Code" define
#      the population name and ID. All rows under the title "Parameter" are
#      considered as column names in the population set. All other rows are
#      transformed to Notes. If the row named "Internal Data" exists, it will
#      stop adding information to the Notes otherwise all rows will be aded 
#      until "Parameter" is reached. The row titled as "Reference" will be 
#      ported to the source of the population set.
#   5) The expressions should be valid and use a base of states/parameters that
#      already exists in the model file. Otherwise the code script will be
#      generated without the model and an error will be reported.
# - The Text file should be of a certain format:
#   1) Only rules will be imported from tables with 4 columns and the following
#      columns in the header row : "Affected Parameter"
#                                  "Occurrence probability"
#                                  "Update Rule (New Value)"
#                                  "Notes"
#   2) No non-ASCII characters such as dash, fraction, directional quotes,  
#      are allowed. These are generally generated by Word with AutoCorrect
#      option turned on - consider turning AutoCorrect off to avoid such
#      characters to be created.
#   3) The expressions should be valid and use a base of states/parameters that
#      already exists in the model file. Otherwise the code script will be
#      generated without the model and an error will be reported.

import csv
import sys
import os
import DataDef as DB

def CodeConvertDocAndSpreadSheet(FileNameSpreadSheet, FileNameDoc, FileNameModelCode, ProjectNumberToUpdateWithRules):
    " The function modifies the generated code using a spreadsheet and a doc"
    # Inputs are:
    # FileNameSpreadSheet: CSV file name with population data from a 
    # spreadsheet FileNameDoc: TXT file name with rules from a word document
    # FileNameModelCode: A python file generated from a model
    #
    # Open the files
    # Handle the SpreadSheet file
    if FileNameSpreadSheet != "":
        ImportFileSpreadSheet = open(FileNameSpreadSheet,"rb")
        ReadLinesSpreadSheet = csv.reader(ImportFileSpreadSheet)
        DataReadSpreadSheet = list(ReadLinesSpreadSheet)
        DataReadSpreadSheetTransposed = map(None,*DataReadSpreadSheet)
        ImportFileSpreadSheet.close()
    # Handle the Doc file
    if FileNameDoc != "":
        ImportFileDoc = open(FileNameDoc,"rb")
        ReadLinesDoc = ImportFileDoc.readlines()
        ImportFileDoc.close()
    # Handle the Model file
    ImportFileModel = open(FileNameModelCode,"r")
    ReadLinesModel = ImportFileModel.readlines()
    ImportFileModel.close()
    # This is the except clause for all try commands
    ExceptClause = "except: AnalyzeVersionConversionError()"
    # Process populations file
    print "$"*70
    if FileNameSpreadSheet == "":
        print "Skipping population processing."
    else:
        print "Processing the population File: " + FileNameSpreadSheet
        CommandStrTemplate = "try: DB.PopulationSets.AddNew( DB.PopulationSet(ID = %s, Name = '%s', Source = '%s', Notes = '%s', DerivedFrom = 0, DataColumns = %s, Data = []), ProjectBypassID = 0)"
        NumberOfPopulations = (len(DataReadSpreadSheet[0])-2)/3
        NumberOfRows = len(DataReadSpreadSheet)
        TitleColumn=0
        # Locate title index
        RowTitles = DataReadSpreadSheetTransposed[TitleColumn]
        RowIndexID = RowTitles.index("Internal Code")
        RowIndexName = RowTitles.index("Group Description")
        RowIndexSource = RowTitles.index("Reference")
        StartRowIndexNotes = RowTitles.index("Study Name")
        StartRowIndexEquationData = RowTitles.index("Parameter") + 1
        EndRowIndexNotes = StartRowIndexEquationData - 2
        if "Internal Data" in RowTitles:
            EndRowIndexNotes = min ( EndRowIndexNotes, RowTitles.index("Internal Data") - 1)

        OutStrSpreadSheet = []
        for PopEnum in range(NumberOfPopulations):
            DescriptionColumn = PopEnum*3+2
            EquationColumn = PopEnum*3+3
            ID = DataReadSpreadSheet[RowIndexID][DescriptionColumn]
            Name = DataReadSpreadSheet[RowIndexName][DescriptionColumn]
            Source = DataReadSpreadSheet[RowIndexSource][DescriptionColumn]
            Notes = ""
            print "Processing the population with the name: " + Name
            for RowIndex in range(StartRowIndexNotes, EndRowIndexNotes+1):
                Notes = Notes + RowTitles[RowIndex] + ": " + DataReadSpreadSheet[RowIndex][DescriptionColumn] + ". "
            EquationData = "["
            for RowIndex in range(StartRowIndexEquationData, NumberOfRows):
                EquationData = EquationData + "('" + RowTitles[RowIndex] + "', '" + DataReadSpreadSheet[RowIndex][EquationColumn] + "'), "
            EquationData = EquationData[:-2] + "]"
            OutStrSpreadSheet.append(CommandStrTemplate%(ID, Name, Source, Notes, EquationData) + "\n")
            OutStrSpreadSheet.append(ExceptClause + "\n")
    #### Handle Doc File
    if FileNameDoc == "":
        print "$"*70
        print "Skipping Rules Document File."
    else:
        print "Processing the Rules Document File: " + FileNameModelCode
        # Table start string
        TableStartString = "Affected Parameter\rOccurrence probability\rUpdate Rule (New Value)\rNotes\r"
        CommandStrTemplate = "try: SimRuleList = SimRuleList + [ DB.SimulationRule(AffectedParam = '%s', SimulationPhase = %i, OccurrenceProbability = '%s', AppliedFormula = '%s', Notes = %s)]"
        OutStrDoc = []
        for DocLine in ReadLinesDoc:
            if DocLine.startswith('Initialization Rules:'):
                    SimulationPhase = 0
            elif DocLine.startswith('Pre state transition Rules:'):
                    SimulationPhase = 1
            elif DocLine.startswith('Post state transition Rules:'):
                    SimulationPhase = 3
            # Detect start of relevant table
            if DocLine.startswith(TableStartString):
                # Process table cells from this table
                Cells = DocLine.split("\r")
                print "Processing the rules table that starts with " + Cells[4]
                if (len(Cells) % 4) !=2 or Cells[-2:] != ["", "\n"]:
                    raise ValueError, "Wrong number of cells detected. Please make sure that you do not have new line characters within the table cells - This conversion system is not designed to cope with paragraphs within the table. Also make sure that the table is rectangular and has 4 columns."
                # Remove characters that may not display well in new code
                for (CellLocation, Cell) in enumerate(Cells):
                    # replace funny characters with escape sequence
                    for (CharIndex, Char) in enumerate(Cell):
                        if ord(Char)>=128:
                            raise ValueError, "Invalid character with ord=%i and location %i detected in Rules Table that starts with %s , Line #%i, Column #%i. This character was probably created by word using the autocorrect feature. Common examples include the dash character replacing the hyphen, a copyright character replacing (c), a fraction character replacing 1/2, or the start and end quotation characters, yet other such characters exits. These characters may not display well on all systems and therefore removed. Please remove this character from the document, save it again as text and rerun the conversion from documents to code. Here is the text where the problem was encountered: %s" % (ord(Char), CharIndex, Cells[4], int(CellLocation/4), CellLocation % 4, repr(Cell) )
                # Start processing cells from cell 4
                for Line in range(1, int(len(Cells)/4)):
                    [AffectedParam, OccurrenceProbability, AppliedFormula, Notes] = Cells[(Line*4):(Line*4+4)]
                    OutStrDoc.append(CommandStrTemplate %( AffectedParam, SimulationPhase, OccurrenceProbability, AppliedFormula, repr(Notes) ) + "\n")
                    OutStrDoc.append(ExceptClause + "\n")
        if OutStrDoc == []:
            raise ValueError, "Invalid Document File detected - No Simulation Rules were detected"
            
    #### Handle model code file
    print "$"*70
    print "Processing the Model Code File: " + FileNameModelCode
    # Detect the first lines
    PopulationStartLocation = None
    PopulationEndLocation = None
    ProjectStartLocation = None
    ProjectEndLocation = None
    NumberOfProjectsDetected = 0
    for (CodeEnum, CodeLine) in enumerate(ReadLinesModel):
        if CodeLine.startswith("try: DB.PopulationSets.AddNew("):
            # Record the first line encountered
            if PopulationStartLocation == None:
                PopulationStartLocation = CodeEnum
                print "Detected population code start at line #" + str(PopulationStartLocation+1)
            # Record the Last line encountered + 1 for the except clause
            PopulationEndLocation = CodeEnum + 1
        if CodeLine.startswith("try: SimRuleList = SimRuleList + [ DB.SimulationRule("):
            # Record only records from the project that will be changed according
            # to the user specification. Note that currently, only the rules for
            # a single project will be changed - the project that was declared at
            # the input.
            if ProjectNumberToUpdateWithRules == NumberOfProjectsDetected:
                # Record the first line encountered
                if ProjectStartLocation == None:
                    ProjectStartLocation = CodeEnum
                    print "Detected Project Rules code start at line #" + str(ProjectStartLocation+1)
                # Record the Last line encountered + 1 for the except clause
                ProjectEndLocation = CodeEnum + 1
        if CodeLine.startswith("try: DB.Projects.AddNew("):
            # Increase the project count
            NumberOfProjectsDetected = NumberOfProjectsDetected + 1
            print "Detected Project wrap-up at line #" + str(CodeEnum+1)
    # Now do some assertion checks to make sure the detections are reasonable
    if PopulationStartLocation == None:
        raise ValueError, "No Population was detected in the generated code file. Make sure the file name is correct and that the file was properly generated and not modified by hand."
    elif not ReadLinesModel[PopulationEndLocation].startswith(ExceptClause):
        raise ValueError, "Population End was not detected well. Make use the generated code file was properly generated and not modified by hand. The problem was located in line #" + str(PopulationEndLocation+1)
    elif not (ReadLinesModel[PopulationStartLocation-1].startswith(ExceptClause) and ReadLinesModel[PopulationStartLocation-2].startswith(("try: DB.Transitions.AddNew(","try: DB.StudyModels.AddNew(","try: DB.Params.AddNew(","try: DB.States.AddNew("))):
        raise ValueError, "Population Start was detected following statements that violate the proper code order of states, parameters, Model, Transitions. Make use the generated code file was properly generated and not modified by hand. The problem was located before line #" + str(PopulationStartLocation+1)
    if ProjectNumberToUpdateWithRules<0 or ProjectNumberToUpdateWithRules>=NumberOfProjectsDetected:
        raise ValueError, "The number of Projects in the file is does not allow modification if the specified project index. Please check the reconstructed model code file and make sure you are working on the correct file and that the file was not manually changed. Also change that you specified the correct number of the project where the first project index is 0. The Index you specified was: " + str(ProjectNumberToUpdateWithRules) + " While there were only " + str(NumberOfProjectsDetected) + " located in the model code file"
    if ProjectStartLocation == None:
        raise ValueError, "No Project was detected in the generated code file. Make sure the file name is correct and that the file was properly generated and not modified by hand."
    elif not ReadLinesModel[ProjectEndLocation].startswith(ExceptClause):
        raise ValueError, "Project End was not detected well. Make use the generated code file was properly generated and not modified by hand. The problem was located in line #" + str(ProjectEndLocation+1)
    elif not ReadLinesModel[ProjectStartLocation-1].startswith("SimRuleList = []"):
        raise ValueError, "Project Start was detected without initializing the rule list. Make use the generated code file was properly generated and not modified by hand. The problem was located before line #" + str(ProjectStartLocation+1)
    # Now actually perform the changes
    NewLines = []
    NewLines = NewLines + ReadLinesModel[:PopulationStartLocation]
    if FileNameSpreadSheet == "":
        NewLines = NewLines + ReadLinesModel[PopulationStartLocation:PopulationEndLocation+1]
    else:
        NewLines = NewLines + OutStrSpreadSheet
    NewLines = NewLines + ReadLinesModel[PopulationEndLocation+1:ProjectStartLocation]
    if FileNameDoc == "":
        NewLines = NewLines + ReadLinesModel[ProjectStartLocation:ProjectEndLocation+1]
    else:
        NewLines = NewLines + OutStrDoc
    NewLines = NewLines + ReadLinesModel[ProjectEndLocation+1:]
    NewText = "".join(NewLines)
    # Backup the old file
    DB.BackupFile(FileNameModelCode)
    # Write the new file
    ExportFileModel = open(FileNameModelCode,"w")
    ExportFileModel.write(NewText)
    ExportFileModel.close()
    # Now actually run this new code file to generate a model zip file
    print "$"*70
    print "Running the Model Code File: " + FileNameModelCode
    # First figure out the path and module name by separating path components
    (ScriptPathOnly, ScriptFileNameOnly, ScriptFileNameFullPath) = DB.DetermineFileNameAndPath(FileNameModelCode)
    (ScriptFileNameNoExtension , ScriptFileNameOnlyExtension ) = os.path.splitext(ScriptFileNameOnly)
    # Make sure the module is in the system path. First save the current
    # system path and then change it
    OldSysPath = sys.path
    # Insert the new path at the beginning of the search list so that
    # the correct file will be run in case of duplicate filenames in
    # different directories.
    sys.path.insert(0,ScriptPathOnly)
    # Now try running the generation - enclose this in a try catch clause
    try:
        # Run the Generation
        __import__(ScriptFileNameNoExtension)
        # remove the module from sys.modules to force reload later on
        del(sys.modules[ScriptFileNameNoExtension])
    except:
        (ExceptType, ExceptValue, ExceptTraceback) = sys.exc_info()
        if ScriptFileNameNoExtension in sys.modules:
            del(sys.modules[ScriptFileNameNoExtension])
        ErrorText = 'Model Regeneration Error: An error was encountered while running the model generation script file ' + ScriptFileNameFullPath + ' . Here are details about the error: ' + str(ExceptValue)
        raise ValueError, ErrorText
    # Reconstruct the system path
    sys.path = OldSysPath
    # Finished generating 
    print "OK"*35
    print "Successfully finished running the Model Code File: " + FileNameModelCode
    # Calculate the file name and replace double backslash characters with a single
    # backslash to avoid the escape sequence
    FileName = ReadLinesModel[-1].split("'")[1].replace("\\\\","\\")
    print "You can now access the following updated model file using MIST:"
    print FileName
    print "OK"*35
    return

if __name__ == "__main__":
    # Redirect stdout to File if needed
    (sys.stdout, BackupOfOriginal) = DB.RedirectOutputToValidFile(sys.stdout)
    if len(sys.argv) > 1:
        FileNameSpreadSheetStr = sys.argv[1]
        FileNameDocStr = sys.argv[2]
        FileNameModelCodeStr = sys.argv[3]
        if len(sys.argv) > 4:
            ProjectNumberToUpdateWithRules = int(sys.argv[4])
        else:
            ProjectNumberToUpdateWithRules = 0
    else:
        print 'Info: this script can be invoked from command line using the following syntax:'
        print ' CodeFromDocAndSpreadsheet.py FileCSV FileTXT FileModel [ProjectNumber]'
        print ' where:'
        print '  FileCSV - .csv spreadsheet file name with population distributions'
        print '  FileTXT - text file name with rules from a word document'
        print '  FileModel - .zip or .py containing the model to be updated'
        print '  ProjectNumber - project number to be updated - default is 0'
        print ' Note that FileCSV and FileTXT can be "" indicating no change'
        print ' The new data will replace existing populations and project rules'
        print ' A new FileModel zip file will be created with the usual backup'
        # Ask about the simulation result of interest
        FileNameSpreadSheetStr = raw_input( 'Please input .csv spreadsheet file name with population distributions: ' )
        FileNameDocStr = raw_input( 'Please input text file name with rules from a word document: ' )
        FileNameModelCodeStr = raw_input( 'Please input .zip or .py containing the model to be updated: ' )
        ProjectNumberToUpdateWithRulesStr = raw_input( 'Please input project number to be updated - or press enter for default: ' )
        if ProjectNumberToUpdateWithRulesStr.strip() != '':
            ProjectNumberToUpdateWithRules = int(ProjectNumberToUpdateWithRulesStr)
        else:
            ProjectNumberToUpdateWithRules = 0
    # Trip file names for possible " encapsulation and for spaces
    FileNameSpreadSheet = FileNameSpreadSheetStr.strip().strip('"')
    FileNameDoc = FileNameDocStr.strip().strip('"')
    FileNameModelCodeCandidate = FileNameModelCodeStr.strip().strip('"')
    # Check if the input is a py file or a zip file
    if FileNameModelCodeCandidate.lower().endswith('.zip'):
        # if a zip file, then convert to a py file
        FileNameModelCode = FileNameModelCodeCandidate[:-4]+'.py'
        DB.ReconstructDataFileAndCheckCompatibility(FileNameModelCodeCandidate, JustCheckCompatibility = False, RegenerationScriptName = FileNameModelCode, ConvertResults = False, KnownNumberOfErrors = 0, CatchError = False, OutputModelFileName = FileNameModelCodeCandidate)
    else:
        # if already a python file, just use it
        FileNameModelCode = FileNameModelCodeCandidate
    CodeConvertDocAndSpreadSheet(FileNameSpreadSheet, FileNameDoc, FileNameModelCode, ProjectNumberToUpdateWithRules)
    # Redirect stdout back if needed
    sys.stdout = DB.RedirectOutputBackwards(sys.stdout, BackupOfOriginal)
