#connect.py

#Import your dependencies
from hdbcli import dbapi
#Initialize your connection
conn = dbapi.connect(
    address='hxehost',
    port='39015',
    user='SESAMER',
    password='SesamRocks01!'
)
#If no errors, print connected
print('connected')

### rest of your code here ###
cursor = conn.cursor()
cursor.execute("SELECT * FROM james")
for result in cursor:
    print(result)
