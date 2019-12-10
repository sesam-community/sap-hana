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
    tablename = tablename.replace('|','/')

    query = "SELECT * FROM " + schemaname + "." + tablename
    logger.info(query)

    try:
        conn = dbapi.connect(
            address=HANA_IP,
            port=HANA_PORT,
            user=HANA_USER,
            password=HANA_PASS
        )
        logger.info("Connected to Hana")
    except:
        logger.info("Couldn't connect to Hana")
        return Response(status=403)

    def emit_rows(connection,querystring):
        logger.info("Running query {}".format(querystring))

        yield "["

        ### rest of your code here ###
        cursor = connection.cursor()
        cursor.execute(querystring)
    
        column_names = []

        #get property names. cursor.description is tuples with the names and column parameters, we just need column name
        for i in range(len(cursor.description)):
          desc = cursor.description[i]
          column_names.append("{}".format(desc[0]))

        is_first = True

        for result in cursor:
            if (is_first):
                is_first = False
            else:
                yield ","
            
            entity = {}
            
            for i in range(len(result)):
                entity[column_names[i]]="{}".format(result[i])
            yield json.dumps(entity)

        cursor.close()
        yield "]"

    try:
        return Response(emit_rows(conn,query),status=200, mimetype='application/json')
    except dbapi.Error as exc:
        logger.error("Error from Hana: %s", exc)
        return Response(status=500)

@app.route('/put_rows/<schemaname>/<tablename>', methods=['POST'])
def put_rows(schemaname,tablename):
    tablename = tablename.replace('|','/')
    try:
        conn = dbapi.connect(
            address=HANA_IP,
            port=HANA_PORT,
            user=HANA_USER,
            password=HANA_PASS
        )
        logger.info("Connected to Hana")
    except:
        logger.info("Couldn't connect to Hana")
        return Response(status=403)

    # get table keys from database for deletes
    keys_query = "SELECT COLUMN_NAME FROM CONSTRAINTS WHERE SCHEMA_NAME = upper('" + schemaname + "') AND TABLE_NAME = upper('" + tablename + "') AND IS_PRIMARY_KEY = 'TRUE' ORDER BY POSITION ASC;"
    cursor_keys = conn.cursor()
    cursor_keys.execute(keys_query)
    table_keys = []
    for table_key in cursor_keys:
        table_keys.append(table_key[0])
    cursor_keys.close()
    
    logger.info("Detected primary keys from hana table: " + "{}".format(table_keys))

    # get entities from request
    entities = request.get_json()
    #print("{}".format(entities))
    if(len(entities)==0):
        return Response(status=200)
    # get column names from sesam data set
    # need a text version for the query string, and a list for the row iterator
    columns = []
    columns_text = '('
    for key,val in entities[0].items():
        if(key[0]!='_'):
            columns_text = columns_text + key + ','
            columns.append(key)
    columns_text = columns_text[:-1] + ')'

    row_data = ()
    deleted_ids = {}
    for entity in entities:
        # add to data to insert if not a delete
        if(entity['_deleted']==False):
            row_temp = ()
            for column in columns:
                row_temp = row_temp + (entity[column],)
            row_data = row_data + (row_temp,)
        # stores the last known state of the _deleted property - so we can delete after upserts are completed.
        temp_delete_dict = {}
        temp_delete_dict['_deleted'] = entity['_deleted']
        for del_key in table_keys:
            temp_delete_dict[del_key] = entity[del_key]
        deleted_ids[entity['_id']] = temp_delete_dict

#    print(row_data)
#    for row in row_data:
#        for i in row:
#            print("{}".format(type(i)) + " " + i)

    delete_data = ()
    for deleted in deleted_ids:
        delete_temp = ()
        if(deleted_ids[deleted]['_deleted']==True):
            for key in table_keys:
                delete_temp = delete_temp + (deleted_ids[deleted][key],)
            delete_data = delete_data + (delete_temp,)

    try:
        # Set up a parameterized SQL 
        if(len(row_data)!=0):
            parms = ("?," * len(row_data[0]))[:-1]
            query = "UPSERT " + schemaname + "." + tablename + " " + columns_text + " VALUES (%s) WITH PRIMARY KEY;" % (parms)
    
            ## upsert rows into hana
            logger.info("Running " + "{}".format(len(row_data)) + " upserts: " + query)
            cursor = conn.cursor()
            cursor.executemany(query, row_data)
            cursor.close()
        else:
            logger.info("No new rows")
    except dbapi.Error as exc:
        logger.error("Error from Hana: %s", exc)
        return Response(status=500)

    try:
        # Set up parameterized SQL DELETE keys in WHERE conditional
        if(len(delete_data)!=0):
            key_conditional = ''
            isFirst = True
            for key_col in table_keys:
                if(isFirst):
                    isFirst = False
                else:
                    key_conditional = key_conditional + "AND "
                key_conditional = key_conditional + key_col + " = ? "
        
            delete_query = "DELETE FROM " + schemaname + "." + tablename + " WHERE " + key_conditional

            ## upsert rows into hana
            logger.info("Running " + "{}".format(len(delete_data)) + " deletes: " + delete_query)
            cursor_del = conn.cursor()
            cursor_del.executemany(delete_query, delete_data)
            cursor_del.close()
        else:
            logger.info("No new deletes")

        return Response(status=200)

    except dbapi.Error as exc:
        logger.error("Error from Hana: %s", exc)
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


