from datetime import datetime, timedelta, date
from fastapi import Depends, FastAPI, HTTPException,status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from datetime import datetime, timedelta
from passlib.context import CryptContext
import secrets
from pydantic import BaseModel
from dotenv import load_dotenv
import os
from database import SessionLocal, engine
import bcrypt                                   
from fastapi.middleware.cors import CORSMiddleware

import smtplib
from email.mime.text import MIMEText


load_dotenv()

database_name=os.getenv("DB_NAME")

gmail=os.getenv("GMAIL")
gmail_password=os.getenv("GMAIL_PASSWORD")

app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:3000",  
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

connection=engine.connect()
VERSION=os.getenv("VERSION")

print("connectionn status",connection)

SECRET_KEY = "Test@123-software-engineering-3434545454"  
ALGORITHM = "HS256"  
ACCESS_TOKEN_EXPIRE_MINUTES = 30


class Token(BaseModel):
    access_token: str
    token_type: str

class User(BaseModel):
    user_id: int
    user_name: str
    email: str

class UserRegistration(BaseModel):
    user_name:str
    email:str
    password:str
    confirm_password:str
    

class UserLogin(BaseModel):
    email:str
    password:str
    
class UserDelete(BaseModel):
    email:str
    
class EventRegister(BaseModel):
    userId : int
    image:str
    eventTitle:str
    eventDescription:str
    price:str
    eventDate:str
    
class Videos(BaseModel):
    category: str 
    video_url: str
    video_title: str

    
class Appointment(BaseModel):
    user_id : int
    name: str
    email: str
    appointment_details: str
    phone_no: str
    
    
def get_user(user_id: int):
    user_query = f"SELECT * from users where user_id = {user_id}"
    user_data = connection.execute(user_query).first()
    if user_data:
        return User(**user_data)
    
# Create a token for authentication
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Initialize the password hasher
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    

@app.post(f"/api/{VERSION}/user/registration")
async def userRegistration(user_registration:UserRegistration):
    
    # print(user_registration.user_name,"username")
    # print(user_registration.email,"emaill")
    # print(user_registration.password,"password")
    if not user_registration.user_name:
        return {"status_code": 400, "message":"Please enter username"}
    
    if not user_registration.email:
        return {"status_code":  400, "message":"Please enter email address"}
    
    if not user_registration.password:
        return {"status_code": 400, "message":"Please enter password"}
    
    if not user_registration.confirm_password:
        return {"status_code":400, "message" :"Please enter confirm password"}
    
    if user_registration.password != user_registration.confirm_password:
        return {"status_code": 400, "message":"password and confirm password should be same"}
    
    query = "SELECT * from users where LOWER(user_name)=LOWER('"+user_registration.user_name+"') and email='"+user_registration.email+"'"
    # print(query,"This is query")
    check_if_email_or_username_exists = connection.execute(query)
    data_object = []
    for row in check_if_email_or_username_exists:
        data_object.append(row)
        
    # print(data_object,"this is result of query")
    if  not data_object:
        # print("need to create user here")
        password = user_registration.password.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password, salt) 
        hashed_password_str = hashed_password.decode('utf-8')
        salt_str = salt.decode('utf-8')
        # print(password,"This is entered password")
        # print(hashed_password,"This is hashed password")
        insert_query = "INSERT INTO users (user_name, email, password_hash, password_salt) VALUES ('"+ user_registration.user_name+"', '"+ user_registration.email+"', '"+hashed_password_str+"','"+salt_str+"')"
        # print("insert query",query)
        create_user = connection.execute(insert_query)
        # print(create_user,"This is create user")
        return {"status_code":200, "message":"user created successfully"}
        
    else:
        return {"status_code":400,"message":"user already exists"}



@app.post(f"/api/{VERSION}/user/login",response_model=dict)
async def userLogin(user_login:UserLogin):
    if not user_login.email:
        return {"status_code":400, "message":"please enter username/email"}
    
    if not user_login.password:
        return {"status_code":400, "message":"please enter password"}
    
    
    query = "SELECT * from users where email = '"+user_login.email +"' "
    
    # print(query,"This is query")
    
    check_email_exists = connection.execute(query)
    
    data_object=[]
    for row in check_email_exists:
        data_object.append(row)
        
    if not data_object:
        return {"status_code":400, "message":"Invalid email address"}
    
    # print(data_object,"This is data object", data_object[0])
    # print(len(data_object),"This is length of data object",type(data_object))
    
    hashed_password = data_object[0][3]
    hashed_salt = data_object[0][4]
    
    entered_password = user_login.password.encode('utf-8')
    hashed_entered_password = bcrypt.hashpw(entered_password,hashed_salt.encode('utf-8'))
    
    user_data = get_user(data_object[0][0])
    print(user_data,"this is user dataa")
    # print(hashed_entered_password,"This is  hashed entered password")
    # print(hashed_password.encode('utf-8'),"This is stored hashed password")
    if user_data:
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub":str(user_data.user_id), "user_name": user_data.user_name},
            expires_delta=access_token_expires
        )
        
    
        if hashed_entered_password == hashed_password.encode('utf-8'):
            return {"status_code":200,"user_id":data_object[0][0], "message":"Login successful","user_name":data_object[0][1],"access_token": access_token, "token_type": "bearer"}
        
        else:
            return {"status_code":400, "message":"Invalid password","access_token":"","token_type": "bearer"}
    else:
            return {"status_code":400, "message":"Invalid password"}
    

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"/api/{VERSION}/user/login")


