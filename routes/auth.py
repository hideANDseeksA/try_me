from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException,Form
from database import get_db
from models.schema import CreateUserRequest, LoginRequest,admin,verificationRequest,UpdateUserRequest
from email_utils import send_email
import bcrypt, random, logging
from datetime import datetime, timedelta
import jwt
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()
JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM")

router = APIRouter()

@router.post("/api/create_user")
async def create_user(user: CreateUserRequest, background_tasks: BackgroundTasks, db=Depends(get_db)):
    try:
        code = random.randint(100000, 999999)
        hashed_pw = bcrypt.hashpw(user.password.encode(), bcrypt.gensalt()).decode()

        await db.execute(
            "INSERT INTO accounts (student_id, email, password, code) VALUES ($1, $2, $3, $4)",
            user.student_id, user.email, hashed_pw, code
        )

        subject = "Verify Your Mabini EasyDocs Account"
        text_body = f"Your verification code is: {code}"
        html_body = f"""<div style='text-align: center; font-family: Arial;'>
            <h2>Mabini EasyDocs</h2>
            <p>Your verification code is:</p><h2>{code}</h2>
            <p>Please enter this code to verify your account.</p></div>"""

        background_tasks.add_task(send_email, user.email, subject, text_body, html_body)
        return {"message": "User created. Verification code sent."}

    except asyncpg.exceptions.UniqueViolationError as e:
        logging.warning(f"⚠️ Duplicate entry: {e}")
        raise HTTPException(status_code=400, detail="Student ID or Email already exists.")
    
    except Exception as e:
        logging.error(f"❌ Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.post("/api/login")
async def login(user: LoginRequest, db=Depends(get_db)):
    try:
        db_user = await db.fetchrow(
            "SELECT student_id, email, password, verification_status FROM accounts WHERE email = $1",
            user.email
        )

        if not db_user or not bcrypt.checkpw(user.password.encode(), db_user["password"].encode()):
            raise HTTPException(status_code=400, detail="Invalid email or password")

        if not db_user["verification_status"]:
            raise HTTPException(status_code=403, detail="Account not verified")

        return {
            "message": "Login successful",
            "user": {
                "student_id": db_user["student_id"],
                "email": db_user["email"]
            }
        }

    except HTTPException as http_exc:
        # Log and re-raise HTTPExceptions (like 403 or 400)
        logging.error(f"❌ Login error: {http_exc.status_code}: {http_exc.detail}")
        raise http_exc

    except Exception as e:
        logging.error(f"❌ Internal login error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    



@router.post("/api/verify")
async def verification(user: verificationRequest, db=Depends(get_db)):
    try:
        db_user = await db.fetchrow(
            "SELECT student_id FROM accounts WHERE email = $1 AND code = $2",
            user.email, user.code
        )

        if db_user:
            # Update the verification_status to TRUE
            await db.execute(
                "UPDATE accounts SET verification_status = TRUE WHERE email = $1",
                user.email
            )

            return {
                "message": "Verification successful",
                "student_id": db_user["student_id"]
            }
        else:
            raise HTTPException(status_code=400, detail="Invalid email or verification code")

    except Exception as e:
        logging.error(f"❌ Internal verification error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")




def create_access_token(data: dict, expires_delta: timedelta = timedelta(hours=4)):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt

@router.post("/api/admin")
async def login(user: admin, db=Depends(get_db)):
    try:
        db_user = await db.fetchrow(
            "SELECT email, password FROM accounts WHERE email = $1", 
            user.email
        )
        if not db_user or not bcrypt.checkpw(user.password.encode(), db_user["password"].encode()):
            raise HTTPException(status_code=400, detail="Invalid email or password")
        
        # Create token
        token = create_access_token({"email": db_user["email"]})

        return {
            "message": "Login successful",
            "user": {

                "email": db_user["email"],
                "token": token
            }
        }
    except Exception as e:
        logging.error(f"❌ Login error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    










@router.put("/api/resend")
async def resend_code(background_tasks: BackgroundTasks, email: str = Form(...), db=Depends(get_db)):
    try:
        code = random.randint(100000, 999999)

        await db.execute(
            "Update accounts set code = $1 WHERE email = $2",
             code, email
        )

        subject = "Verify Your Mabini EasyDocs Account"
        text_body = f"Your verification code is: {code}"
        html_body = f"""<div style='text-align: center; font-family: Arial;'>
            <h2>Mabini EasyDocs</h2>
            <p>Your verification code is:</p><h2>{code}</h2>
            <p>Please enter this code to verify your account.</p></div>"""

        background_tasks.add_task(send_email, email, subject, text_body, html_body)
        return {"message": " Verification code sent."}

    except Exception as e:
        logging.error(f"❌ Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    





@router.put("/api/resetpassword")
async def updatepassword( email: str = Form(...),password:str = Form(...), db=Depends(get_db)):
    try:
       
        hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        await db.execute(
            "Update accounts set password = $1 WHERE email = $2",
             hashed_pw, email
        )

        return {"message": " Verification code sent."}

    except Exception as e:
        logging.error(f"❌ Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


    
@router.post("/api/finduser")
async def findmail(email: str = Form(...), db=Depends(get_db)):
    try:
        db_user = await db.fetchrow(
            "SELECT student_id FROM accounts WHERE email = $1",
            email
        )

        if db_user:
            return {
                "message": "Email exists",
                "student_id": db_user["student_id"]
            }
        else:
            raise HTTPException(status_code=404, detail="Email not found")

    except HTTPException as http_exc:
        logging.error(f"❌ Login error: {http_exc.status_code}: {http_exc.detail}")
        raise http_exc

    except Exception as e:
        logging.error(f"❌ Internal login error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
    
@router.put("/api/updateuser")
async def updateuser(data: UpdateUserRequest, db=Depends(get_db)):
    try:
        await db.execute(
            "UPDATE accounts SET email = $1 WHERE student_id = $2",
            data.email, data.studentid
        )
        return {
    "user": {
        "email": data.email,
        "verified": True  # or fetch from DB if needed
    },
    "message": "Email updated successfully."
}

    except Exception as e:
        logging.error(f"❌ Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")