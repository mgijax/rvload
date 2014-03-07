#!/usr/local/bin/python
#
#  rvQC.py
###########################################################################
#
#  Purpose:
#
#	This script will generate a sanity/QC report for a feature relationship
#	    obo file
#
#  Usage:
#
#      rvQC.py  filename
#
#      where:
#          filename = path to the input file
#
#  Env Vars:
#
#      The following environment variables are set by the configuration
#      files that are sourced by the wrapper script:
#
#          MGI_PUBLICUSER
#          MGI_PUBPASSWORDFILE
#          INVALID_TERMID_RPT
#	   
#      The following environment variable is set by the wrapper script:
#
#          LIVE_RUN
#
#  Inputs:
# 	obo file
#
#  Outputs:
#
#      - QC report (${INVALID_TERMID_RPT})
#
#  Exit Codes:
#
#      0:  Successful completion
#      1:  An exception occurred
#      2:  Non-fatal discrepancy errors detected in the input files
#      3:  Fatal discrepancy errors detected in the input files
#
#  Assumes:
#
#  Implementation:
#
#      This script will perform following steps:
#
#      1) Validate the arguments to the script.
#      2) Perform initialization steps.
#      3) Open the input/output files.
#      4) Generate the QC reports.
#
#  Notes:  None
#
###########################################################################

import sys
import os
import string
import re
import mgi_utils
import db

#
#  CONSTANTS
#
TAB = '\t'
CRT = '\n'

USAGE = 'Usage: rvQC.py  inputFile'

#
#  GLOBALS
#

# Report file names
sanityRptFile = os.environ['SANITY_RPT']

# expected obo file version
expectedVersion = os.environ['OBO_FILE_VERSION']

# list of invalid ids found in input
invalidIDList = []

# list of ids with invalid set of synonyms
invalidSynList = []

timestamp = mgi_utils.date()

# dict representing all anatomical structure stanzas in the obo file
# Looks like
#   {integerKey: {field1Name:field1Value, ... fieldnName:fieldnValue}, ...}
allStanzasDict = {}

# 1 if we have found the string 'format-version'
foundVersion = 0

# 1 if sanity errors
hasSanityErrors = 0

#
# Purpose: Validate the arguments to the script.
# Returns: Nothing
# Assumes: Nothing
# Effects: sets global variable
# Throws: Nothing
#
def checkArgs ():
    global inputFile

    if len(sys.argv) != 2:
        print USAGE
        sys.exit(1)

    inputFile = sys.argv[1]

    return


#
# Purpose: Perform initialization steps.
# Returns: Nothing
# Assumes: Nothing
# Effects: Sets global variables.
# Throws: Nothing
#
def init ():
    openFiles()
    return


#
# Purpose: Open the files.
# Returns: Nothing
# Assumes: Nothing
# Effects: Sets global variables.
# Throws: Nothing
#
def openFiles ():
    global fpObo, fpSanityRpt

    #
    # Open the input file.
    #
    try:
        fpObo = open(inputFile, 'r')
    except:
        print 'Cannot open input file: %s' % inputFile
        sys.exit(1)

    try:
        fpSanityRpt = open(sanityRptFile, 'w')
    except:
        print 'Cannot open report file: %s' % sanityRptFile
        sys.exit(1)

    return