@app.delete(f"/api/{VERSION}/user/delete")
async def userDelete(user_delete:UserDelete):
    
    if not user_delete.email:
        return {"status_code":  400, "message":"Please enter email address"}

    query = "SELECT * from users where email = '"+user_delete.email +"' "
    
    # print(query,"This is query")
    
    check_email_exists = connection.execute(query)
    
    data_object=[]
    for row in check_email_exists:
        data_object.append(row)
    
    # print(data_object,"This is data object")
    if not data_object:
        return {"status_code":400, "message":"User doesn't exists"}

    delete_query = "delete from users where email = '"+ user_delete.email+"'"
    
    delete_user = connection.execute(delete_query)
    
    return {"status_code":200,"message":"User deleted successfully"}



@app.post(f"/api/{VERSION}/event/registration")
async def eventRegistration(event_register:EventRegister):
    if not event_register.userId:
        return {"status_code":400,"message":"invalid user id"}
    
    if not event_register.image:
        return {"status_code":400,"message":"invalid image address"}
    
    if not event_register.eventTitle:
        return {"status_code":400,"message":"invalid image address"}
    
    if not event_register.eventDescription:
        return {"status_code":400,"message":"invalid image address"}
    
    if not event_register.price:
        return {"status_code":400,"message":"invalid image address"}
    
    user_query = f"SELECT * from users where user_id ={event_register.userId}"

    check_user_exists = connection.execute(user_query)
    
    user_object = []
    for row in check_user_exists:
        user_object.append(row)
    
    if not user_object:
        return {"status_code":400,"message":"user doesn't exists"}
    
    query = f"SELECT * FROM events WHERE user_id = {event_register.userId} AND event_title = '{event_register.eventTitle}'"
    

    check_event_exists = connection.execute(query)
    
    data_object = []
    for row in check_event_exists:
        data_object.append(row)
        
    if not data_object:
        fetch_user_query = f"select email from users where user_id={event_register.userId};"
        all_users = connection.execute(fetch_user_query)
        user_email=[]
        for user in all_users:
            user_email.append(user)
            
        
       
        insert_query = f"INSERT INTO events (user_id,image, event_title, event_description, price,event_date) VALUES (  {event_register.userId},'"+ event_register.image+"', '"+ event_register.eventTitle+"', '"+event_register.eventDescription+"','"+event_register.price+"','"+event_register.eventDate+"')"
        event_create = connection.execute(insert_query)
        
        
        smtp_server = smtplib.SMTP('smtp.gmail.com', 587)
        smtp_server.starttls()
        
        msg = MIMEText('We look forward to having you at the event.')
        msg['Subject'] = 'Event Registration successful'    
        msg['From'] = gmail
        msg['To'] = user_email[0][0]
        smtp_server.login(gmail, gmail_password)
        smtp_server.sendmail(gmail, user_email[0][0], msg.as_string())
        
        smtp_server.quit()
        return {"status_code":200, "message":"event registerd successfully"}
    
    else:
        return {"status_code":400,"message":"user already registerd"}
    
    

@app.get("/events/{user_id}")
async def getEventDetails(user_id:int, token: str = Depends(oauth2_scheme)):
    user_query = f"SELECT * from users where user_id ={user_id}"
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id_in_token = payload.get("sub")
        if str(user_id) != user_id_in_token:
            return {"status_code":403,"message":"Not authorized"}
    except JWTError:
        return {"status_code":403,"message":"Not authorized"}


    check_user_exists = connection.execute(user_query)
    
    user_object = []
    for row in check_user_exists:
        user_object.append(row)
    
    if not user_object:
        return {"status_code":400,"message":"user doesn't exists"}
    
    query = f"SELECT * FROM events WHERE user_id = {user_id}"
    events =connection.execute(query).fetchall()
    return events
    
    
    
@app.post(f"/api/{VERSION}/selfhelp/videos")
async def selfHelpVideos(self_help_videos: Videos):
    
    
    
    if not self_help_videos.video_url:
        return { "status_code ": 400, "message":"video url is missing"}

    if not self_help_videos.video_title:
        return {"status_code":400, "message":"video title is missing"}
    
    
    if not self_help_videos.category:
        return {"status_code":400, "message":"category is missing"}
    
    
    check_if_video_exists_query = f"SELECT * from videos where video_url ='{self_help_videos.video_url}' and video_title='{self_help_videos.video_title}' "
    
    check_video_exists =  connection.execute(check_if_video_exists_query)
    
    video_object = []
    
    for row in check_video_exists:
        video_object.append(row)
        
    if  len(video_object) > 0 :
        return {"status_code":400, "message":"video already uploaded"}
    
    
    insert_video_query = f"INSERT INTO videos(category, video_type, video_url, video_title) values ('{self_help_videos.category}','selfhelp','{self_help_videos.video_url}','{self_help_videos.video_title}')"
    
    create_video = connection.execute(insert_video_query)
    
    return {"status_code":200, "message":"video inserted successfully"} 



