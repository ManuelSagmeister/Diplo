from multiprocessing import connection
import mysql.connector
import time
import numpy as np
from numpy import sqrt
from datetime import datetime


listeDerJsonObjekte = []

zaehler = 0
counter = 2
# mögliche Lösung --> listeDerJsonObjekte mit den 3 AchorsID; wenn Anchor in listeDerJsonObjekte vorhanden - distance wird überschrieben ansonsten wird anchor in listeDerJsonObjekte aufgenommen
# -->wartet bis 3 Anchors in der listeDerJsonObjekte vermerkt wurden

def DBQuery():
    global mydb
    mydb = mysql.connector.connect(
        host='192.168.25.107',
        port=3306,
        user='TestUser',
        password='password',
        database='strack'
    )



def checkIfElementInList(outputFromList):

    if not listeDerJsonObjekte:
        listeDerJsonObjekte.append({outputFromList[0]: outputFromList[1]})
        print("Daten wurde hinzugefügt")
        return

    else:
        zaehler = 0
        while zaehler < len(listeDerJsonObjekte):
            for espID in listeDerJsonObjekte[zaehler]:
                if espID == outputFromList[0]:
                    del listeDerJsonObjekte[zaehler]
                    listeDerJsonObjekte.insert(
                        zaehler, {outputFromList[0]: outputFromList[1]})
                    print(listeDerJsonObjekte)
                    if len(listeDerJsonObjekte) == 3:
                        trilateration()
                    else:
                        return  # springt aus der funktion heraus

                else:
                    zaehler = zaehler + 1
                    break  # sprint aus der for loop heraus

    if len(listeDerJsonObjekte) < 3:
        listeDerJsonObjekte.append({outputFromList[0]: outputFromList[1]})
        return
    else:
        trilateration()


def getValue():
    counter = 0
    while counter < 3:
        for i in listeDerJsonObjekte[counter]:
            for x in myresultAnchor:
                if x[0] == i:
                    
                    getDistance = globals()[f"d{counter}"] = [x[0], listeDerJsonObjekte[counter][i]]
                    getAnchor = globals()[f"a{counter}"] = [x[0], x[1],x[2]]
                    counter += 1




def getLatLongFromAnchor():
    time.sleep(1)
    global keyListFromAnchor
    keyListFromAnchor = []
    mycursor = mydb.cursor()
    mycursor.execute(
        "SELECT a_MAC,a_Lat, a_Lon FROM Anchor")
    global myresultAnchor
    myresultAnchor = mycursor.fetchall()

    mycursor.execute(
          "SELECT fk_Anchor_MAC,r_Range FROM Ranges order by r_ID DESC Limit 3")
    myresultRanges = mycursor.fetchall()
    for x in myresultRanges:
        checkIfElementInList(x)
        


def trilateration():
    getValue()
    time.sleep(0.5)
 # ported from https://github.com/gheja/trilateration.js
    # points -> list of np arrays in the form of [[x, y, z], [x, y, z]
    # distances -> np array [r1, r2, r3]

    p1 = np.array([a0[1],a0[2], 0.0])  # 6017
    p2 = np.array([a1[1],a1[2], 0.0])  # 6018
    p3 = np.array([a2[1],a2[2], 0.0])  # 6019

    r1 = d0[1]
    r2 = d1[1]
    r3 = d2[1]

    def norm(v):
        return np.sqrt(np.sum(v**2))

    def dot(v1, v2):
        return np.dot(v1, v2)

    def cross(v1, v2):
        return np.cross(v1, v2)

    ex = (p2-p1) / norm(p2-p1)
    i = dot(ex, p3-p1)
    a = (p3-p1) - ex*i
    ey = a / norm(a)
    ez = cross(ex, ey)
    d = norm(p2-p1)
    j = dot(ey, p3-p1)
    x = (r1**2 - r2**2 + d**2) / (2*d)
    y = (r1**2 - r3**2 + i**2 + j**2) / (2*j) - (i/j) * x
    b = r1**2 - x**2 - y**2

    # floating point math flaw in IEEE 754 standard
    # see https://github.com/gheja/trilateration.js/issues/2
    if (np.abs(b) < 0.0000000001):
        b = 0

    z = np.sqrt(abs(b))
    if np.isnan(z):
        raise Exception('NaN met, cannot solve for z')

    a = p1 + ex*x + ey*y

    p4a = a + ez*z

    position = list(p4a)
    insertXY(position)
    #p4b = a - ez*z
    # print(p4b)

    for i in listeDerJsonObjekte:
        global counter
        while counter >= 0:

            listeDerJsonObjekte.remove(listeDerJsonObjekte[counter])
            counter = counter-1

    counter = 2
    return


def insertXY(location):
    mycursor = mydb.cursor()
    current_time = datetime.now()
    print(current_time)
    sql = "INSERT INTO Location (l_Time, l_Lat, l_Lon) VALUES (%s, %s, %s)"
    val = (current_time, float(location[0]), float(location[1]))
    mycursor.execute(sql, val)
    mydb.commit()


def loop():
    while True:
        getLatLongFromAnchor()
        #getDataFromRanges(mydb)


DBQuery()
loop()
