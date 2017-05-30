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
#          SANITY_RPT
#	   OBO_FILE_VERSION
#	   
#  Inputs:
# 	obo file
#
#  Outputs:
#
#      - QC report (${SANITY_RPT})
#
#  Exit Codes:
#
#      0:  Successful completion
#      1:  Fatal initialization error occurred
#      2:  If the OBO version is not the one we expect
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
#      3) Run the sanity checks.
#      4) close input/output files.
#
#  Notes:  None
#
###########################################################################

import sys
import os
import string
import re
import mgi_utils

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
# Effects: opens files
# Throws: Nothing
#
def init ():
    openFiles()
    return


#
# Purpose: Open input and output files.
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
# Effects: sets global variables, write report to file system
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
		#print 'fieldame: %s' % fieldName
                value = lineStripped[i+1:].strip()
		#print 'value: %s' % value
                if fieldName not in currentStanzaDict.keys():
                    currentStanzaDict[fieldName] = []
		#print 'adding value: %s to fieldName: %s' % (value, fieldName)
                currentStanzaDict[fieldName].append(value)
            else: # add the current stanza to the dict of all obo stanzas
                allStanzasDict[keyCtr] = currentStanzaDict
                currentStanzaDict = {}
                keyCtr += 1

    for s in allStanzasDict.keys():
	currentStanzaDict = allStanzasDict[s]
	hasOrganizer = 0
	hasParticipant = 0
	hasSynValue = 1
	# check ID format
	hasId = currentStanzaDict.has_key('id')
	if not hasId:
	    invalidIDList.append('stanza without id. Stanza # %s  stanza: %s' % (s, currentStanzaDict))
	    continue
	id = currentStanzaDict['id'][0]
	#print id
	if id.find(':') != 2:
	    invalidIDList.append('%s - stanza with invalid primary ID' % id)
	    continue
	prefix, suffix = string.split(id, ':')
	if prefix != 'RV' or len(suffix) != 7  :
	    invalidIDList.append('%s - stanza with invalid primary ID' % id)
	else:
	    try:
		x = int(suffix)
	    except:
		invalidIDList.append('%s - stanza with invalid primary ID' % id)
	hasAltId = currentStanzaDict.has_key('alt_id')
	#print 'hasAltId: %s' % hasAltId
	if hasAltId:
	    altIdList = currentStanzaDict['alt_id']
	    #print 'altIdList: %s' % altIdList
	    # check each alt id for correct format
	    for id in altIdList:
		# factor this out with above - later
		#print 'id: %s' % id
		if id.find(':') != 2:
		    invalidIDList.append('%s - stanza with invalid alt ID' % id)
		    continue
		prefix, suffix = string.split(id, ':')
		#print 'prefix: %s suffix: %s' % (prefix, suffix)
                if prefix != 'RV' or len(suffix) != 7  :
                    invalidIDList.append('%s - stanza with invalid alt ID' % id)
                else:
                    try:
                        x = int(suffix)
                    except:
			#print 'adding %s to invalidIDList' %  id
                        invalidIDList.append('%s - stanza with invalid alt ID' % id)

	# if root id don't check for synonyms (there aren't any)
	if id == 'RV:0000000':
	    continue
	# check synonymTypes
	hasSyn = currentStanzaDict.has_key('synonym')
	if not hasSyn:
	    invalidSynList.append('%s - stanza w/o synonyms' % id)
	    continue
	synList = currentStanzaDict['synonym']
	# list of synonym values to make sure all uniq
	frSynList = []
	for s in synList:
	    #print s
	    # check for missing syn value
	    tokens = re.split (' ', s)
	    if tokens[0].find('"') == -1:
		hasSynValue = 0
		invalidSynList.append('%s - stanza with missing synonym value "synonym: %s"' % (id, s))
		continue
	    # RELATED
	    type = re.split (' ', re.split ('"', s)[2].lstrip())[0]
	    # RELATED ORGANIZER/PARTICIPANT
	    type = type + ' ' + re.split (' ', re.split ('"', s)[2].lstrip())[1]

	    if type == 'RELATED ORGANIZER':
		if not hasOrganizer:
		    hasOrganizer = 1
		    frSynList.append(re.split ('"', s)[1])
		else:
		    invalidSynList.append('%s - stanza with multi ORGANIZER' % id)
		    continue
	    elif type == "RELATED PARTICIPANT":
		if not hasParticipant:
		    hasParticipant = 1
		    frSynList.append(re.split ('"', s)[1])
		else:
		    invalidSynList.append('%s - stanza with multi PARTICIPANT' % id)
		    continue
	if hasSynValue and not (hasOrganizer and hasParticipant):
	    #print 'missing organizer or participant %s' % id
	    invalidSynList.append('%s - stanza missing ORGANIZER or PARTICIPANT' % id)
	elif hasSynValue and len(set(frSynList)) != 2:
	    invalidSynList.append('%s - ORGANIZER and PARTICIPANT values identical' % id)
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
else:
    sys.exit(0)