@app.get("/api/{VERSION}/{category_type}/videos")
async def getSelfHelpVideos(category_type: str):
    
    query = f"SELECT * from videos where video_type = '{category_type}'"
    selfHelpVideos=connection.execute(query).fetchall()
    return selfHelpVideos

  



@app.post(f"/api/{VERSION}/appointments")
async def appointmentBooking(appointment: Appointment):
    
    if not appointment.user_id:
        return {"status_code":400, "message":"user id is missing "}
    
    if not appointment.name :
        return {"status_code":400, "message":"name is missing"}
    
    if not appointment.email :
        return {"status_code":400, "message":"email is missing "}
    
    if not appointment.appointment_details :
        return {"status_code":400, "message":"appointment details are missing"}
    
    if not appointment.phone_no :
        return {"status_code":400, "message":"phone number is missing "}
    
    
    user_query = f"SELECT * from users where user_id ={appointment.user_id}"

    check_user_exists = connection.execute(user_query)
    
    user_object = []
    for row in check_user_exists:
        user_object.append(row)
    
    if not user_object:
        return {"status_code":400,"message":"user doesn't exists"}
    
    
    
    check_if_appointment_exists = f"SELECT * from appointments where user_id = '{appointment.user_id}' and appointment_details = '{appointment.appointment_details}'"
    
    check_exists = connection.execute(check_if_appointment_exists)
    
    appointment_exists = []
    
    for row in check_exists:
        appointment_exists.append(row)
        
    if len(appointment_exists) > 0:
        return {"status_code":400, "message":"already booked "}
    
    
    insert_query = f"INSERT INTO appointments(user_id, name, email, appointment_details, phone_no) values('{appointment.user_id}','{appointment.name}','{appointment.email}','{appointment.appointment_details}','{appointment.phone_no}')"
    
    
    insertion = connection.execute(insert_query)
    
    return {"status_code":200, "message":"appointment booked successfully"}
    
    

from datetime import datetime, timedelta, date
from datetime import datetime, timedelta, date
from fastapi import Depends, FastAPI, HTTPException,status
from fastapi import Depends, FastAPI, HTTPException,status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi import Request, HTTPException
from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from jose import JWTError, jwt
from datetime import datetime, timedelta
from datetime import datetime, timedelta
from passlib.context import CryptContext
from passlib.context import CryptContext
import secrets
import secrets
from pydantic import BaseModel
from pydantic import BaseModel
from dotenv import load_dotenv
from dotenv import load_dotenv
import os
import os
from database import SessionLocal, engine
from database import SessionLocal, engine
import bcrypt                                  
import bcrypt                                  
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.cors import CORSMiddleware
import smtplib
import smtplib
from email.mime.text import MIMEText
from email.mime.text import MIMEText
load_dotenv()
load_dotenv()
database_name=os.getenv("DB_NAME")
database_name=os.getenv("DB_NAME")
gmail=os.getenv("GMAIL")
gmail=os.getenv("GMAIL")
gmail_password=os.getenv("GMAIL_PASSWORD")
gmail_password=os.getenv("GMAIL_PASSWORD")
app = FastAPI()
app = FastAPI()
origins = [
origins = [
    "http://localhost",
    "http://localhost",
    "http://localhost:3000",  
    "http://localhost:3000",  
    "*",
    "*",
]
]
app.add_middleware(
app.add_middleware(
    CORSMiddleware,
    CORSMiddleware,
    allow_origins=origins,
    allow_origins=origins,
    allow_credentials=True,
    allow_credentials=True,
    allow_methods=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_headers=["*"],
)
)
connection=engine.connect()
connection=engine.connect()
VERSION=os.getenv("VERSION")
VERSION=os.getenv("VERSION")
print("connectionn status",connection)
print("connectionn status",connection)
SECRET_KEY = "Test@123-software-engineering-3434545454"  
SECRET_KEY = "Test@123-software-engineering-3434545454"  
ALGORITHM = "HS256"  
ALGORITHM = "HS256"  
ACCESS_TOKEN_EXPIRE_MINUTES = 30
ACCESS_TOKEN_EXPIRE_MINUTES = 30
class Token(BaseModel):
class Token(BaseModel):
    access_token: str
    access_token: str
    token_type: str
    token_type: str
class User(BaseModel):
class User(BaseModel):
    user_id: int
    user_id: int
    user_name: str
    user_name: str
    email: str
    email: str
class UserRegistration(BaseModel):
class UserRegistration(BaseModel):
    user_name:str
    user_name:str
    email:str
    email:str
    password:str
    password:str
    confirm_password:str
    confirm_password:str
    
    
class UserLogin(BaseModel):
class UserLogin(BaseModel):
    email:str
    email:str
    password:str
    password:str
    
    
class UserDelete(BaseModel):
class UserDelete(BaseModel):
    email:str
    email:str
    
    
