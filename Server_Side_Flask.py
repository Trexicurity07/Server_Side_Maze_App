from Database_Logic import *
from smtplib import SMTP_SSL
from datetime import datetime, timezone, timedelta
from flask import Flask, jsonify, request, render_template
from Session_Modules import Session, Users
from sqlalchemy import func
from secrets import token_urlsafe


App = Flask(__name__)


def VerifyToken(Token):

    try:
        TokenToUserDict[Token]
        return True
    except KeyError:
        return False
    # Except state in case no such token was assigned
# Verifies the session token and user through flask request


# Token passed in URL (easier to track user activity without safety risk) but more sensitive info eg passwords and user info are passed in json body that doesnt leave logs on servers
@App.route('/Signup', methods = ['POST'])
def Signup():

    JsonData = request.get_json()
    UsedCredentials = []

    UsedCredentials.append(
        Session.query(func.count()).filter(
        Users.UserName == JsonData['username']).scalar())
    UsedCredentials.append(
        Session.query(func.count()).filter(
        Users.Email == JsonData['email']).scalar())
    # Checks whether UserName or Email have already been used previously

    if UsedCredentials == [0, 0]:

        Token = token_urlsafe(16)  #  Generates 16 byte long random unique token
        JsonData['IssuedTime'] = datetime.now(timezone.utc)
        EmailTokenDict[Token] = JsonData
        # Adds to log of tokens used for email validation and sets their IssuedTime for timestamp ordering

        try:
            Gmail.sendmail('DummyEmailNEA@gmail.com', JsonData['email'], f'Click the following link to authenticate your account :\n\nhttps://server-side-maze-app.onrender.com/{Token}')
            # Sends email with authentication link to user address

        except:
            return jsonify(False)
            # Errors raised from incrorrectly entered email addresses

        return jsonify(True)

    return jsonify(UsedCredentials)


@App.route('/EmailAuth/<Token>', methods = ['GET'])
def EmailAuth(Token):
    
    try:
        if (EmailTokenDict[Token]['IssuedTime'] + timedelta(minutes = 30)) > datetime.now(timezone.utc):
            print(1)

            global UsersTimstamp
            # local assignment overrides scope of variable assigned in if __name__ == '__main__'
            # No simple workaround as flask routes and methods do not take parameters from rest of script

            if CheckTimestamp(UsersTimstamp, EmailTokenDict[Token]['IssuedTime']):
                print(2)

                UsersTimstamp = datetime.now(timezone.utc)
                # Updates last edit for timestamp ordering

                UserInfoUnProcessed = EmailTokenDict[Token]
                UserInfo = {
                    'FName' : UserInfoUnProcessed['first name'],
                    'LName' : UserInfoUnProcessed['last name'],
                    'UserName' : UserInfoUnProcessed['username'],
                    'Password' : UserInfoUnProcessed['password'],
                    'Email' : UserInfoUnProcessed['email']
                }
                del EmailTokenDict[Token]
                # Removes this token from dict and reassigns user data for easy parsing
                print(3)
                Create('Users', UserInfo)
                print(4)
                return render_template('Successful.html')
                # Parses users information from dict
                # Sends user webpage notifying that signup was a success

            else:
                del EmailTokenDict[Token]
                raise KeyError
                # Removes token from dict if timestamp ordering is failed
        
        else:
            del EmailTokenDict[Token]
            raise KeyError
            # Removes token from dict if token is expired

    except KeyError:
        return render_template('Failed.html')
    # Except state is ran when token is expired or wasnt issued
    # Except state sends user webpage notifying there was an issue with the signup


@App.route('/Login', methods = ['POST'])
def Login():
    
    JsonData = request.get_json()
    SuccessFeedback = []

    UserQuery = Session.query(Users).filter(
        ((JsonData['UN_Email'] == Users.UserName) |
        (JsonData['UN_Email'].lower() == Users.Email)) &
        (JsonData['Password'] == Users.Password)).first()
    # Checks users for one whos username and passwords match or email and passwords match

    if UserQuery:
        NewToken = token_urlsafe(16)
        TokenToUserDict[NewToken] = UserQuery.UserID
        # If such use exists, generate a token and map said token to their ID and vice versa

        return jsonify({'UserName' : UserQuery.UserName, 'Token' : NewToken})
    
    return jsonify(False)


