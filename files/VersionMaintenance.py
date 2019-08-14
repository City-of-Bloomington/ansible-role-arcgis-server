# -*- coding: utf-8 -*-
import sys, string, os, arcpy, datetime, psycopg2, smtplib, configparser

dir    = os.path.abspath(os.path.dirname(sys.argv[0]))
config = configparser.ConfigParser()
config.read(dir + '/config.ini')

now               = datetime.datetime.now()
current_date      = now.strftime('%Y%m%d')
current_timestamp = now.isoformat(sep=' ', timespec='seconds')
main_log          = open(config['arcgis']['logFile'], 'w')

def sendemail(logFile, config):
    """Email the log file to someone

    :param logFile: Path to the file to send
    :type  logFile: string

    :param config: Email values
    :type  config: dict
    """
    from email.message import EmailMessage

    msg            = EmailMessage()
    msg['Subject'] = 'Version Maintenance'
    msg['From'   ] = config['from']
    msg['To'     ] = config['to'  ]

    with open(logFile) as fp:
        msg.set_content(fp.read())

    # Send the message
    s = smtplib.SMTP(config['server'], 587)
    s.ehlo()
    s.starttls()
    s.send_message(msg)
    s.quit()

main_log.write("Starting script {}\n".format(current_timestamp))



#SDE default version
defaultVersion = "SDE.DEFAULT"
editVersion = "SDE.MasterEdit"

#send the email or not
needsToSendEmail = False

# Get a list of versions to pass into the ReconcileVersions tool
main_log.write("Rec and Post Edit version to Default\n")
versionList = arcpy.ListVersions(config['arcgis']['sdeFile'])

# Process: Reconcile and Post MasterEdit to Default
arcpy.ReconcileVersions_management(config['arcgis']['sdeFile'],
                                   "ALL_VERSIONS",
                                   defaultVersion,
                                   editVersion,
                                   "LOCK_ACQUIRED",
                                   "ABORT_CONFLICTS",
                                   "BY_OBJECT",
                                   "FAVOR_TARGET_VERSION",
                                   "POST",
                                   "KEEP_VERSION")
main_log.write(arcpy.GetMessages() + "\n")


# Process: Compress
main_log.write("Compress DB\n")
arcpy.Compress_management(config['arcgis']['sdeFile'])
main_log.write(arcpy.GetMessages() + "\n")

# Process: Reconcile All Versions
main_log.write("Reconcile all the versions\n")
arcpy.ReconcileVersions_management(config['arcgis']['sdeFile'],
                                   "ALL_VERSIONS",
                                   defaultVersion,
                                   versionList ,
                                   "LOCK_ACQUIRED",
                                   "ABORT_CONFLICTS",
                                   "BY_OBJECT",
                                   "FAVOR_TARGET_VERSION",
                                   "NO_POST",
                                   "KEEP_VERSION")
main_log.write(arcpy.GetMessages() + "\n")
main_log.write("ArcPY POST And Rec Complete\n")

# Analyze and Vacuum postgres
main_log.write("Connecting to the db directly through pg\n")
pgConnection = "host={} dbname={} user={} password={}".format(
    config['postgres']['server'],
    config['postgres']['db'    ],
    config['postgres']['user'  ],
    config['postgres']['pass'  ]
)

conn = psycopg2.connect(pgConnection)
conn.set_session(autocommit=True)
cur  = conn.cursor()

main_log.write("Analyzing DB\n")
cur.execute("ANALYZE;")

main_log.write("Vaccum DB\n")
cur.execute("VACUUM ANALYZE;")

main_log.write("Re index DB\n")
cur.execute("REINDEX DATABASE " + config['postgres']['db'] + ";")

conn.close()

current_timestamp = datetime.datetime.now().isoformat(sep=' ', timespec='seconds')
main_log.write("Complete " + current_timestamp + "\n")
main_log.close()

if config['smtp']['enabled']:
    sendemail(config['arcgis']['logFile'], config['smtp'])