class EventRegister(BaseModel):
class EventRegister(BaseModel):
    userId : int
    userId : int
    image:str
    image:str
    eventTitle:str
    eventTitle:str
    eventDescription:str
    eventDescription:str
    price:str
    price:str
    eventDate:str
    eventDate:str
    
    
class Videos(BaseModel):
class Videos(BaseModel):
    category: str
    category: str
    video_url: str
    video_url: str
    video_title: str
    video_title: str
    
    
class Appointment(BaseModel):
class Appointment(BaseModel):
    user_id : int
    user_id : int
    name: str
    name: str
    email: str
    email: str
    appointment_details: str
    appointment_details: str
    phone_no: str
    phone_no: str
    
    
    
    
def get_user(user_id: int):
def get_user(user_id: int):
    user_query = f"SELECT * from users where user_id = {user_id}"
    user_query = f"SELECT * from users where user_id = {user_id}"
    user_data = connection.execute(user_query).first()
    user_data = connection.execute(user_query).first()
    if user_data:
    if user_data:
        return User(**user_data)
        return User(**user_data)
    
    
# Create a token for authentication
# Create a token for authentication
def create_access_token(data: dict, expires_delta: timedelta = None):
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    to_encode = data.copy()
    if expires_delta:
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
        expire = datetime.utcnow() + expires_delta
    else:
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
    return encoded_jwt
# Initialize the password hasher
# Initialize the password hasher
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    
@app.post(f"/api/{VERSION}/user/registration")
@app.post(f"/api/{VERSION}/user/registration")
async def userRegistration(user_registration:UserRegistration):
async def userRegistration(user_registration:UserRegistration):
    
    
    # print(user_registration.user_name,"username")
    # print(user_registration.user_name,"username")
    # print(user_registration.email,"emaill")
    # print(user_registration.email,"emaill")
    # print(user_registration.password,"password")
    # print(user_registration.password,"password")
    if not user_registration.user_name:
    if not user_registration.user_name:
        return {"status_code": 400, "message":"Please enter username"}
        return {"status_code": 400, "message":"Please enter username"}
    
    
    if not user_registration.email:
    if not user_registration.email:
        return {"status_code":  400, "message":"Please enter email address"}
        return {"status_code":  400, "message":"Please enter email address"}
    
    
    if not user_registration.password:
    if not user_registration.password:
        return {"status_code": 400, "message":"Please enter password"}
        return {"status_code": 400, "message":"Please enter password"}
    
    
    if not user_registration.confirm_password:
    if not user_registration.confirm_password:
        return {"status_code":400, "message" :"Please enter confirm password"}
        return {"status_code":400, "message" :"Please enter confirm password"}
    
    
    if user_registration.password != user_registration.confirm_password:
    if user_registration.password != user_registration.confirm_password:
        return {"status_code": 400, "message":"password and confirm password should be same"}
        return {"status_code": 400, "message":"password and confirm password should be same"}
    
    
    query = "SELECT * from users where LOWER(user_name)=LOWER('"+user_registration.user_name+"') and email='"+user_registration.email+"'"
    query = "SELECT * from users where LOWER(user_name)=LOWER('"+user_registration.user_name+"') and email='"+user_registration.email+"'"
    # print(query,"This is query")
    # print(query,"This is query")
    check_if_email_or_username_exists = connection.execute(query)
    check_if_email_or_username_exists = connection.execute(query)
    data_object = []
    data_object = []
    for row in check_if_email_or_username_exists:
    for row in check_if_email_or_username_exists:
        data_object.append(row)
        data_object.append(row)
        
        
    # print(data_object,"this is result of query")
    # print(data_object,"this is result of query")
    if  not data_object:
    if  not data_object:
        # print("need to create user here")
        # print("need to create user here")
        password = user_registration.password.encode('utf-8')
        password = user_registration.password.encode('utf-8')
        salt = bcrypt.gensalt()
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password, salt)
        hashed_password = bcrypt.hashpw(password, salt)
        hashed_password_str = hashed_password.decode('utf-8')
        hashed_password_str = hashed_password.decode('utf-8')
        salt_str = salt.decode('utf-8')
        salt_str = salt.decode('utf-8')
        # print(password,"This is entered password")
        # print(password,"This is entered password")
        # print(hashed_password,"This is hashed password")
        # print(hashed_password,"This is hashed password")
        insert_query = "INSERT INTO users (user_name, email, password_hash, password_salt) VALUES ('"+ user_registration.user_name+"', '"+ user_registration.email+"', '"+hashed_password_str+"','"+salt_str+"')"
        insert_query = "INSERT INTO users (user_name, email, password_hash, password_salt) VALUES ('"+ user_registration.user_name+"', '"+ user_registration.email+"', '"+hashed_password_str+"','"+salt_str+"')"
        # print("insert query",query)
        # print("insert query",query)
        create_user = connection.execute(insert_query)
        create_user = connection.execute(insert_query)
        # print(create_user,"This is create user")
        # print(create_user,"This is create user")
        return {"status_code":200, "message":"user created successfully"}
        return {"status_code":200, "message":"user created successfully"}
        
        
    else:
    else:
        return {"status_code":400,"message":"user already exists"}
        return {"status_code":400,"message":"user already exists"}
