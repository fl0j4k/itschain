import sqlite3 as db


def installDatabase(dbconn):
    #dbconn = db.connect(location)

    with dbconn:
        cur = dbconn.cursor()
        cur.execute("CREATE TABLE connected(nodename INT, nodeaddr INT, handshaketime DATETIME)")
        #cur.execute("INSERT INTO assignednodes VALUES('Node1','localhost:5111',datetime('now', 'localtime'))")
        cur.execute("CREATE TABLE lastid(dataid INT, nodesid INT, assignedid INT)")
        cur.execute("INSERT INTO lastid VALUES(?,?,?)", (0, 0, 0))
        cur.execute("CREATE TABLE data(id INT, address TEXT)")
        cur.execute("CREATE TABLE assignednodes(id INT, dataid INT, nodeid INT)")
        cur.execute("CREATE TABLE nodes(id INT, name TEXT, connectaddr TEXT)")
        #cur.execute("DROP TABLE connected")
        #cur.execute("CREATE TABLE connected(nodename INT, nodeaddr INT, handshaketime DATETIME)")
        #cur.execute("DELETE FROM connected WHERE timestamp <= datetime('now', '-1 minutes')")
        #cur.execute("SELECT * FROM connected WHERE handshaketime <= datetime('now', '-1 Minute')")
        #rows = cur.fetchall()
        #cur.execute("DELETE FROM nodes WHERE connectaddr ='localhost:5222'")

        dbconn.commit()