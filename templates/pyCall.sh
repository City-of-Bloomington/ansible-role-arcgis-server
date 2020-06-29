#!/bin/bash
#modify this to the location of the arcgis server home directly
export ARCGISHOME=/srv/arcgis/server

source activate
#assumes the py script is in the same directory as the shell script
python VersionMaintenance.py
source deactivate

#notes
#####################
#Install conda
##install arcpy for server
#Conda install -c arcgis-server-10.6-py3
##install the Postgres connection stuff
#Pip install psycopg2-binary
#
#to call the py script outside the sh do the following
##set the arcgishome directory
#export ARCGISHOME=/srv/arcgis/server
#
##call this before starting the python with arcpy..
#Source activate
#
#Then call the python file directly by executing: python /path to py script/VersionMaintenance.py
#
#Finally call the following to deactivate python
#source deactivate



#to execute from bash
#
#copy shell script to execution location
#make the shell script executable chmod u+x pyCall.sh
#Then execute the script from the terminal


#####################
#end notes