@app.post(f"/api/{VERSION}/user/login",response_model=dict)
@app.post(f"/api/{VERSION}/user/login",response_model=dict)
async def userLogin(user_login:UserLogin):
async def userLogin(user_login:UserLogin):
    if not user_login.email:
    if not user_login.email:
        return {"status_code":400, "message":"please enter username/email"}
        return {"status_code":400, "message":"please enter username/email"}
    
    
    if not user_login.password:
    if not user_login.password:
        return {"status_code":400, "message":"please enter password"}
        return {"status_code":400, "message":"please enter password"}
    
    
    
    
    query = "SELECT * from users where email = '"+user_login.email +"' "
    query = "SELECT * from users where email = '"+user_login.email +"' "
    
    
    # print(query,"This is query")
    # print(query,"This is query")
    
    
    check_email_exists = connection.execute(query)
    check_email_exists = connection.execute(query)
    
    
    data_object=[]
    data_object=[]
    for row in check_email_exists:
    for row in check_email_exists:
        data_object.append(row)
        data_object.append(row)
        
        
    if not data_object:
    if not data_object:
        return {"status_code":400, "message":"Invalid email address"}
        return {"status_code":400, "message":"Invalid email address"}
    
    
    # print(data_object,"This is data object", data_object[0])
    # print(data_object,"This is data object", data_object[0])
    # print(len(data_object),"This is length of data object",type(data_object))
    # print(len(data_object),"This is length of data object",type(data_object))
    
    
    hashed_password = data_object[0][3]
    hashed_password = data_object[0][3]
    hashed_salt = data_object[0][4]
    hashed_salt = data_object[0][4]
    
    
    entered_password = user_login.password.encode('utf-8')
    entered_password = user_login.password.encode('utf-8')
    hashed_entered_password = bcrypt.hashpw(entered_password,hashed_salt.encode('utf-8'))
    hashed_entered_password = bcrypt.hashpw(entered_password,hashed_salt.encode('utf-8'))
    
    
    user_data = get_user(data_object[0][0])
    user_data = get_user(data_object[0][0])
    print(user_data,"this is user dataa")
    print(user_data,"this is user dataa")
    # print(hashed_entered_password,"This is  hashed entered password")
    # print(hashed_entered_password,"This is  hashed entered password")
    # print(hashed_password.encode('utf-8'),"This is stored hashed password")
    # print(hashed_password.encode('utf-8'),"This is stored hashed password")
    if user_data:
    if user_data:
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
        access_token = create_access_token(
            data={"sub":str(user_data.user_id), "user_name": user_data.user_name},
            data={"sub":str(user_data.user_id), "user_name": user_data.user_name},
            expires_delta=access_token_expires
            expires_delta=access_token_expires
        )
        )
        
        
    
    
        if hashed_entered_password == hashed_password.encode('utf-8'):
        if hashed_entered_password == hashed_password.encode('utf-8'):
            return {"status_code":200,"user_id":data_object[0][0], "message":"Login successful","user_name":data_object[0][1],"access_token": access_token, "token_type": "bearer"}
            return {"status_code":200,"user_id":data_object[0][0], "message":"Login successful","user_name":data_object[0][1],"access_token": access_token, "token_type": "bearer"}
        
        
        else:
        else:
            return {"status_code":400, "message":"Invalid password","access_token":"","token_type": "bearer"}
            return {"status_code":400, "message":"Invalid password","access_token":"","token_type": "bearer"}
    else:
    else:
            return {"status_code":400, "message":"Invalid password"}
            return {"status_code":400, "message":"Invalid password"}
    
    
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"/api/{VERSION}/user/login")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"/api/{VERSION}/user/login")
@app.delete(f"/api/{VERSION}/user/delete")
@app.delete(f"/api/{VERSION}/user/delete")
async def userDelete(user_delete:UserDelete):
async def userDelete(user_delete:UserDelete):
    
    
    if not user_delete.email:
    if not user_delete.email:
        return {"status_code":  400, "message":"Please enter email address"}
        return {"status_code":  400, "message":"Please enter email address"}
    query = "SELECT * from users where email = '"+user_delete.email +"' "
    query = "SELECT * from users where email = '"+user_delete.email +"' "
    
    
    # print(query,"This is query")
    # print(query,"This is query")
    
    
    check_email_exists = connection.execute(query)
    check_email_exists = connection.execute(query)
    
    
    data_object=[]
    data_object=[]
    for row in check_email_exists:
    for row in check_email_exists:
        data_object.append(row)
        data_object.append(row)
    
    
    # print(data_object,"This is data object")
    # print(data_object,"This is data object")
    if not data_object:
    if not data_object:
        return {"status_code":400, "message":"User doesn't exists"}
        return {"status_code":400, "message":"User doesn't exists"}
    delete_query = "delete from users where email = '"+ user_delete.email+"'"
    delete_query = "delete from users where email = '"+ user_delete.email+"'"
    
    
    delete_user = connection.execute(delete_query)
    delete_user = connection.execute(delete_query)
    
    
    return {"status_code":200,"message":"User deleted successfully"}
    return {"status_code":200,"message":"User deleted successfully"}
