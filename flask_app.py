from cgitb import html
from flask.globals import request
import pymysql
from flask import Flask, render_template, session
from flask import flash, url_for, redirect, session
from flask import make_response
from flask.globals import request
from flask_sqlalchemy import SQLAlchemy
from flask_login import current_user, login_user, logout_user, login_required
from flask_login import LoginManager
from functools import wraps
import datetime



app = Flask(__name__)
app.secret_key = '_5#y2L"F4Q8z\n\xec]/'  # for login session

# sqlalchemy connection to database
app.config[
    'SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://MaristGroup5:password123@MaristGroup5.mysql.pythonanywhere-services.com:3306/MaristGroup5$polling'
db = SQLAlchemy(app)

# initialize the login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# set the session to expire after 30 minutes
session_duration = datetime.timedelta(seconds=1800)
app.permanent_session_lifetime = session_duration

# Set the option to the page is stored in the session under the key next.
app.config['USE_SESSION_FOR_NEXT'] = True


# connection to the "user" table in database using sqlalchemy
class User(db.Model):
    __tablename__ = 'user'
    username = db.Column('username', db.String(50), primary_key=True)
    firstName = db.Column('firstName', db.String(50))
    mi = db.Column('mi', db.String(1))
    lastName = db.Column('lastName', db.String(50))
    emailaddress = db.Column('emailaddress', db.String(50))
    password = db.Column('password', db.String(30))
    role = db.Column('role', db.String(20))
    authenticated = False

    def __init__(self, uname, fname, mi, lname, passwd, eaddress, role):
        self.username = uname
        self.firstName = fname
        self.mi = mi
        self.lastName = lname
        self.emailaddress = eaddress
        self.password = passwd
        self.authenticated = True
        self.role = role

    def is_authenticated(self):
        """Return True if the user is authenticated."""
        return self.authenticated

    def is_active(self):
        """True, as all users are active."""
        return True

    def is_anonymous(self):
        """False, as anonymous users aren't supported."""
        return False

    def get_id(self):
        """Return the id to satisfy Flask-Login's requirements."""
        return self.username

    def set_authenticated(self, is_authenticated):
        self.authenticated = is_authenticated

    def is_administrator(self):
        return self.role == 'admin'


# This method is required by Login Manager so that it can get the user's id.
@login_manager.user_loader
def load_user(user_id):
    return User.query.filter(User.username == user_id).first()


# function to check if user is an admin
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_administrator():
            flash("The user " + current_user.username
                  + " is not allowed to take this action.  "
                  + "Logout and log back in with appropriate credentials.")
            return redirect(url_for('index', next=request.url))
        return f(*args, **kwargs)

    return decorated_function


# verifying users, also passing login and password to database
@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    loginname = request.values["loginname"]
    password = request.values["loginpassword"]
    user = User.query.filter(User.username == loginname and User.password == password).first()
    if user is not None:
        login_user(user)
        # Now, look-up which page the user was trying to access and redirect
        next_page = url_for('index')
        return redirect(next_page)
    else:
        #errors stem from this.
        return render_template("login.html")


# logs user out of authorized account
@app.route('/logout', methods=["GET", "POST"])
def logout():
    if current_user is not None and current_user.is_authenticated:
        logout_user()
        flash('You have been logged out.')

        return redirect(url_for('index'))

    flash('You are not logged in currently')
    return redirect(url_for('index'))


# checks for unauthorized user
@app.route('/unauthorized', methods=["GET", "POST"])
def unauthorized():
    flash('You are not authorized to access this view.')
    return redirect(url_for('index'))


# main page
@app.route('/')
def index():
    return render_template("Polling_application_startup.html")


# renders form that allows for users to signup
@app.route('/signUp', methods=["get"])
def signUp():
    return render_template("signUp.html")


# Returns true if there is a user record for a given username
def doesUserExist(username):
    userExists = False
    dbConnection = getdbconnection(mysqlconnection)
    dbcursor = None
    try:
        get_user_query = "SELECT * FROM user WHERE username = %s"
        dbcursor = dbConnection.cursor()
        dbcursor.execute(get_user_query, (username))
        result = dbcursor.fetchone()
        if result != None:
            userExists = True
    finally:
        dbcursor.close()

    return userExists


# populate the completion the you have signed up. passing the values to the database
@app.route("/signUpNewUser", methods=["post"])
def signUpNewUser():

    # connection the database
    dbConnection = getdbconnection(mysqlconnection)
    dbcursor = None
    try:
        username = request.form.get('username')
        firstName = request.form.get('firstName')
        mi = request.form.get('mi')
        lastName = request.form.get('lastName')
        emailaddress = request.form.get('emailaddress')
        password = request.form.get('password')
        role = "admin"


        username = username.strip()

        # verify that the student and the course/section exists.
        if doesUserExist(username) and (username is not None) and (username != ""):
            msg = "Username already exists"
            return render_template("error.html", error_message=msg)


        # insert a row into the answer database table
        dbcursor = dbConnection.cursor()
        insert_question_qry = "INSERT INTO user (username, firstName, mi, lastName, emailaddress, password, role) \
                                            VALUES ( %s, %s, %s, %s, %s, %s, %s);"

        dbcursor.execute(insert_question_qry, (username, firstName, mi, lastName, emailaddress, password, role))

        # connection is not autocommit by default. So you must commit to save your changes.
        # Do this after inserts, updates, and deletes.  In other words, any operation that
        # changes the state of the DB.  Select statements do not require this step.
        dbConnection.commit()

        # Build a response HTML document for confirmation
        html_response_str = render_template("signUpNewUser.html", username=username, firstName=firstName, mi=mi,lastName=lastName, emailaddress=emailaddress, password=password, role=role)

    finally:
        if dbcursor is not None:
            dbcursor.close()

    return html_response_str


# renders the form to create a poll
@app.route('/MakePoll', methods=["get", "POST"])
@login_required
def render_add_poll_form():
    return render_template("MakePoll.html")


# populates the verification that the polls been created
# passes the values from "make poll" into the database once the user is redirected to "/pollCreated"
@app.route("/poll_created", methods=["post"])
def pollCreated():
    # connection the database
    dbConnection = getdbconnection(mysqlconnection)
    dbcursor = None
    try:
        questionTitle = request.form.get('questionTitle')
        askQuestion = request.form.get('askQuestion')
        ansQuestionResponse1 = request.form.get('ansQuestionResponse1')
        ansQuestionResponse2 = request.form.get('ansQuestionResponse2')
        ansQuestionResponse3 = request.form.get('ansQuestionResponse3')
        ansQuestionResponse4 = request.form.get('ansQuestionResponse4')
        response = request.form.get('response')

        # Next, insert a row into the student DB table.
        dbcursor = dbConnection.cursor()
        insert_question_qry = "INSERT INTO question (questionTitle, askQuestion, \
                                            ansQuestionResponse1, \
                                            ansQuestionResponse2, ansQuestionResponse3, \
                                            ansQuestionResponse4, response) \
                                            VALUES ( %s, %s, %s, %s, %s, %s, %s);"

        dbcursor.execute(insert_question_qry, (
        questionTitle, askQuestion, ansQuestionResponse1, ansQuestionResponse2, ansQuestionResponse3,
        ansQuestionResponse4, response))

        # connection is not autocommit by default. So you must commit to save your changes.
        # Do this after inserts, updates, and deletes.  In other words, any operation that
        # changes the state of the DB.  Select statements do not require this step.
        dbConnection.commit()

        # Build a response HTML document for confirmation
        html_response_str = render_template("poll_created.html", questionTitle=questionTitle, askQuestion=askQuestion,
                                            ansQuestionResponse1=ansQuestionResponse1,
                                            ansQuestionResponse2=ansQuestionResponse2,
                                            ansQuestionResponse3=ansQuestionResponse3,
                                            ansQuestionResponse4=ansQuestionResponse4, response=response)
    finally:
        if dbcursor is not None:
            dbcursor.close()

    return html_response_str


##############################################################################################################
# populates the verification that the polls been created
# passes the values from "make poll" into the database once the user is redirected to "/pollCreated"
@app.route("/second_poll_created", methods=["post"])
def secondPollCreated():
    # connection the database
    dbConnection = getdbconnection(mysqlconnection)
    dbcursor = None
    try:
        questionTitle2 = request.form.get('questionTitle2')
        askQuestion2 = request.form.get('askQuestion2')
        QuestionResponse1 = request.form.get('QuestionResponse1')
        QuestionResponse2 = request.form.get('QuestionResponse2')
        QuestionResponse3 = request.form.get('QuestionResponse3')
        QuestionResponse4 = request.form.get('QuestionResponse4')

        # Next, insert a row into the student DB table.
        dbcursor = dbConnection.cursor()
        insert_question_qry = "INSERT INTO freeTextQuestion (questionTitle2, askQuestion2, \
                                            QuestionResponse1, \
                                            QuestionResponse2, QuestionResponse3, \
                                            QuestionResponse4) \
                                            VALUES ( %s, %s, %s, %s, %s, %s);"

        dbcursor.execute(insert_question_qry, (
        questionTitle2, askQuestion2, QuestionResponse1, QuestionResponse2, QuestionResponse3,
        QuestionResponse4))

        dbConnection.commit()

        # Build a response HTML document for confirmation
        html_response_str = render_template("second_poll_created.html", questionTitle2=questionTitle2, askQuestion2=askQuestion2,
                                            QuestionResponse1=QuestionResponse1,
                                            QuestionResponse2=QuestionResponse2,
                                            QuestionResponse3=QuestionResponse3,
                                            QuestionResponse4=QuestionResponse4)
    finally:
        if dbcursor is not None:
            dbcursor.close()

    return html_response_str
##############################################################################################################



# This is used to generate a list of links to question poll
@app.route('/QuestionsForm', methods=["get"])
def render_poll_questions():
    dbConnection = getdbconnection(mysqlconnection)
    dbcursor = None
    try:
        dbcursor = dbConnection.cursor()  # tuple

        # questionID and question title
        sql_query2 = "SELECT question.questionID, question.questionTitle FROM question;"
        recordCount2 = dbcursor.execute(sql_query2)
        print("The query returns ", recordCount2, " records.")
        questionTitleDB = dbcursor.fetchall()
        questionTitleDB = list(questionTitleDB)

        # return the title to the template (as a link on the template)
        for questionRecord in questionTitleDB:
            print(questionRecord[1])


    finally:
        if dbcursor is not None:
            dbcursor.close()
    return render_template("QuestionsForm.html", question_list=questionTitleDB)



# "poll" is the primary key identifier to "question" which is passed into the URL as an argument
@app.route('/<poll>', methods=["get"])
@login_required
def takePoll(poll):
    dbConnection = getdbconnection(mysqlconnection)
    dbcursor = None
    try:
        # question is identified by primary key
        dbcursor = dbConnection.cursor()  # tuple
        sql_query = "SELECT * FROM question WHERE questionID = %s;"
        recordCount = dbcursor.execute(sql_query, (poll))
        print("The query returns ", recordCount, " records.")
        questions = dbcursor.fetchall()
        questions = list(questions)

        # list the answer choices from "MakePoll"
        for questionRecord in questions:
            print(questionRecord[4], questionRecord[5], questionRecord[6], questionRecord[7])

    finally:
        if dbcursor is not None:
            dbcursor.close()
    return render_template("TakePoll.html", question_list=questions)




# deletes a poll
@app.route('/DeletePoll', methods=["get", "POST"])
@login_required
def render_delete_poll_form():
    dbConnection = getdbconnection(mysqlconnection)
    dbcursor = None
    try:
        # returns the primary key and the question title in a list
        dbcursor = dbConnection.cursor()  # tuple
        sql_query = "SELECT * FROM question;"
        recordCount = dbcursor.execute(sql_query)
        print("The query returns ", recordCount, " records.")
        questionID = dbcursor.fetchall()
        questionID = list(questionID)

        # returns the elements in the "question" table
        # is displayed in a drop down box in a template
        for questionIDRecord in questionID:
            print(questionIDRecord[0])

    finally:
        if dbcursor is not None:
            dbcursor.close()
    return render_template("DeletePoll.html", category_list=questionID)


# renders page saying "deletion of poll completed"
# executes deletion based on primary key
@app.route('/DeletePollComplete', methods=["get", "POST"])
@login_required
def render_delete_poll_Complete():
    dbConnection = getdbconnection(mysqlconnection)
    dbcursor = None
    try:
        delete = request.form.get('category')
        dbcursor = dbConnection.cursor()
        sql_query = "DELETE FROM question WHERE questionID = %s;"
        recordCount = dbcursor.execute(sql_query, (delete))
        print("The query returns ", recordCount, " records.")
        dbConnection.commit()

        html_response_str = render_template("DeletePollComplete.html", recordCount=recordCount, category=delete)

    finally:
        if dbcursor is not None:
            dbcursor.close()
    return html_response_str


# this updates poll question
# **there is a problem here with auto increment and update --> cannot pass integer to primary key
@app.route('/UpdatePoll', methods=["get", "POST"])
@login_required
def render_update_poll():
    dbConnection = getdbconnection(mysqlconnection)
    dbcursor = None
    try:
        questionID = request.form.get('questionID')
        questionTitle = request.form.get('questionTitle')
        askQuestion = request.form.get('askQuestion')
        ansQuestionResponse1 = request.form.get('ansQuestionResponse1')
        ansQuestionResponse2 = request.form.get('ansQuestionResponse2')
        ansQuestionResponse3 = request.form.get('ansQuestionResponse3')
        ansQuestionResponse4 = request.form.get('ansQuestionResponse4')
        response = request.form.get('response')
        # questionID = int(questionID)

        # Next, update a row into the student DB table.
        dbcursor = dbConnection.cursor()

        insert_question_qry = "UPDATE question SET  questionID = %s, questionTitle = %s, askQuestion = %s, \
                                            ansQuestionResponse1= %s, \
                                            ansQuestionResponse2 = %s, ansQuestionResponse3 = %s, \
                                            ansQuestionResponse4 = %s, response = %s  \
                                            WHERE questionID = %s;"

        dbcursor.execute(insert_question_qry, (
        questionID, questionTitle, askQuestion, ansQuestionResponse1, ansQuestionResponse2, ansQuestionResponse3,
        ansQuestionResponse4, response, questionID))

        # connection is not autocommit by default. So you must commit to save your changes.
        # Do this after inserts, updates, and deletes.  In other words, any operation that
        # changes the state of the DB.  Select statements do not require this step.
        dbConnection.commit()

        # Build a response HTML document for confirmation
        html_response_str = render_template("UpdatePoll.html", questionID=questionID, questionTitle=questionTitle,
                                            askQuestion=askQuestion,
                                            ansQuestionResponse1=ansQuestionResponse1,
                                            ansQuestionResponse2=ansQuestionResponse2,
                                            ansQuestionResponse3=ansQuestionResponse3,
                                            ansQuestionResponse4=ansQuestionResponse4, response=response)
    finally:
        if dbcursor is not None:
            dbcursor.close()

    return html_response_str


# populates the answer table with the results of take a poll
@app.route('/results', methods=["get", "POST"])
def results():
    dbConnection = getdbconnection(mysqlconnection)
    dbcursor = None
    try:
        username = current_user.username
        questionID = request.form.get('questionID')
        answerChoiceSelected = request.form.get('Question')

        # insert a row into the answer database table
        dbcursor = dbConnection.cursor()
        insert_question_qry = "INSERT INTO answer (username, questionID, answerChoiceSelected) \
                                            VALUES ( %s, %s, %s);"

        dbcursor.execute(insert_question_qry, (username, questionID, answerChoiceSelected))

        # connection is not autocommit by default. So you must commit to save your changes.
        # Do this after inserts, updates, and deletes.  In other words, any operation that
        # changes the state of the DB.  Select statements do not require this step.
        dbConnection.commit()

        # Build a response HTML document for confirmation
        html_response_str = render_template("results.html", username=username, questionID=questionID,
                                            answerChoiceSelected=answerChoiceSelected)

    finally:
        if dbcursor is not None:
            dbcursor.close()

    return html_response_str



##########################################################################################

def countTotal(questionNumber):
    dbConnection = getdbconnection(mysqlconnection)
    dbcursor = None
    try:
        get_user_query = "SELECT count(questionID) FROM question NATURAL JOIN answer where question.response is NULL and questionID = %s;"
        dbcursor = dbConnection.cursor()
        dbcursor.execute(get_user_query, (questionNumber))
        result = dbcursor.fetchall()
        result = list(result[0])
        #result = int(result[0])

    finally:
        dbcursor.close()

    return result
##########################################################################################

def countChoice(questionID, answerChoiceSelected):
    dbConnection = getdbconnection(mysqlconnection)
    dbcursor = None
    try:
        get_user_query = "SELECT count(%s) FROM question NATURAL JOIN answer where question.response is NULL and answerChoiceSelected = %s ; "
        dbcursor = dbConnection.cursor()
        dbcursor.execute(get_user_query, (questionID, answerChoiceSelected))
        result = dbcursor.fetchall()
        result = list(result[0])
        #result = int(result[0])
    finally:
        dbcursor.close()
    return result



# this populates an html table so that admins may view results
@app.route('/ViewResult', methods=["get"])
@login_required
def render_poll_results():
    dbConnection = getdbconnection(mysqlconnection)
    dbcursor = None
    try:

        dbcursor = dbConnection.cursor()  # tuple

        # used a natural join to combine the elements of both "question" and "answer" table
        sql_query = "SELECT * FROM question NATURAL JOIN answer WHERE question.response IS NOT NULL;"
        recordCount = dbcursor.execute(sql_query)
        print("The query returns ", recordCount, " records.")
        responses = dbcursor.fetchall()
        responses = list(responses)

        # listing both tables into an html table to compare responses
        for responseRecord in responses:
            print(responseRecord)

        #dbcursor2 = dbConnection.cursor()  # tuple
        sql_query2 = "SELECT distinct * FROM question NATURAL JOIN answer WHERE question.response is NULL GROUP BY questionID ORDER BY questionID ASC ;"
        recordCount2 = dbcursor.execute(sql_query2)
        print("The query returns ", recordCount2, " records.")
        responses2 = dbcursor.fetchall()
        responses2 = list(responses2)
        #responses2 = int(responses2[0])

               # listing both tables into an html table to compare responses
        for responseRecord in responses2 :
            count = countTotal(responseRecord[0])
            count2 = countChoice(responseRecord[0], "A")
            count3 = countChoice(responseRecord[0], "B")
            count4 = countChoice(responseRecord[0], "C")
            count5 = countChoice(responseRecord[0], "D")
            print(responseRecord)

        #count = countTotal(6)
        #count = int(count)
        #count2 = countChoice(6, "A")
        #countTotal(questionNumber)
        #countChoice(questionID, answerChoiceSelected)

    finally:
        if dbcursor is not None:
            dbcursor.close()
    return render_template("ViewResult.html", response_list=responses, responses2=responses2, count=count, count2=count2,  count3=count3,  count4=count4, count5=count5)




# This method either returns a new connection for the first time it is called
# or checks whether the connection still works and makes another one if
# connetcion is lost
def getdbconnection(con):
    if con is None or not con.open:
        con = pymysql.connect(user='MaristGroup5',
                              password='password123',
                              host='MaristGroup5.mysql.pythonanywhere-services.com',
                              port=3306,
                              database='MaristGroup5$polling')

    return con


mysqlconnection = getdbconnection(None)

if __name__ == '__main__':
    app.run()
