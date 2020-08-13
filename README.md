# Introduction 

This package integrates SAP Hana with Sesam and implements the Sesam protocol for reading tables from SAP Hana

# Usage

The endpoint [GET] /query has no required arguments and will simply query the SAP HANA using SELECT 1. This can be used to check whether a connection is successfully established.
If you pass a SQL-Query don't worry about pagination. From the arguments given the following final query is constructed:

```
  SELECT
    <since_expression> AS _updated,
    *
  FROM (<raw_query>) T
  WHERE <since_expression> >= <since>
  ORDER BY _updated
LIMIT <limit>
```

Example GET arguments:

```
  {
    "since_expression": "DateUpdated",
    "query": "SELECT * FROM T WHERE T.spend > 100000",
    "limit": 1000,
    "since": "2020-11-12"
  }
```

query
-----

Query the data in plain SQL you are interested in. Pagination etc. will be handled separately.

limit
-----

Batch size, used for querying and returning the data in an paginated, Sesam compatible way.

since_expression
----------------

The Sesam-Pull protocol requires a since-attribute that acts as a last-updated attribute. It does not need to be a timestamp, any orderable attribute or SQL-expression will do. Examples: since_expression="UpdatedAt" or since_expression="0FISCYEAR" || "VENDOR" || "VENDOR_COUNTRY"

since
-----

Skip values that come before the given value when compared with <since_expression>. Together with limit this argument is used for querying and returning the data in an paginated, Sesam compatible way.

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
Example put_rows pipe config:
----------------------------
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