@app.post(f"/api/{VERSION}/event/registration")
@app.post(f"/api/{VERSION}/event/registration")
async def eventRegistration(event_register:EventRegister):
async def eventRegistration(event_register:EventRegister):
    if not event_register.userId:
    if not event_register.userId:
        return {"status_code":400,"message":"invalid user id"}
        return {"status_code":400,"message":"invalid user id"}
    
    
    if not event_register.image:
    if not event_register.image:
        return {"status_code":400,"message":"invalid image address"}
        return {"status_code":400,"message":"invalid image address"}
    
    
    if not event_register.eventTitle:
    if not event_register.eventTitle:
        return {"status_code":400,"message":"invalid image address"}
        return {"status_code":400,"message":"invalid image address"}
    
    
    if not event_register.eventDescription:
    if not event_register.eventDescription:
        return {"status_code":400,"message":"invalid image address"}
        return {"status_code":400,"message":"invalid image address"}
    
    
    if not event_register.price:
    if not event_register.price:
        return {"status_code":400,"message":"invalid image address"}
        return {"status_code":400,"message":"invalid image address"}
    
    
    user_query = f"SELECT * from users where user_id ={event_register.userId}"
    user_query = f"SELECT * from users where user_id ={event_register.userId}"
    check_user_exists = connection.execute(user_query)
    check_user_exists = connection.execute(user_query)
    
    
    user_object = []
    user_object = []
    for row in check_user_exists:
    for row in check_user_exists:
        user_object.append(row)
        user_object.append(row)
    
    
    if not user_object:
    if not user_object:
        return {"status_code":400,"message":"user doesn't exists"}
        return {"status_code":400,"message":"user doesn't exists"}
    
    
    query = f"SELECT * FROM events WHERE user_id = {event_register.userId} AND event_title = '{event_register.eventTitle}'"
    query = f"SELECT * FROM events WHERE user_id = {event_register.userId} AND event_title = '{event_register.eventTitle}'"
    
    
    check_event_exists = connection.execute(query)
    check_event_exists = connection.execute(query)
    
    
    data_object = []
    data_object = []
    for row in check_event_exists:
    for row in check_event_exists:
        data_object.append(row)
        data_object.append(row)
        
        
    if not data_object:
    if not data_object:
        fetch_user_query = f"select email from users where user_id={event_register.userId};"
        fetch_user_query = f"select email from users where user_id={event_register.userId};"
        all_users = connection.execute(fetch_user_query)
        all_users = connection.execute(fetch_user_query)
        user_email=[]
        user_email=[]
        for user in all_users:
        for user in all_users:
            user_email.append(user)
            user_email.append(user)
            
            
        
        
      
      
        insert_query = f"INSERT INTO events (user_id,image, event_title, event_description, price,event_date) VALUES (  {event_register.userId},'"+ event_register.image+"', '"+ event_register.eventTitle+"', '"+event_register.eventDescription+"','"+event_register.price+"','"+event_register.eventDate+"')"
        insert_query = f"INSERT INTO events (user_id,image, event_title, event_description, price,event_date) VALUES (  {event_register.userId},'"+ event_register.image+"', '"+ event_register.eventTitle+"', '"+event_register.eventDescription+"','"+event_register.price+"','"+event_register.eventDate+"')"
        event_create = connection.execute(insert_query)
        event_create = connection.execute(insert_query)
        
        
        
        
        smtp_server = smtplib.SMTP('smtp.gmail.com', 587)
        smtp_server = smtplib.SMTP('smtp.gmail.com', 587)
        smtp_server.starttls()
        smtp_server.starttls()
        
        
        msg = MIMEText('We look forward to having you at the event.')
        msg = MIMEText('We look forward to having you at the event.')
        msg['Subject'] = 'Event Registration successful'    
        msg['Subject'] = 'Event Registration successful'    
        msg['From'] = gmail
        msg['From'] = gmail
        msg['To'] = user_email[0][0]
        msg['To'] = user_email[0][0]
        smtp_server.login(gmail, gmail_password)
        smtp_server.login(gmail, gmail_password)
        smtp_server.sendmail(gmail, user_email[0][0], msg.as_string())
        smtp_server.sendmail(gmail, user_email[0][0], msg.as_string())
        
        
        smtp_server.quit()
        smtp_server.quit()
        return {"status_code":200, "message":"event registerd successfully"}
        return {"status_code":200, "message":"event registerd successfully"}
    
    
    else:
    else:
        return {"status_code":400,"message":"user already registerd"}
        return {"status_code":400,"message":"user already registerd"}
    
    
    
    
