from sqlalchemy import create_engine, Column, ForeignKey, Integer, String, Boolean, Text, Float
from sqlalchemy.orm import declarative_base, sessionmaker


engine = create_engine('sqlite:///Database/MazeDatabase.db')
# Creates connection to database file usign SQLite

Base = declarative_base()
# Creates a default table class for custom tables to inherit from

class Users(Base):
    __tablename__ = 'Users'

    UserID = Column(Integer, primary_key = True, autoincrement = True)
    # Acts as primary key even though UserName is unique as it is smaller (faster query) and allows future functionality of changing UserName easier to implement

    FName = Column(String(20))
    LName = Column(String(20))
    UserName = Column(String(20))  # Max 20 char length for strings entered
    Password = Column(String(20))
    Email = Column(String(254))  # 254 characters is the maximum possible email length

class Mazes(Base):
    __tablename__ = 'Mazes'

    MazeID = Column(Integer, primary_key = True, autoincrement = True)
    UserID = Column(Integer, ForeignKey('Users.UserID'))  # Foreign key for UserID
    Name = Column(String(20))  # Max 20 char length for strings entered
    SizeArea = Column(Integer)
    Algorithm = Column(String(11)) # 'Backtracker' is longest and 11 char
    Maze = Column(Text)  # Stores JSON text describing the nested list information

class Likes(Base):
    __tablename__ = 'Likes'

    UserID = Column(Integer, ForeignKey('Users.UserID'), primary_key = True)  # Both keys double as foreign keys and composite primary keys
    MazeID = Column(Integer, ForeignKey('Mazes.MazeID'), primary_key = True)

class Comments(Base):
    __tablename__ = 'Comments'

    CommentID = Column(Integer, primary_key = True, autoincrement = True)
    UserID = Column(Integer, ForeignKey('Users.UserID'))  # Foreign key for UserID
    MazeID = Column(Integer, ForeignKey('Mazes.MazeID'))  # Foreign key for MazeID
    Comment = Column(String(150))

class Progress(Base):
    __tablename__ = 'Progress'

    UserID = Column(Integer, ForeignKey('Users.UserID'), primary_key = True)  # Both keys double as foreign keys and composite primary keys
    MazeID = Column(Integer, ForeignKey('Mazes.MazeID'), primary_key = True)
    Time = Column(Float)
    Completed = Column(Boolean)

Base.metadata.create_all(engine)
# Maps created classes to tables

session = sessionmaker(engine)
Session = session()
# Creates session blueprint and instance allowing interaction with database