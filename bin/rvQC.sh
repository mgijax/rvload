#!/bin/sh
#
#  rvQC.sh
###########################################################################
#
#  Purpose:
#
#      This script is a wrapper around the process that does sanity
#      checks for the RV vocabulary load
#
#  Usage:
#
#      rvQC.sh  filename  
#
#      where
#          filename = full path to the input file
#
#  Env Vars:
#
#      See the configuration file
#
#  Inputs:
#	RV obo file
#
#  Outputs:
#
#      - sanity report for the input file.
#
#      - Log file (${QC_LOGFILE})
#
#  Exit Codes:
#
#      0:  Successful completion
#      1:  Fatal initialization error occurred
#      2:  Invalid obo version
#      3:  Fatal sanity errors
#
#  Assumes:  Nothing
#
#  Implementation:
#
#      This script will perform following steps:
#
#      ) Validate the arguments to the script.
#      ) Validate & source the configuration files to establish the environment.
#      ) Verify that the input file exists.
#      ) Initialize the log and report files.
#      ) Call rvQC.py to generate the sanity/QC report.
#
#  Notes:  None
#
###########################################################################
#
#  Modification History:
#
#  Date        SE   Change Description
#  ----------  ---  -------------------------------------------------------
#
#  05/12/2014 - sc Finalize 
#
#  03/7/2014  sc  Initial development
#
###########################################################################
CURRENTDIR=`pwd`
BINDIR=`dirname $0`

CONFIG=`cd ${BINDIR}/..; pwd`/rvload.config
USAGE='Usage: rvQC.sh  filename'

# this is a sanity check only run, set LIVE_RUN accordingly
LIVE_RUN=0; export LIVE_RUN

#
# Make sure an input file was passed to the script. If the optional "live"
# argument is given, that means that the output files are located in the
# /data/loads/... directory, not in the current directory.
#
if [ $# -eq 1 ]
then
    INPUT_FILE=$1
elif [ $# -eq 2 -a "$2" = "live" ]
then
    INPUT_FILE=$1
    LIVE_RUN=1
else
    echo ${USAGE}; exit 1
fi

#
# Make sure the configuration file exists and source it.
#
if [ -f ${CONFIG} ]
then
    . ${CONFIG}
else
    echo "Missing configuration file: ${CONFIG}"
    exit 1
fi

#
# If this is not a "live" run, the output, log and report files should reside
# in the current directory, so override the default settings.
#
if [ ${LIVE_RUN} -eq 0 ]
then
	SANITY_RPT=${CURRENTDIR}/`basename ${SANITY_RPT}`
	QC_LOGFILE=${CURRENTDIR}/`basename ${QC_LOGFILE}`

fi
#
# Make sure the input file exists (regular file or symbolic link).
#
if [ "`ls -L ${INPUT_FILE} 2>/dev/null`" = "" ]
then
    echo "Missing input file: ${INPUT_FILE}"
    exit 1
fi

#
# Initialize the log file.
#
LOG=${QC_LOGFILE}
rm -rf ${LOG}
touch ${LOG}

#
# Convert the input file into a QC-ready version that can be used to run
# the sanity/QC reports against.
#
dos2unix ${INPUT_FILE} ${INPUT_FILE} 2>/dev/null

#
# Initialize the report files to make sure the current user can write to them.
#
rm -f ${SANITY_RPT}; >${SANITY_RPT}

#
# Run sanity checks on RV obo file
#
echo "" >> ${LOG}
date >> ${LOG}
echo "Run sanity checks on the input file" >> ${LOG}

# run the sanity checks on the RV obo file 
${PYTHON} ${RVLOAD_QC}  ${INPUT_FILE}
STAT=$?
if [ ${STAT} -eq 1 ]
then
    echo "Fatal initialization error. See ${SANITY_RPT}" | tee -a ${LOG}
    echo "" | tee -a ${LOG}
    exit ${STAT}
fi

if [ ${STAT} -eq 2 ]
then
    echo ""
    echo "Invalid OBO format $1"
    echo "Version ${OBO_FILE_VERSION} expected"
    echo ""
    exit ${STAT}
fi

if [ ${STAT} -eq 3 ]
then
    echo "Fatal sanity errors detected. See ${SANITY_RPT}" | tee -a ${LOG}
    echo "" | tee -a ${LOG}
else
    echo "No fatal errors detected."
fi

echo "" >> ${LOG}
date >> ${LOG}
echo "Finished running sanity checks on the input file" >> ${LOG}

exit 0