@app.get("/events/{user_id}")
@app.get("/events/{user_id}")
async def getEventDetails(user_id:int, token: str = Depends(oauth2_scheme)):
async def getEventDetails(user_id:int, token: str = Depends(oauth2_scheme)):
    user_query = f"SELECT * from users where user_id ={user_id}"
    user_query = f"SELECT * from users where user_id ={user_id}"
    try:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id_in_token = payload.get("sub")
        user_id_in_token = payload.get("sub")
        if str(user_id) != user_id_in_token:
        if str(user_id) != user_id_in_token:
            return {"status_code":403,"message":"Not authorized"}
            return {"status_code":403,"message":"Not authorized"}
    except JWTError:
    except JWTError:
        return {"status_code":403,"message":"Not authorized"}
        return {"status_code":403,"message":"Not authorized"}
    check_user_exists = connection.execute(user_query)
    check_user_exists = connection.execute(user_query)
    
    
    user_object = []
    user_object = []
    for row in check_user_exists:
    for row in check_user_exists:
        user_object.append(row)
        user_object.append(row)
    
    
    if not user_object:
    if not user_object:
        return {"status_code":400,"message":"user doesn't exists"}
        return {"status_code":400,"message":"user doesn't exists"}
    
    
    query = f"SELECT * FROM events WHERE user_id = {user_id}"
    query = f"SELECT * FROM events WHERE user_id = {user_id}"
    events =connection.execute(query).fetchall()
    events =connection.execute(query).fetchall()
    return events
    return events
    
    
    
    
    
    
@app.post(f"/api/{VERSION}/selfhelp/videos")
@app.post(f"/api/{VERSION}/selfhelp/videos")
async def selfHelpVideos(self_help_videos: Videos):
async def selfHelpVideos(self_help_videos: Videos):
    
    
    
    
    
    
    if not self_help_videos.video_url:
    if not self_help_videos.video_url:
        return { "status_code ": 400, "message":"video url is missing"}
        return { "status_code ": 400, "message":"video url is missing"}
    if not self_help_videos.video_title:
    if not self_help_videos.video_title:
        return {"status_code":400, "message":"video title is missing"}
        return {"status_code":400, "message":"video title is missing"}
    
    
    
    
    if not self_help_videos.category:
    if not self_help_videos.category:
        return {"status_code":400, "message":"category is missing"}
        return {"status_code":400, "message":"category is missing"}
    
    
    
    
    check_if_video_exists_query = f"SELECT * from videos where video_url ='{self_help_videos.video_url}' and video_title='{self_help_videos.video_title}' "
    check_if_video_exists_query = f"SELECT * from videos where video_url ='{self_help_videos.video_url}' and video_title='{self_help_videos.video_title}' "
    
    
    check_video_exists =  connection.execute(check_if_video_exists_query)
    check_video_exists =  connection.execute(check_if_video_exists_query)
    
    
    video_object = []
    video_object = []
    
    
    for row in check_video_exists:
    for row in check_video_exists:
        video_object.append(row)
        video_object.append(row)
        
        
    if  len(video_object) > 0 :
    if  len(video_object) > 0 :
        return {"status_code":400, "message":"video already uploaded"}
        return {"status_code":400, "message":"video already uploaded"}
    
    
    
    
    insert_video_query = f"INSERT INTO videos(category, video_type, video_url, video_title) values ('{self_help_videos.category}','selfhelp','{self_help_videos.video_url}','{self_help_videos.video_title}')"
    insert_video_query = f"INSERT INTO videos(category, video_type, video_url, video_title) values ('{self_help_videos.category}','selfhelp','{self_help_videos.video_url}','{self_help_videos.video_title}')"
    
    
    create_video = connection.execute(insert_video_query)
    create_video = connection.execute(insert_video_query)
    
    
    return {"status_code":200, "message":"video inserted successfully"}
    return {"status_code":200, "message":"video inserted successfully"}
@app.get("/api/{VERSION}/{category_type}/videos")
@app.get("/api/{VERSION}/{category_type}/videos")
async def getSelfHelpVideos(category_type: str):
async def getSelfHelpVideos(category_type: str):
    
    
    query = f"SELECT * from videos where video_type = '{category_type}'"
    query = f"SELECT * from videos where video_type = '{category_type}'"
    selfHelpVideos=connection.execute(query).fetchall()
    selfHelpVideos=connection.execute(query).fetchall()
    return selfHelpVideos
    return selfHelpVideos
  
  
@app.post(f"/api/{VERSION}/articles/videos")
async def selfHelpVideos(self_help_videos: Videos):
    
    
    
    if not self_help_videos.video_url:
        return { "status_code ": 400, "message":"video url is missing"}
    if not self_help_videos.video_title:
        return {"status_code":400, "message":"video title is missing"}
    
    
    if not self_help_videos.category:
        return {"status_code":400, "message":"category is missing"}
    
    
    check_if_video_exists_query = f"SELECT * from videos where video_url ='{self_help_videos.video_url}' and video_title='{self_help_videos.video_title}' "
    
    check_video_exists =  connection.execute(check_if_video_exists_query)
    
    video_object = []
    
    for row in check_video_exists:
        video_object.append(row)
        
    if  len(video_object) > 0 :
        return {"status_code":400, "message":"video already uploaded"}
    
    
    insert_video_query = f"INSERT INTO videos(category, video_type, video_url, video_title) values ('{self_help_videos.category}','articles','{self_help_videos.video_url}','{self_help_videos.video_title}')"
    
    create_video = connection.execute(insert_video_query)
    
    return {"status_code":200, "message":"video inserted successfully"}
