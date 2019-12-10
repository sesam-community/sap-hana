# Introduction 
This package integrates SAP Hana with Sesam and implements the Sesam protocol for reading tables from SAP Hana

# Getting Started
This guide presumes knowledge about Databases, SQL and queries


Example microservice config:
---------------------------
```
{
  "_id": "sap-hana-service",
  "connect_timeout": 60,
  "docker": {
    "environment": {
      "HANA_IP": "10.1.2.3",
      "HANA_PORT": "39015",
      "HANA_USER": "<username>",
      "HANA_PASS": "$SECRET(hana_psas)",
      "LOG_LEVEL": "DEBUG"
    },
    "image": "sesamcommunity/sap-hana:0.1.0",
    "memory": 128,
    "port": 5001
  },
  "read_timeout": 7200,
  "type": "system:microservice",
  "use_https": false,
  "verify_ssl": true
}
```
Example get_rows pipe config:
--------------------
```
{
  "_id": "hana-pipe",
  "type": "pipe",
  "source": {
    "type": "json",
    "system": "sap-hana-service",
    "url": "/get_rows/<schema>/<table>"
  },
  "transform": {
    "type": "dtl",
    "rules": {
      "default": [
        ["add", "_id", "_S.<primary_key>"],
        ["copy", "*"]
      ]
    }
  }
}

```
Example get_rows pipe config:
--------------------
```
{
  "_id": "hana-write",
  "type": "pipe",
  "source": {
    "type": "dataset",
    "dataset": "sesam-test-hana"
  },
  "sink": {
    "type": "json",
    "system": "sap-hana-service",
    "batch_size": 1000,
    "url": "/put_rows/<schema>/<table>"
  },
  "batch_size": 1000
}

```

# Extra info
Note that SAP Hana tables can have the '/' character which breaks the URL endpoint path for the table segment. This MS handles this by converting the '|' to '/' character, so simply replace the '/'s in the pipe url string with '|'s.

The put_rows function requires the pipe to produce the properties exactly as the table expects. This is usually case sensitive and the default is upper case. The service does upserts and expects the primary key(s) to be correct. This is also requried for the deletes to work correctly.