#!/bin/sh 
#
#  rvload.sh
###########################################################################
#
#  Purpose:
# 	This script runs Feature Relationship Vocab (RV) Load
#
  Usage=rvload.sh
#
#  Env Vars:
#
#      See the configuration file rvload.config
#
#  Inputs:
#
#      - Common configuration file -
#               /usr/local/mgi/live/mgiconfig/master.config.sh
#      - configuration file - mcvload.config
#      - input file - see rvload.config 
#
#  Outputs:
#
#      - An archive file
#      - Log files defined by the environment variables ${LOG_PROC},
#        ${LOG_DIAG}, ${LOG_CUR} and ${LOG_VAL}
#      - vocload logs and bcp files  - also see vocload/RV.config
#      - Records written to the database tables
#      - Exceptions written to standard error
#      - Configuration and initialization errors are written to a log file
#        for the shell script
#
#  Exit Codes:
#
#      0:  Successful completion
#      1:  Fatal error occurred
#
#  Assumes:  Nothing
#
#      This script will perform following steps:
#
#      1) Validate the arguments to the script.
#      2) Source the configuration file to establish the environment.
#      3) Verify that the input files exist.
#      4) Initialize the log file.
#      5) Determine if the input file has changed since the last time that
#         the load was run. Do not continue if the input file is not new.
#      6) Call rvQC.sh to generate the sanity/QC reports
#      7) call vocload
#      8) Archive the input file.
#      9) Touch the "lastrun" file to timestamp the last run of the load.
#
# History:
#
# sc	03/03/2014 - TR11560 - Feature Relationship Project
#	-new
#

cd `dirname $0`
LOG=`pwd`/rvload.log
rm -rf ${LOG}

RUNTYPE=live

CONFIG_LOAD=../rvload.config

#
# Verify and source the configuration file
#
if [ ! -r ${CONFIG_LOAD} ]
then
   echo "Cannot read configuration file: ${CONFIG_LOAD}"
    exit 1   
fi

. ${CONFIG_LOAD}

#
# Make sure the input file exists (regular file or symbolic link).
#
if [ "`ls -L ${INPUT_FILE_DEFAULT} 2>/dev/null`" = "" ]
then
    echo "Missing input file: ${INPUT_FILE_DEFAULT}"
    exit 1
fi

#
#  Source the DLA library functions.
#

if [ "${DLAJOBSTREAMFUNC}" != "" ]
then
    if [ -r ${DLAJOBSTREAMFUNC} ]
    then
        . ${DLAJOBSTREAMFUNC}
    else
        echo "Cannot source DLA functions script: ${DLAJOBSTREAMFUNC}" | tee -a ${LOG}
        exit 1
    fi
else
    echo "Environment variable DLAJOBSTREAMFUNC has not been defined." | tee -a ${LOG}
    exit 1
fi

#
# Verify and source the vocload configuration file
#
CONFIG_VOCLOAD=${VOCLOAD}/RV.config

if [ ! -r ${CONFIG_VOCLOAD} ]
then
   echo "Cannot read configuration file: ${CONFIG_VOCLOAD}"
    exit 1
fi

. ${CONFIG_VOCLOAD}

#####################################
#
# Main
#
#####################################

#
# createArchive including OUTPUTDIR, startLog, getConfigEnv
# sets "JOBKEY"
preload ${OUTPUTDIR}

#
# There should be a "lastrun" file in the input directory that was created
# the last time the load was run for this input file. If this file exists
# and is more recent than the input file, the load does not need to be run.
#
LASTRUN_FILE=${INPUTDIR}/lastrun

if [ -f ${LASTRUN_FILE} ]
then
    if test ${LASTRUN_FILE} -nt ${INPUT_FILE_DEFAULT}
    then
        echo "Input file has not been updated - skipping load" | tee -a ${LOG_PROC}
        STAT=0
        checkStatus ${STAT} 'Checking input file'
        shutDown
        exit 0
    fi
fi

#
# Generate the sanity/QC reports
#
echo "" >> ${LOG_DIAG}
date >> ${LOG_DIAG}
echo "Generate the sanity/QC reports" | tee -a ${LOG_DIAG}
${RVLOAD_QC_SH} ${INPUT_FILE_DEFAULT} ${RUNTYPE} 2>&1 >> ${LOG_DIAG}
STAT=$?
checkStatus ${STAT} "QC reports"
if [ ${STAT} -eq 1 ]
then
    shutDown
    exit 1
fi

#
# run vocabulary load
#
echo "Running RV Vocabulary load"  | tee -a ${LOG_DIAG}

${VOCLOAD}/runOBOIncLoad.sh ${CONFIG_VOCLOAD} >> ${LOG_PROC}
STAT=$?
echo "runOBOIncLoad.sh STAT: ${STAT}"
checkStatus ${STAT} "${VOCLOAD}/runOBOIncLoad ${CONFIG_VOCLOAD}"

#
# Archive a copy of the input file, adding a timestamp suffix.
#
echo "" >> ${LOG_DIAG}
date >> ${LOG_DIAG}
echo "Archive input file" | tee -a ${LOG_DIAG}
TIMESTAMP=`date '+%Y%m%d.%H%M'`
ARC_FILE=`basename ${INPUT_FILE_DEFAULT}`.${TIMESTAMP}
cp -p ${INPUT_FILE_DEFAULT} ${ARCHIVEDIR}/${ARC_FILE}

#
# Touch the "lastrun" file to note when the load was run.
#
touch ${LASTRUN_FILE}

#
# run postload cleanup and email logs
#
shutDown


