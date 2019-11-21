from flask import Flask, request, Response
import os
import cherrypy
import json
import logging
import paste.translogger
#import requests
from hdbcli import dbapi

app = Flask(__name__)

logger = logging.getLogger("sap-hana-service")

# settings dependent on environment variables
HANA_IP = os.environ.get("HANA_IP", "")
HANA_USER = os.environ.get("HANA_USER", "")
HANA_PASS = os.environ.get("HANA_PASS", "")
HANA_PORT = os.environ.get("HANA_PORT", "39015")

@app.route('/', methods=['GET'])
def root():
    return Response(status=200, response="Working.")

@app.route('/get_rows/<schemaname>/<tablename>', methods=['GET'])
def get_rows(schemaname,tablename):
    #Initialize your connection
    querylimit=0
    since=0
    query=""

    try:
        conn = dbapi.connect(
            address=HANA_IP,
            port=HANA_PORT,
            user=HANA_USER,
            password=HANA_PASS
        )
        logger.info("Connected to Hana, running query {}".format(query))
    except:
        return Response(status=403)

    try:
        querylimit=int(request.args.get('limit',''))
        since=int(request.args.get('since',''))

        logger.info("Get me {}".format(querylimit)+" rows since {}".format(since))

        if querylimit>0:
            if since>0:
                query = "SELECT * FROM " + schemaname + "." + tablename + " limit " + "{}".format(querylimit) + " offset " + "{}".format(since)
            else:
                query = "SELECT * FROM " + schemaname + "." + tablename + " limit " + "{}".format(querylimit)
        else:
            query = "SELECT * FROM " + schemaname + "." + tablename


        logger.info(query)

        ### rest of your code here ###
        cursor = conn.cursor()
        cursor.execute(query)

        table_rows = []
        column_names = []
        
        #cursor.description is tuples with the names and column parameters, we just need column name
        for i in range(len(cursor.description)):
          desc = cursor.description[i]
          column_names.append("{}".format(desc[0]))

        for result in cursor:
            entity = {}
            for i in range(len(result)):
                entity[column_names[i]]="{}".format(result[i])
            table_rows.append(entity)
        cursor.close()
        return Response(status=200, response=json.dumps(table_rows))
    except:
        return Response(status=500)


if __name__ == '__main__':
    format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    # Log to stdout, change to or add a (Rotating)FileHandler to log to a file
    stdout_handler = logging.StreamHandler()
    stdout_handler.setFormatter(logging.Formatter(format_string))
    logger.addHandler(stdout_handler)

    # Comment these two lines if you don't want access request logging
    app.wsgi_app = paste.translogger.TransLogger(app.wsgi_app, logger_name=logger.name,
                                                 setup_console_handler=False)
    app.logger.addHandler(stdout_handler)

    logger.propagate = False
    logger.setLevel(logging.INFO)

    cherrypy.tree.graft(app, '/')

    # Set the configuration of the web server to production mode
    cherrypy.config.update({
        'environment': 'production',
        'engine.autoreload_on': False,
        'log.screen': True,
        'server.socket_port': 5001,
        'server.socket_host': '0.0.0.0'
    })

    # Start the CherryPy WSGI web server
    cherrypy.engine.start()
    cherrypy.engine.block()


