from datetime import datetime, timedelta, date
from fastapi import Depends, FastAPI, HTTPException,status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import secrets
from pydantic import BaseModel
from dotenv import load_dotenv
import os
from database import SessionLocal, engine
import bcrypt


load_dotenv()

database_name=os.getenv("DB_NAME")
print(database_name,"database name")

app = FastAPI()
connection=engine.connect()
VERSION=os.getenv("VERSION")

print("connectionn status",connection)


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



@app.post(f"/api/{VERSION}/user/login")
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
    
    
    # print(hashed_entered_password,"This is  hashed entered password")
    # print(hashed_password.encode('utf-8'),"This is stored hashed password")
    
    if hashed_entered_password == hashed_password.encode('utf-8'):
        return {"status_code":200, "message":"Login successful"}
    
    else:
        return {"status_code":400, "message":"Invalid password"}


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