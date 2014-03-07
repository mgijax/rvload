#!/bin/sh
#
#  rvQC.sh
###########################################################################
#
#  Purpose:
#
#      This script is a wrapper around the process that does sanity
#      checks for the EMAPA/EMAPS load
#
#  Usage:
#
#      rvQC.sh  filename  
#
#      where
#          filename = path to the input file
#
#  Env Vars:
#
#      See the configuration file
#
#  Inputs:
#	EMAPA obo file
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
#      1:  Fatal error occurred
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
#      ) Call rvQC.sh to generate the sanity/QC report.
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
#  03/7/2014  sc  Initial development
#
###########################################################################
CURRENTDIR=`pwd`
BINDIR=`dirname $0`

CONFIG=`cd ${BINDIR}/..; pwd`/rvload.config
USAGE='Usage: rvQC.sh  filename'

# this is a sanity check only run, set LIVE_RUN accordingly
#LIVE_RUN=0; export LIVE_RUN

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
# Make sure the input file exists (regular file or symbolic link).
#
if [ "`ls -L ${INPUT_FILE} 2>/dev/null`" = "" ]
then
    echo "Missing input file: ${INPUT_FILE}"
    exit 1
fi

QC_LOGFILE=${CURRENTDIR}/`basename ${QC_LOGFILE}`
SANITY_RPT=${CURRENTDIR}/`basename ${SANITY_RPT}`

#
# Initialize the log file.
#
LOG=${QC_LOGFILE}
rm -rf ${LOG}
touch ${LOG}

#
# Initialize the report files to make sure the current user can write to them.
#
rm -f ${QC_RPT}; >${QC_RPT}

#
# Run sanity checks on EMAPA obo file
#
echo "" >> ${LOG}
date >> ${LOG}
echo "Run sanity checks on the input file" >> ${LOG}

# run the sanity checks on the RV obo file 
${RVLOAD_QC}  ${INPUT_FILE}
STAT=$?
if [ ${STAT} -eq 1 ]
then
    echo "Fatal initialization error. See ${QC_RPT}\n" | tee -a ${LOG}
    exit ${STAT}
fi

if [ ${STAT} -eq 2 ]
then
    echo "\nInvalid OBO format $1"
    echo "Version ${OBO_FILE_VERSION} expected\n"
    exit ${STAT}
fi

if [ ${STAT} -eq 3 ]
then
    echo "Fatal sanity errors detected. See ${SANITY_RPT}\n" | tee -a ${LOG}
else
    echo "No fatal sanity errors detected."
fi

echo "" >> ${LOG}
date >> ${LOG}
echo "Finished running sanity checks on the input file" >> ${LOG}

exit 0
