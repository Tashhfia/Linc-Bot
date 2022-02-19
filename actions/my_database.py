import mysql.connector

# add user to mailing list
def addToMailingList(email):
    """ here we add the user's email to our mailing list database"""
    mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        passwd="root",
        database="rasa_restobot"
    )
    # takes care of all the sql execution
    mycursor = mydb.cursor()

    addMailing_sql = 'INSERT INTO mailingList (email_add) VALUES ("{0}");'.format(email)

    # execute the statement
    mycursor.execute(addMailing_sql)

    # commit changes into database
    mydb.commit()


# check mailing list for user's email
def checkMailingList(email):
    """Here we check if the user's email address already exists in the mailing list"""
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        passwd="root",
        database="rasa_restobot"
    )
    myCursor = db.cursor()
    # finds the first entry that matches the user's input
    check_sql = 'SELECT EXISTS(SELECT email_add FROM mailingList WHERE email_add="{0}");'.format(email)
    myCursor.execute(check_sql)
    data = myCursor.fetchone()

    if data[0] == 1:
        return True
    else:
        return False

# record user's req for human handoff
def addToHandoffReq(email, issue, urgency):
    """Here we insert the values retrieved from the user's messages into our database"""
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        passwd="root",
        database="rasa_restobot"
    )
    myCursor = db.cursor()
    # inserts request details into the handoffReq table
    sql = 'INSERT INTO handoffReq(Urgency, Issue, email_add) VALUES ("{0}","{1}","{2}");'.format(urgency, issue, email)
    myCursor.execute(sql)
    db.commit()


# add booking
def addToBookingList(date, time,email):
    """Here we insert the values retrieved from the user's messages into our database"""
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        passwd="root",
        database="rasa_restobot"
    )
    myCursor = db.cursor()
    # inserts request details into the handoffReq table
    sql = 'INSERT INTO bookingList(date, time, email) VALUES ("{0}","{1}","{2}");'.format(date, time,email)
    myCursor.execute(sql)
    db.commit()


# check if booking exists
def checkBookingList(email, date="none"):
    """Here we check if the user's email address already exists in the mailing list"""
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        passwd="root",
        database="rasa_restobot"
    )
    myCursor = db.cursor()
    # finds the first entry that matches the user's input
    # see if anybooking for this email address exists
    check_sql = 'SELECT EXISTS(SELECT email FROM bookingList WHERE email="{0}");'.format(email)
    myCursor.execute(check_sql)
    data_ch = myCursor.fetchone()

    # if data exists for this email
    if data_ch[0] == 1:
        if date != "none":
            # search wth date and email
            fetch_sql_1 = 'SELECT time FROM bookingList WHERE email="{0}" AND date="{1}";'.format(email, date)
            myCursor.execute(fetch_sql_1)
            data = myCursor.fetchone()
            print(data)

            if data is not None:
                time = data[0]
                return True, time
            else:
                return (False,)

        else:
            # user didnt provide date, so search without date, we will show all the available booking dates
            fetch_sql = 'SELECT date,time FROM bookingList WHERE email="{0}";'.format(email)
            myCursor.execute(fetch_sql)
            fetched_data = myCursor.fetchall()
            print(fetched_data)

            return True, fetched_data

    else:
        return (False,)  # need to return a tuple


# delete booking details
def deleteFromBookingList(email, date):
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        passwd="root",
        database="rasa_restobot"
    )
    myCursor = db.cursor()
    deleteBookingsql = 'DELETE FROM bookingList WHERE email="{0}" AND date="{1}";'.format(email, date)
    myCursor.execute(deleteBookingsql)
    print('deleted booking record')
    db.commit()


def deleteFromMalingList(email):
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        passwd="root",
        database="rasa_restobot"
    )
    myCursor = db.cursor()
    deletemailingsql = 'DELETE FROM mailingList WHERE email_add="{0}";'.format(email)
    myCursor.execute(deletemailingsql)
    print('deleted email')
    db.commit()


def menuQuery(query, item='none'):
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        passwd="root",
        database="rasa_restobot"
    )
    myCursor = db.cursor()

    available_info = ['healthy', 'vegan', 'popular', 'allergen']
    if item == 'none':
        if query.lower() == available_info[0]:
            healthyQ = 'SELECT Item_name, Calories FROM menu_info ORDER BY Calories ASC LIMIT 3;'
            myCursor.execute(healthyQ)
            fetched_data = myCursor.fetchall()
            print(fetched_data)
            return fetched_data

        elif query.lower() == available_info[1]:
            veganQ = 'SELECT Item_name FROM menu_info WHERE Vegan_friendly =1;'
            myCursor.execute(veganQ)
            fetched_data = myCursor.fetchall()
            print(fetched_data)
            return fetched_data
        elif query == available_info[2]:
            popularQ = 'SELECT Item_name, Units_sold FROM menu_info ORDER BY Units_sold DESC LIMIT 3;'
            myCursor.execute(popularQ)
            fetched_data = myCursor.fetchall()
            print(fetched_data)
            allpop = "SELECT Item_name, Units_sold FROM menu_info WHERE Category != 'beverage' ORDER BY Units_sold DESC LIMIT 4;"
            myCursor.execute(allpop)
            fetch_data = myCursor.fetchall()
            print(fetch_data)
            return fetched_data, fetch_data
    else:
        if query.lower() == available_info[0]:
            healthyQ = "SELECT Calories FROM menu_info WHERE Item_name='{0}'; ".format(item)
            myCursor.execute(healthyQ)
            fetched_data = myCursor.fetchone()
            # print(fetched_data)
            return fetched_data

        elif query.lower() == available_info[1]:
            veganQ = "SELECT Vegan_friendly FROM menu_info WHERE Item_name='{0}'; ".format(item)
            myCursor.execute(veganQ)
            fetched_data = myCursor.fetchone()

            if fetched_data[0] == 1:
                return True
            else:
                return False
        elif query.lower() == available_info[3]:
            allergenQ = "SELECT Allergen_list FROM menu_info WHERE Item_name='{0}'; ".format(item)
            myCursor.execute(allergenQ)
            fetched_data = myCursor.fetchone()
            return fetched_data


# edit booking details
# use actions for editing slots?
#test if database connection is working correctly
if __name__ == "__main__":
    k = menuQuery('allergen', 'apple pie')
    len = len(k)
    print(k[0])






