# import os
# import asyncpg
# import pytz
# import bcrypt
# import random
# import logging
# from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel, EmailStr, Field
# from email.mime.multipart import MIMEMultipart
# from email.mime.text import MIMEText
# import aiosmtplib
# from dotenv import load_dotenv
# from datetime import datetime
# from typing import List
# from email.utils import formataddr


# # Load environment variables
# load_dotenv()

# # Initialize FastAPI app
# app = FastAPI()
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # Database connection settings
# DB_URL = os.getenv("SUPABASE_DB_URL") + "?prepared_statement_cache_size=0"
# async def get_db():
#     conn = await asyncpg.connect(DB_URL)
#     try:
#         yield conn
#     finally:
#         await conn.close()

# # SMTP Email Config
# SMTP_CONFIG = {
#     "server": os.getenv("SMTP_SERVER"),
#     "port": int(os.getenv("SMTP_PORT", 587)),
#     "username": os.getenv("SMTP_USERNAME"),
#     "password": os.getenv("SMTP_PASSWORD"),
#     "sender_email": os.getenv("SMTP_USERNAME"),
# }

# # Utility Functions
# def format_datetime(dt: datetime, timezone: str = "Asia/Manila") -> str:
#     return dt.astimezone(pytz.timezone(timezone)).strftime("%A, %B %d, %Y, %I:%M %p")

# async def send_email(to_email: str, subject: str, text_body: str, html_body: str):
#     message = MIMEMultipart()
#     message["From"] = formataddr(("Easy Docs", SMTP_CONFIG["sender_email"]))
#     message["To"] = to_email
#     message["Subject"] = subject

#     message.attach(MIMEText(text_body, "plain"))
#     message.attach(MIMEText(html_body, "html"))

#     try:
#         await aiosmtplib.send(
#             message.as_string(),
#             sender=SMTP_CONFIG["sender_email"],
#             recipients=[to_email],
#             hostname=SMTP_CONFIG["server"],
#             port=SMTP_CONFIG["port"],
#             username=SMTP_CONFIG["username"],
#             password=SMTP_CONFIG["password"],
#             use_tls=False,
#             start_tls=True,
#         )
#         logging.info(f"✅ Email sent to {to_email}")
#     except Exception as e:
#         logging.error(f"❌ Email sending failed: {e}")

# # Pydantic Models
# class CreateUserRequest(BaseModel):
#     student_id: int
#     email: EmailStr
#     password: str

# class LoginRequest(BaseModel):
#     email: EmailStr
#     password: str

# class Enrollment(BaseModel):
#     id: int
#     student_id: int
#     program_id: int
#     academic_year: str
#     semester: str
#     status: str
#     enrollment_date: datetime
#     firstname: str = Field(alias="fName")
#     middlename: str = Field(alias="mName")
#     lastname: str = Field(alias="lName")
#     address: str
#     contact: str
#     email: str
#     programcode: str = Field(alias="program_code")
#     programname: str = Field(alias="program_name")

# class Transaction(BaseModel):
#     transaction_id: int
#     student_id: int
#     email: EmailStr
#     certificate_type: str
#     certificate_details: str
#     purpose: str
#     status: str
#     daterequested: datetime = datetime.utcnow()


# class CreateTransactionRequest(BaseModel):
#     student_id:int
#     certificate_type:str
#     certificate_details:str
#     purpose:str
#     status:str

# # API Endpoints
# @app.post("/api/create_user")
# async def create_user(user: CreateUserRequest, background_tasks: BackgroundTasks, db=Depends(get_db)):
#     try:
#         # Auto-generate 6-digit code
#         verification_code = int(random.randint(100000, 999999))

#         # Hash the password
#         hashed_password = bcrypt.hashpw(user.password.encode(), bcrypt.gensalt()).decode()

#         # Insert into database
#         await db.execute(
#             """
#             INSERT INTO accounts (student_id, email, password, code)
#             VALUES ($1, $2, $3, $4)
#             """,
#             user.student_id, user.email, hashed_password, verification_code
#         )