#
# Purpose: run the sanity checks
# Returns: Nothing
# Assumes: Nothing
# Effects: Nothing
# Throws: Nothing
#
def runSanityChecks ():

    global allStanzasDict, foundVersion, hasSanityErrors

    # incremental key to our dictionary of stanzas, the global allStanzasDict
    # we use an incremental key rather than, say the EMAPA id, as the id could
    # be misssing
    keyCtr = 1

    # flag indicating we have found the first stanza i.e. we are beyond the
    # header
    foundStanza = 0

    # flag indicating we are within a stanza
    inStanza = 0

    # represents data from the current stanza we are parsing
    currentStanzaDict = {}
    
    #
    # parse the obo file into a data structure
    #
    for line in fpObo.readlines():
	# we use this to find lines with tabs
        lineNoCRT = string.strip(line, CRT)
	
	# we use this to evaluate the stanza attributes
        lineStripped = string.strip(line)

	if string.find(lineStripped, 'format-version') != -1:
            foundVersion = 1
            lineList = string.split(lineStripped, ':')
            version = string.strip(lineList[1])

            # exit if the version is not the one we expect
            if version != expectedVersion:
                closeFiles()
                sys.exit(2)
	if lineStripped == '[Term]':
            foundStanza = 1
            inStanza = 1
            continue
        if lineStripped == '':
            inStanza = 0
        if foundStanza == 1:
            # if we're within a stanza store the field name and its value
            # in the currentStanzaDict
            if inStanza == 1:
                i = string.find(lineStripped, ':')
                tabIndex = string.find(lineNoCRT, TAB)
                if tabIndex > -1:
                    if not currentStanzaDict.has_key('tab'):
                        currentStanzaDict['tab'] = []
                    currentStanzaDict['tab'].append(lineNoCRT)
                fieldName = lineStripped[0:i]
                value = lineStripped[i+1:].strip()
                if fieldName not in currentStanzaDict.keys():
                    currentStanzaDict[fieldName] = []
                currentStanzaDict[fieldName].append(value)
            else: # add the current stanza to the dict of all obo stanzas
                allStanzasDict[keyCtr] = currentStanzaDict
                currentStanzaDict = {}
                keyCtr += 1

    for s in allStanzasDict.keys():
	currentStanzaDict = allStanzasDict[s]
	hasForward = 0
	hasReverse = 0
	# check ID format
	hasId = currentStanzaDict.has_key('id')
	if not hasId:
	    invalidIDs.append('stanza without id')
	else:
	    id = currentStanzaDict['id'][0]
	    #print id
	    if id.find(':') != 2:
		invalidIDList.append(i)
	    else:
		prefix, suffix = string.split(id, ':')
		if prefix != 'RV' or len(suffix) != 7:
		    invalidIDList.append(i)

	# check synonymTypes
	if id == 'RV:0000000':
	    continue
	hasSyn = currentStanzaDict.has_key('synonym')
	if not hasSyn:
	    invalidSynList.append('stanza without synonyms')
	else:
	    synList = currentStanzaDict['synonym']
	    for s in synList:
		# RELATED
		syn = re.split (' ', re.split ('"', s)[2].lstrip())[0]
		# RELATED FORWARD
		syn = syn + ' ' + re.split (' ', re.split ('"', s)[2].lstrip())[1]
	 	if syn == 'RELATED FORWARD':
		    #print 'hasForward'
		    hasForward = 1
		elif syn == "RELATED REVERSE":
		    #print 'hasReverse'
		    hasReverse = 1
	    if not (hasForward and hasReverse):
		#print 'missing forward or reverse %s' % id
		invalidSynList.append(id)
    if len(invalidIDList) > 0:
	hasSanityErrors = 1
	fpSanityRpt.write('Incorrectly formatted RV IDs %s%s'  % \
	    (CRT, CRT))
	fpSanityRpt.write(string.join(invalidIDList, CRT))
	fpSanityRpt.write('%s%s' % ( CRT, CRT))
    if len(invalidSynList) > 0:
	hasSanityErrors = 1
	fpSanityRpt.write('Stanzas with missing or invalid synonym types %s%s'  % \
	    (CRT, CRT))
	#print 'invalidSynList %s' % invalidSynList
	fpSanityRpt.write(string.join(invalidSynList, CRT))
	fpSanityRpt.write('%s%s' % ( CRT, CRT))
	
#
# Purpose: Close the files.
# Returns: Nothing
# Assumes: Nothing
# Effects: Nothing
# Throws: Nothing
#
def closeFiles ():
    global fpObo, fpSanityRpt
    fpObo.close()
    fpSanityRpt.close()
    return

#
# Main
#
checkArgs()
init()
runSanityChecks()
closeFiles()

if hasSanityErrors == 1 : 
    sys.exit(3)
#elif nonfatalCount > 0:
#    sys.exit(2)
else:
    sys.exit(0)