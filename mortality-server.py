# A simple server for mortality data
#
# Requires the bottle framework
# (sufficient to have bottle.py in the same folder)
#
# run with:
#
#    python mortality-server.py 8080
#
# You can use any legal port number instead of 8080
# of course

from bottle import get, run, request, static_file
import sys
import sqlite3


# the name of the database file
MORTALITYDB = "mortality.db"


# Function to take a list of rows (each a dictionary)
# and group them by the value of a field F
# creating a dictionary with a key for each value
# in F mapping to the rows with that value for field F 

def group_by (rows,field):
    values = set([r[field] for r in rows])
    grouped_rows = {}
    for (value,rows) in [(value,[r for r in rows if r[field]==value]) for value in values]:
        grouped_rows[value] = rows
    return grouped_rows


# Pulls the data from the database file
# All rows with the given gender
# (all rows if gender is None)
# Group the results by cause of death and
# by year

def pullData (gender):
    # ignore age & gender for now
    conn = sqlite3.connect(MORTALITYDB)
    cur = conn.cursor()

    try: 
        if gender:
            cur.execute("""SELECT year, Cause_Recode_39, SUM(1) as total 
                           FROM mortality
                           WHERE sex = '%s'
                           GROUP BY year, Cause_Recode_39""" % (gender))
        else:
            cur.execute("""SELECT year, Cause_Recode_39, SUM(1) as total 
                           FROM mortality
                           GROUP BY year, Cause_Recode_39""")
        data = [{"year":int(year),
                 "cause":int(cause),
                 "total":total} for (year, cause, total,) in  cur.fetchall()]
        grouped_data = group_by(data,"cause")
        for cause in grouped_data:
            grouped_data[cause]= group_by(grouped_data[cause],"year")
        conn.close()
        return grouped_data

    except: 
        print "ERROR!!!"
        conn.close()
        raise
        

# URI for getting data
# pass a gender argument as:
#    data?gender=M  
#    data?gender=F
#    data?gender=
#
# Return the result in JSON format

@get("/data")
def data ():
    print list(request.query)
    gender = request.query.gender

    print "gender =", gender
    return pullData(gender)

    
# URI for getting a static file from the
# server
# For instance, mortality-demo.html

@get('/<name>')
def static (name="index.html"):
    return static_file(name, root='.')


# main entry point
# run the server on the given port

def main (p):
    run(host='0.0.0.0', port=p)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        main(int(sys.argv[1]))
    else:
        print "Usage: server <port>"