#         # Prepare email
#         subject = "Verify Your Mabini EasyDocs Account"
#         text_body = f"Your verification code is: {verification_code}"
#         html_body = f"""
#         <div style='text-align: center; font-family: Arial;'>
#             <h2 style='color: #2E86C1;'>Mabini EasyDocs</h2>
#             <p>Your verification code is:</p>
#             <h2 style='background: #f4f4f4; padding: 10px;'>{verification_code}</h2>
#             <p>Please enter this code in the app to verify your account.</p>
#         </div>
#         """

#         # Send email in background
#         background_tasks.add_task(send_email, user.email, subject, text_body, html_body)

#         return {"message": "User created. Verification code sent."}

#     except Exception as e:
#         logging.error(f"❌ Error: {e}")
#         raise HTTPException(status_code=500, detail="Internal Server Error")

# @app.post("/api/login")
# async def login(user: LoginRequest, db=Depends(get_db)):
#     try:
#         db_user = await db.fetchrow("SELECT student_id, email, password FROM accounts WHERE email = $1", user.email)
#         if not db_user or not bcrypt.checkpw(user.password.encode(), db_user["password"].encode()):
#             raise HTTPException(status_code=400, detail="Invalid email or password")
#         return {"message": "Login successful", "user": {"student_id": db_user["student_id"], "email": db_user["email"]}}
#     except Exception as e:
#         logging.error(f"❌ Login error: {e}")
#         raise HTTPException(status_code=500, detail="Internal Server Error")

# @app.get("/enrollments", response_model=List[Enrollment])
# async def get_enrollments(db=Depends(get_db)):
#     query = """
#         SELECT * FROM enrollments
#         INNER JOIN students ON enrollments.student_id = students.id
#         INNER JOIN programs ON enrollments.program_id = programs.id;
#     """
#     return [dict(row) for row in await db.fetch(query)]



# @app.get("/enrollments/{student_id}", response_model=List[dict])
# async def get_enrollments_by_student(student_id: int, db=Depends(get_db)):
#     query = """
#         SELECT enrollments.*, students.*, programs.*
#         FROM enrollments
#         INNER JOIN students ON enrollments.student_id = students.id
#         INNER JOIN programs ON enrollments.program_id = programs.id
#         WHERE students.id = $1;
#     """
#     rows = await db.fetch(query, student_id)  # Use `fetch()` instead of `fetch_all()`
#     return [dict(row) for row in rows]



# @app.get("/certificate/retrieve", response_model=List[Transaction])
# async def get_certificate_requests(db=Depends(get_db)):
#     query = """
#         SELECT transaction_id, student_id, email, certificate_type, certificate_details, purpose, status, date_requested
#         FROM certificate_transactions
#         INNER JOIN students ON certificate_transactions.student_id = students.id;
#     """
#     return [dict(row) for row in await db.fetch(query)]






# @app.post("/certificate/request")
# async def create_certificate_request(request: CreateTransactionRequest, db=Depends(get_db)):
#     try:
#         await db.execute(
#             "INSERT INTO certificate_transactions (student_id,  certificate_type, certificate_details, purpose, status) VALUES ($1, $2, $3, $4, $5)",
#             request.student_id, request.certificate_type, request.certificate_details, request.purpose, request.status
#         )
#         return {"message": "Certificate request submitted successfully."}
#     except Exception as e:
#         logging.error(f"❌ Certificate request error: {e}")
#         raise HTTPException(status_code=500, detail="Internal Server Error")

# @app.put("/certificate/request/{transaction_id}")
# async def update_certificate_request(transaction_id: int, status: str, db=Depends(get_db)):
#     try:
#         await db.execute("UPDATE certificate_transactions SET status = $1 WHERE transaction_id = $2", status, transaction_id)
#         return {"message": "Certificate request updated successfully."}
#     except Exception as e:
#         logging.error(f"❌ Certificate update error: {e}")
#         raise HTTPException(status_code=500, detail="Internal Server Error")



from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import auth, certificates, enrollments,generator
from models import schema
from utils import helpers


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(enrollments.router)
app.include_router(certificates.router)
app.include_router(generator.router)
