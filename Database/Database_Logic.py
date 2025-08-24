from Session_Modules import Session
from sqlalchemy import func, desc
from Session_Modules import Users, Mazes, Likes, Comments, Progress


TableDict = {
    'Users' : Users,
    'Mazes' : Mazes,
    'Likes' : Likes,
    'Comments' : Comments,
    'Progress' : Progress
}
# For easy translation for string passed by user device relaying which table they created a new object in User table is omitted as it only occurs in EmailAuth method and is thus hard coded

def Create(TableName, Field_Dict):
    Session.add(TableDict[TableName](**Field_Dict))
    Session.commit()
# Adds to table TableDict[TableName]
# ** parses each item in dict as a keyword argument eg **{'x' : 1} will input x = 1 into the method


def FetchFilterMazes(FilterDict, UsersID, Pages = 1):

    MazesFit = Session.query(Mazes)

    for key, value in FilterDict.items():
        if value:

            if key == 'Size':
                MazesFit = MazesFit.filter((value[0] < Mazes.SizeArea) & (Mazes.SizeArea <= value[1]))

            elif key == 'Name':
                MazesFit = MazesFit.filter(Mazes.Name == value)

            elif key == 'Algorithm':
                MazesFit = MazesFit.filter(Mazes.Algorithm == value)

            elif key == 'UserName':
                UserID = Session.query(Users).filter(Users.UserName == value).first()
                MazesFit = MazesFit.filter(Mazes.UserID == UsersID)

            else:  # By MazeID
                MazesFit = MazesFit.filter(Mazes.MazeID == value)
                break
            
    # Filters mazes by key == value (key is a field name) if value is specified by the user
    # Some exceptions with filtering by user and by size
    
    MazesFit = MazesFit.order_by(desc(Mazes.MazeID)).offset((Pages - 1) * 5).limit(5).all()
    # Takes max 5 mazes and skips some mazes depending on page number
    # Retrieves latest mazes (highest maze ID)

    MazePostList = []

    for MazeObj in MazesFit:

        ProgressQuery = Session.query(Progress).filter((Progress.MazeID == MazeObj.MazeID) & (Progress.UserID == UsersID)).first()

        MazePostList.append({
            'MazeID' : MazeObj.MazeID,
            'MazeName' : MazeObj.Name,
            'MazeList' : MazeObj.Maze,
            'UserName' : Session.get(Users, MazeObj.UserID).UserName,

            'Likes' : Session.query(func.count()).filter(Likes.MazeID == MazeObj.MazeID).scalar(),
            'Liked' : True if Session.query(func.count()).filter((Likes.MazeID == MazeObj.MazeID) & (Likes.UserID == UsersID)).scalar() else False,
            # func.count returns the line number, can use len(query) however this loads every instance of said query to memory

            'Completed' : True if ProgressQuery and ProgressQuery.Completed else False,
            'Time' : ProgressQuery.Time if ProgressQuery else 0.0
            # Must check if the query isnt empty else progressQuery.AnyField raises error
        })

    return MazePostList
# Filters max 5 mazes that match criteria
# Returns a list with elements being a dictionary containing each of the 5 mazes relevant information


def FetchComments(ID, Pages, ByUser):

    if ByUser:
        ID = Session.query(Users).filter(Users.UserID == ID).first().UserID
        CommentsQuery = Session.query(Comments).filter(Comments.UserID == ID)
    else:
        CommentsQuery = Session.query(Comments).filter(Comments.MazeID == ID)

    CommentsQuery = CommentsQuery.order_by(desc(Comments.CommentID)).offset((Pages - 1) * 5).limit(5).all()
    # Takes max 10 comments and skips some comments depending on page number
    # Retreives latest comments (highest comment ID)

    CommentsPostList = []

    for index, CommentsObj in enumerate(CommentsQuery):

        CommentsPostDict = {
            'UserName' : Session.get(Users, CommentsObj.UserID).UserName,
            'Text' : CommentsObj.Comment
        }

        if ByUser:
            CommentsPostDict['ID'] = CommentsObj.MazeID

        CommentsPostList.append(CommentsPostDict)

    return CommentsPostList
# Fetches max 5 comments from a certain maze or user
# Returns a list with elements being a dictionary containing each of the comments UserName, Text and either UserID or MazeID


def FetchProgressedMazes(UserID, Pages):

    ProgressQuery = Session.query(Progress).filter(Progress.UserID == UserID)
    ProgressQuery = ProgressQuery.order_by(Progress.Completed, Progress.Time).offset((Pages - 1) * 5).limit(5).all()
    # Queries progressed mazes for a certain user
    # Returns uncompleted progress instances with the lowest time spent first

    MazePostList = []

    for ProgressObj in ProgressQuery:
        MazePostList.append(FetchFilterMazes({'MazeID' : ProgressObj.MazeID}, UserID)[0])

    return MazePostList
    # Queries the mazes themselves and their information from the bundle of progressed mazes
# Fetches max 5 progressed mazes from a certain user
# Returns a list with elements being a dictionary containing each of the 5 mazes relevant information


def CheckTimestamp(LastEdit, LastFetch):
    if LastEdit < LastFetch:
        return True #  timezone.uts to convert local time into utc
    return False
# Timestamp ordering, approve edit if last time information was fetched > time of last edit


def ProgressTime(UserID, MazeID, Time, Completed):

    ProgressObj = Session.query(Progress).filter((Progress.UserID == UserID) & (Progress.MazeID == MazeID)).first()
    ProgressObj.Time = ProgressObj.Time + Time

    if Completed:
        ProgressObj.Completed = Completed

    Session.commit()
# Adds datetime time spent to total datatime spent for a certain user completing a certain maze
# If the maze is marked as completed, add this information to progress table


def DeleteLike(UserID, MazeID):
    LikeInstance = Session.query(Likes).filter((Likes.UserID == UserID) & (Likes.MazeID == MazeID)).first()
    Session.delete(LikeInstance)
    Session.commit()
# Deletes LikeInstance where both MazeID and UserID match



# ---------------------------- DONE ----------------------------

# Insert Users              Session.add(Users())         
# Insert Mazes              Session.add(Mazes())        
# Insert Likes              Session.add(Likes())        
# Insert Comments           Session.add(Comments())        
# Insert Progress           Session.add(Progress())

# Delete Likes              Session.delete(Like)

# Get Mazes From Filter     Session.query(Mazes).filter().offset().limit().all()
# Get UserName From Maze    Maze.User.UserName
# Get MazeList From Maze
# Get If Liked From Maze
# Get Likes From Maze       Maze.Likes
# Get if Completed From Maze
# Get Completion Time From Maze

# Get Comments From Maze    Maze.Comments.Comment
# Get UserName From Com     Comments.Users.UserName
# get UserID From Com

# Get Timestamp             Session.query(Timestamp).filter_by(TableID = '---').first()

# Update Timestamp          Timestamp.update({ LastEdit : --- })

# Update Progress           Progress.update({ Time : --- , Completed : --- })

# Get User From UserName    Session.query(Users).filter_by(UserName = '---').first()
# Get MazeName From User    User.Mazes.Name
# Get MazeList From User    User.Mazes.Maze

# Get User From UserName    Session.query(Users).filter_by(UserName = '---').first()
# Get ComStr From User      User.Comments.Comment

# Get User From UserName    Session.query(Users).filter_by(UserName = '---').first()
# Get Time From User        User.Progress.Time
# Get Maze From Progress    Progress.Mazes