@App.route('/Logout/<Token>', methods = ['DELETE'])
def Logout(Token):
    
    try:
        del TokenToUserDict[Token]
    except KeyError:
        None
    # KeyError occurs if someone logs into your account, changing the account token as the system tries to delete the current account token which now doesnt exist


@App.route('/Filter/<Token>', methods = ['POST'])
def Filter(Token):
    
    if VerifyToken(Token) == False:
        return jsonify(False)
    
    JsonData = request.get_json()
    PageNum = JsonData.pop('Pages')
    # Extracts pages value from dictionary as method takes it as a seperate parameter

    return jsonify(FetchFilterMazes(JsonData, TokenToUserDict[Token], PageNum))
    # Sends back json containing a list of 5 dictionaries with maze information


@App.route('/CreateRecord/<Token>', methods = ['POST'])
def CreateRecord(Token):
    
    if VerifyToken(Token) == False:
        return jsonify(False)
    
    JsonData = request.get_json()
    JsonData['Fields']['UserID'] = TokenToUserDict[Token]
    # Adds UserID to fields dict

    try:
        Create(JsonData['Table'], JsonData['Fields'])
        return jsonify(True)
    except:
        return jsonify(False)
    # Protection against any corruption to json / token in transfer or someone changing it unsolicitedly
    # Errors not specified in except statement as sqlalchemy raises many different error types when Session.commit() fails


@App.route('/Unlike/<Token>', methods = ['DELETE', 'POST'])
def Unlike(Token):
    
    if VerifyToken(Token) == False:
        return jsonify(False)
    
    JsonData = request.get_json()

    try:
        DeleteLike(TokenToUserDict[Token], JsonData['MazeID'])
        return jsonify(True)
    except:
        return jsonify(False)
    # Protection against any corruption to json / token in transfer or someone changing it unsolicitedly
    # Errors not specified in except statement as sqlalchemy raises many different error types when Session.commit() fails
    

@App.route('/FetchComments/<Token>', methods = ['POST'])
def UserComments(Token):
    
    if VerifyToken(Token) == False:
        return jsonify(False)
    
    JsonData = request.get_json()

    if JsonData['ByUser']:
        ID = TokenToUserDict[Token]
    else:
        ID = JsonData['ID']
        
    CommentsList = FetchComments(ID, JsonData['Pages'], JsonData['ByUser'])
    # Fetches relevant comments

    if JsonData['ByUser']:

        for index, CommentDict in enumerate(CommentsList):

            SingleMaze = FetchFilterMazes({'MazeID' : CommentDict['ID']}, TokenToUserDict[Token])[0]
            SingleMaze['Comment'] = CommentDict['Text']
            CommentsList[index] = SingleMaze
    # If comments are pulled from user profile, fetch the mazes linked to these comments aswell

    print(CommentsList,'Printed')
    return jsonify(CommentsList)
    

@App.route('/UserProgress/<Token>', methods = ['POST'])
def UserProgress(Token):
    
    if VerifyToken(Token) == False:
        return jsonify(False)
    
    JsonData = request.get_json()

    return FetchProgressedMazes(TokenToUserDict[Token], JsonData['Pages'])


@App.route('/AddProgress/<Token>', methods = ['POST'])
def AddProgress(Token):
    
    if VerifyToken(Token) == False:
        return jsonify(False)
    
    JsonData = request.get_json()

    try:
        ProgressTime(TokenToUserDict[Token], **JsonData)
        return jsonify(True)
        # fromisoformat() takes string created by isoformat(datetime) and converts it back into datetime Json doesnt natively support datetime objects

    except:
        return jsonify(False)
    # Protection against any corruption to json / token in transfer or someone changing it unsolicitedly
    # Errors not specified in except statement as sqlalchemy raises many different error types when Session.commit() fails


@App.errorhandler(404)
def NoPage(Error):
    return render_template('NotFound.html')



UsersTimstamp = datetime.now(timezone.utc)  #  timezone.uts to convert local time into utc
# Timestamp ordering only exists for users as no other table requires unique, user-enterable data

Gmail = SMTP_SSL('smtp.gmail.com', 465)  #  Connects to gmails port
Gmail.login('dummyemailnea@gmail.com', 'blus ofur oiys gqez')
# Python scripts arent secure so gmail requires 16 char app app password

TokenToUserDict = {}

EmailTokenDict = {}