@app.post(f"/api/{VERSION}/appointments")
@app.post(f"/api/{VERSION}/appointments")
async def appointmentBooking(appointment: Appointment):
async def appointmentBooking(appointment: Appointment):
    
    
    if not appointment.user_id:
    if not appointment.user_id:
        return {"status_code":400, "message":"user id is missing "}
        return {"status_code":400, "message":"user id is missing "}
    
    
    if not appointment.name :
    if not appointment.name :
        return {"status_code":400, "message":"name is missing"}
        return {"status_code":400, "message":"name is missing"}
    
    
    if not appointment.email :
    if not appointment.email :
        return {"status_code":400, "message":"email is missing "}
        return {"status_code":400, "message":"email is missing "}
    
    
    if not appointment.appointment_details :
    if not appointment.appointment_details :
        return {"status_code":400, "message":"appointment details are missing"}
        return {"status_code":400, "message":"appointment details are missing"}
    
    
    if not appointment.phone_no :
    if not appointment.phone_no :
        return {"status_code":400, "message":"phone number is missing "}
        return {"status_code":400, "message":"phone number is missing "}
    
    
    
    
    user_query = f"SELECT * from users where user_id ={appointment.user_id}"
    user_query = f"SELECT * from users where user_id ={appointment.user_id}"
    check_user_exists = connection.execute(user_query)
    check_user_exists = connection.execute(user_query)
    
    
    user_object = []
    user_object = []
    for row in check_user_exists:
    for row in check_user_exists:
        user_object.append(row)
        user_object.append(row)
    
    
    if not user_object:
    if not user_object:
        return {"status_code":400,"message":"user doesn't exists"}
        return {"status_code":400,"message":"user doesn't exists"}
    
    
    
    
    
    
    check_if_appointment_exists = f"SELECT * from appointments where user_id = '{appointment.user_id}' and appointment_details = '{appointment.appointment_details}'"
    check_if_appointment_exists = f"SELECT * from appointments where user_id = '{appointment.user_id}' and appointment_details = '{appointment.appointment_details}'"
    
    
    check_exists = connection.execute(check_if_appointment_exists)
    check_exists = connection.execute(check_if_appointment_exists)
    
    
    appointment_exists = []
    appointment_exists = []
    
    
    for row in check_exists:
    for row in check_exists:
        appointment_exists.append(row)
        appointment_exists.append(row)
        
        
    if len(appointment_exists) > 0:
    if len(appointment_exists) > 0:
        return {"status_code":400, "message":"already booked "}
        return {"status_code":400, "message":"already booked "}
    
    
    
    
    insert_query = f"INSERT INTO appointments(user_id, name, email, appointment_details, phone_no) values('{appointment.user_id}','{appointment.name}','{appointment.email}','{appointment.appointment_details}','{appointment.phone_no}')"
    insert_query = f"INSERT INTO appointments(user_id, name, email, appointment_details, phone_no) values('{appointment.user_id}','{appointment.name}','{appointment.email}','{appointment.appointment_details}','{appointment.phone_no}')"
    
    
    
    
    insertion = connection.execute(insert_query)
    insertion = connection.execute(insert_query)
    
    
    return {"status_code":200, "message":"appointment booked successfully"}
    return {"status_code":200, "message":"appointment booked successfully"}
    

  
@app.post(f"/api/{VERSION}/articles/videos")
async def selfHelpVideos(self_help_videos: Videos):
    
    
    
    if not self_help_videos.video_url:
        return { "status_code ": 400, "message":"video url is missing"}
    if not self_help_videos.video_title:
        return {"status_code":400, "message":"video title is missing"}
    
    
    if not self_help_videos.category:
        return {"status_code":400, "message":"category is missing"}
    
    
    check_if_video_exists_query = f"SELECT * from videos where video_url ='{self_help_videos.video_url}' and video_title='{self_help_videos.video_title}' "
    
    check_video_exists =  connection.execute(check_if_video_exists_query)
    
    video_object = []
    
    for row in check_video_exists:
        video_object.append(row)
        
    if  len(video_object) > 0 :
        return {"status_code":400, "message":"video already uploaded"}
    
    
    insert_video_query = f"INSERT INTO videos(category, video_type, video_url, video_title) values ('{self_help_videos.category}','articles','{self_help_videos.video_url}','{self_help_videos.video_title}')"
    
    create_video = connection.execute(insert_video_query)
    
    return {"status_code":200, "message":"video inserted successfully"}
    
    
    
    
@app.get("/api/{VERSION}/appointments/{user_id}")
async def getAppointments(user_id: int, token: str = Depends(oauth2_scheme)):
    user_query = f"SELECT * from users where user_id ={user_id}"
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id_in_token = payload.get("sub")
        if str(user_id) != user_id_in_token:
            return {"status_code":403,"message":"Not authorized"}
    except JWTError:
        return {"status_code":403,"message":"Not authorized"}
    check_user_exists = connection.execute(user_query)
    
    user_object = []
    for row in check_user_exists:
        user_object.append(row)
    
    if not user_object:
        return {"status_code":400,"message":"user doesn't exists"}
    
    
    query = f"SELECT * FROM appointments WHERE user_id = {user_id}"
    appointments =connection.execute(query).fetchall()
    return appointments
    