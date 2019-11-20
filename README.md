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
      "HANA_USER": "$ENV(hana_user)",
      "HANA_PASS": "$SECRET(hana_psas)",
      "LOG_LEVEL": "DEBUG"
    },
    "image": "<docker repo>",
    "memory": 128,
    "password": "<password>",
    "port": 5001,
    "username": "<username>"
  },
  "read_timeout": 7200,
  "type": "system:microservice",
  "use_https": false,
  "verify_ssl": true
}
```
Example pipe config:
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
