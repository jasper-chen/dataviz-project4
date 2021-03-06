# A simple server for mortality data
#
# Requires the bottle framework
# (sufficient to have bottle.py in the same folder)
#
# run with:
#
#    python server.py 8080
#
# You can use any legal port number instead of 8080
# of course

from bottle import get, run, request, static_file
import sys
import sqlite3
import json


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

def converttoYearAge(ageKey,ageValue):
    float_age = 0
    if ageKey == u'1':
        float_age = float(ageValue)
    elif ageKey == u'2':
        float_age = float(ageValue)/12
    elif ageKey == u'4':
        float_age = float(ageValue)/365.25
    elif ageKey == u'5':
        float_age = float(ageValue)/8670
    elif ageKey == u'6':
        float_age = float(ageValue)/525600    
    return float_age

# Pulls the data from the database file
# Gets the key, value, year, code and max count
# Returns a JSON object of the type of death per year, per age.

def pullbyAvgAge():
    #code #2003 #2008 #2013

    conn = sqlite3.connect(MORTALITYDB)
    cur = conn.cursor()

    try:
        cur.execute("""SELECT mortality.Cause_Recode_39, mortality.year, mortality.Age_Key, AVG(mortality.Age_Value), COUNT(mortality.Age_Value), recodecounts.recodetotal
                        FROM mortality
                        INNER JOIN (SELECT Cause_Recode_39, year, COUNT(Age_Key) as recodetotal
                              FROM mortality
                              WHERE Age_Value != '999'
                              GROUP BY year, Cause_Recode_39) recodecounts
                        ON mortality.Cause_Recode_39 = recodecounts.Cause_Recode_39 and mortality.year = recodecounts.year
                        WHERE mortality.Age_Value != '999'
                        GROUP BY mortality.Cause_Recode_39,
                            mortality.year, 
                            mortality.Age_Key""")

        #refinedAgeCount : # of people dying by Recode, year and Age Key
        #recodeCount : # of people dying by Recode and Year

        data = [{"cause": int(cause),
            "year": str(year),
            "ageKey": ageKey,
            "avgAge": avgAge,
            "refinedAgeCount": refinedAgeCount,
            "recodeCount": recodeCount} for (cause, year, ageKey, avgAge, refinedAgeCount, recodeCount) in cur.fetchall()]

        returnJson = []

        groupedData = group_by(data, "cause")

        for cause in groupedData.keys():
            causeJson = {"cause": cause}
            for row in groupedData[cause]:
                age = converttoYearAge(row["ageKey"],row["avgAge"])

                if row["year"] in causeJson:
                    causeJson[row["year"]] += (row["refinedAgeCount"]/float(row["recodeCount"]))*age
                else:
                    causeJson[row["year"]] = (row["refinedAgeCount"]/float(row["recodeCount"]))*age

            returnJson.append(causeJson)

        conn.close()
        return sorted(returnJson, key = lambda causeJson: causeJson["cause"])

    except:
        print "ERROR!!!"
        conn.close()
        raise

def pullbyAgeAndTopCause():
    conn = sqlite3.connect(MORTALITYDB)
    cur = conn.cursor()

    try:
        cur.execute("""SELECT Age_Key, Age_Value, year, Cause_Recode_39, MAX(Count_of_Deaths)
                        FROM (SELECT Age_Key, Age_Value, year, Cause_Recode_39, COUNT(Cause_Recode_39) as Count_of_Deaths
                              FROM mortality
                              WHERE Age_Value != '999'
                              GROUP BY Age_Key, Age_Value, year, Cause_Recode_39

                        )
                        GROUP BY Age_Key, Age_Value, year""")
        returnJson = []
        data = []

        for (ageKey, ageValue, year, cause, total,) in cur.fetchall():
            #converts to its real age based on the key and value
            age = converttoYearAge(ageKey,ageValue)

            data.append({"age": age,
                 "year": str(year), 
                 "cause": int(cause),
                 "total": int(total)})

        #grouping by age
        grouped_data = group_by(data, "age")
        #accessing all ages
        for age in grouped_data.keys():
            ageJson = {"age": float(age), #wont be ordered unless has float cast
                        "2003": "NA",
                        "2008": "NA",
                        "2013": "NA"}
            for row in grouped_data[age]: 
                #in each age, replace json's year with its cause
                ageJson["age"] = row["age"]
                ageJson[row["year"]] = row["cause"]
            returnJson.append(ageJson)
        conn.close()

        return sorted(returnJson, key= lambda ageJson: ageJson["age"])
        #sorting by age

    except:
        print "ERROR!!!"
        conn.close()
        raise

def newDataPull():
    conn = sqlite3.connect(MORTALITYDB)
    cur = conn.cursor()

    try:
        cur.execute("""SELECT Manner_Of_Death, Activity_Code, Place_Of_Death, COUNT(*)
                      FROM mortality
                      WHERE Activity_Code != "" AND Activity_Code != "9" AND Manner_Of_Death != ""
                      GROUP BY Manner_Of_Death, Activity_Code, Place_Of_Death
                    """)
        returnJson = []
        data = []

        for (cause, activity, place, count,) in cur.fetchall():
            #converts to its real age based on the key and value

            data.append({"cause": int(cause),
                 "activity": activity, 
                 "place": int(place),
                 "count": int(count)})

        conn.close()

        return data

    except:
        print "ERROR!!!"
        conn.close()
        raise

@get('/test.html')
def static (name="test.html"):
    return static_file(name, root='.')

@get('/project4.html')
def static (name="project4.html"):
    return static_file(name, root='.')    

@get('/topcause')
def ageData():
    print ("GETTING AGE DATA")
    AgeAndTopCause = pullbyAgeAndTopCause()
    return {"AgeAndTopCause" : AgeAndTopCause}
    # data = []
    # with open('./topcause.json') as f:
    #     for line in f:
    #         data.append(json.loads(line))

    # return {'TopCause': data}

@get('/avg')
def ageData():
    print ("GETTING AGE DATA")
    AvgAge = pullbyAvgAge()
    return {"AvgAge" : AvgAge}
    data = []
    # with open('./avgage.json') as f:
    #     for line in f:
    #         data.append(json.loads(line))

    # return {'AvgData': data}   

# main entry point
# run the server on the given port

@get('/new')
def newData():
    print ("GETTING NEW DATA")
    data = newDataPull()
    #return {"ActivityData" : newData}
    #data = []
    # with open('./new.json') as f:
    #     for line in f:
    #         data.append(json.loads(line))

    # return {'ActivityData': data[0]['ActivityData'], 
    #         'Viz1' : group_by(data[0]['ActivityData'],"place"), 
    #         'Viz2' : group_by(data[0]['ActivityData'],"cause"),
    #         'Viz3' : group_by(data[0]['ActivityData'],"activity")} 

    return {
            'Viz1' : group_by(data,"place"), 
            'Viz2' : group_by(data,"cause"),
            'Viz3' : group_by(data,"activity")} 


def main (p):
    run(host='0.0.0.0', port=p)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        main(int(sys.argv[1]))
    else:
        print "Usage: server <port>"
