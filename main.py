# import os
# import asyncpg
# import pytz
# import bcrypt
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
#     message["From"], message["To"], message["Subject"] = SMTP_CONFIG["sender_email"], to_email, subject
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
#     code: int

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
#         hashed_password = bcrypt.hashpw(user.password.encode(), bcrypt.gensalt()).decode()
#         await db.execute(
#             """
#             INSERT INTO accounts (student_id, email, password, code)
#             VALUES ($1, $2, $3, $4)
#             """,
#             user.student_id, user.email, hashed_password, user.code
#         )
#         subject, text_body = "Verify Your Barangay EasyDocs Account", f"Your verification code is: {user.code}"
#         html_body = f"""
#         <div style='text-align: center; font-family: Arial;'>
#             <h2 style='color: #2E86C1;'>Barangay EasyDocs</h2>
#             <p>Your verification code is:</p>
#             <h2 style='background: #f4f4f4; padding: 10px;'>{user.code}</h2>
#             <p>Please enter this code in the app to verify your account.</p>
#         </div>
#         """
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
from fastapi import FastAPI, Query
import numpy as np
import math
from pydantic import BaseModel
from typing import List, Union

app = FastAPI(title="NumPy Activities API", description="FastAPI endpoints for various NumPy-based activities.", version="1.0.0")

@app.get("/activity1", summary="Verify NumPy Installation", description="Returns the installed version of NumPy.")
def verify_numpy():
    return {"NumPy version": np.__version__}

@app.get("/activity2", summary="Array Properties", description="Creates a 2D NumPy array and returns its shape, dtype, and size.")
def array_properties():
    arr = np.array([[1, 2, 3], [4, 5, 6]])
    return {
        "array": arr.tolist(),
        "shape": arr.shape,
        "dtype": str(arr.dtype),
        "size": arr.size
    }

@app.get("/activity3", summary="Random Array Operations", description="Generates two 5x5 arrays and performs mean, median, std, addition, and reshaping.")
def random_array_operations():
    arr1 = np.random.rand(5, 5)
    arr2 = np.random.rand(5, 5)
    reshaped = arr1.reshape(25, 1)
    return {
        "array1": arr1.tolist(),
        "mean": np.mean(arr1),
        "median": np.median(arr1),
        "std": np.std(arr1),
        "element_wise_add": (arr1 + arr2).tolist(),
        "reshaped": reshaped.tolist()
    }

@app.get("/activity4", summary="Slicing and Indexing", description="Demonstrates different slicing and indexing techniques on a 2D NumPy array.")
def slicing_indexing():
    sample = np.array([
        [10, 20, 30, 40],
        [50, 60, 70, 80],
        [90, 100, 110, 120]
    ])
    return {
        "first_row": sample[0].tolist(),
        "second_column": sample[:, 1].tolist(),
        "first_third_rows": sample[[0, 2]].tolist(),
        "greater_than_50": sample[sample > 50].tolist()
    }

@app.get("/activity5", summary="Normalize Array", description="Normalizes a 1D NumPy array to values between 0 and 1.")
def normalize_array():
    arr = np.array([2, 4, 6, 8, 10])
    norm = (arr - np.min(arr)) / (np.max(arr) - np.min(arr))
    return {"normalized_array": norm.tolist()}

@app.get("/activity6", summary="Matrix Multiplication", description="Multiplies two compatible NumPy matrices and handles exceptions if mismatched.")
def matrix_multiplication():
    a = np.random.rand(3, 2)
    b = np.random.rand(2, 4)
    try:
        result = np.dot(a, b)
        return {"result": result.tolist()}
    except ValueError as e:
        return {"error": str(e)}

@app.get("/activity7", summary="Math Operations", description="Generates 10 random numbers and applies sqrt, log, and exponential functions.")
def math_operations():
    arr = np.random.rand(10) * 10
    sqrt_arr = [math.sqrt(x) for x in arr]
    log_arr = [math.log(x) for x in arr]
    exp_arr = [math.exp(x) for x in arr]
    return {
        "original": arr.tolist(),
        "sqrt": sqrt_arr,
        "log": log_arr,
        "exp": exp_arr
    }

@app.get("/activity8", summary="Custom Module Functions", description="Simulates importing functions from a custom module for addition and subtraction of arrays.")
def custom_module_functions():
    def add_arrays(a, b):
        return np.add(a, b)

    def subtract_arrays(a, b):
        return np.subtract(a, b)

    x = np.array([1, 2, 3])
    y = np.array([4, 5, 6])

    return {
        "add": add_arrays(x, y).tolist(),
        "subtract": subtract_arrays(x, y).tolist()
    }

def is_vowel(letter):
    return letter.lower() in "aeiou"

def is_consonant(letter):
    return letter.lower() in "bcdfghjklmnpqrstvwxyz"

def contains_love(name):
    return any(letter in "LOVE" for letter in name.upper())

def count_vowels(word):
    return sum(1 for letter in word if is_vowel(letter))

def count_consonants(word):
    return sum(1 for letter in word if is_consonant(letter))

def calculate_love_match(name1, name2):
    match_percent = 0

    if len(name1) == len(name2):
        match_percent += 25

    if is_vowel(name1[0]) and is_vowel(name2[0]):
        match_percent += 15

    if is_consonant(name1[0]) and is_consonant(name2[0]):
        match_percent += 10

    if contains_love(name1) and contains_love(name2):
        match_percent += 25

    if count_vowels(name1) and count_vowels(name2):
        match_percent += 15

    if count_consonants(name1) and count_consonants(name2):
        match_percent += 10

    if match_percent >= 90:
        message = f"{match_percent}% - try natin, kasi why not diba"
    elif match_percent >= 80:
        message = f"{match_percent}% - talking stage lang muna"
    elif match_percent >= 70:
        message = f"{match_percent}% - friends lang tayo lods"
    elif match_percent >= 60:
        message = f"{match_percent}% - alanganin lods"
    else:
        message = f"{match_percent}% - awit lods"

    return message

class LoveInput(BaseModel):
    boy_name: str
    girl_name: str

@app.post("/lovematch", summary="Calculate Love Match", description="Returns a love match percentage and message based on two names.")
def love_match(data: LoveInput):
    result = calculate_love_match(data.boy_name, data.girl_name)
    return {
        "boy": data.boy_name,
        "girl": data.girl_name,
        "love_result": result
    }


class NumberList(BaseModel):
    numbers: List[int]

@app.post("/second-largest", summary="Find Second Largest Number", description="Returns the second largest number in a given list of integers.")
def second_largest(data: NumberList):
    numbers = data.numbers
    if len(numbers) < 2:
        return {"error": "List must have at least 2 numbers"}
    
    largest = max(numbers[0], numbers[1])
    second_largest = min(numbers[0], numbers[1])
    for i in range(2, len(numbers)):
        if numbers[i] > largest:
            second_largest = largest
            largest = numbers[i]
        elif numbers[i] > second_largest and numbers[i] != largest:
            second_largest = numbers[i]
    return {"second_largest": second_largest}


class InputList(BaseModel):
    lst: List[Union[int, str]]

@app.post("/most-frequent", summary="Most Frequent Element", description="Returns the most frequent element from a list.")
def most_frequent(data: InputList):
    lst = data.lst
    if not lst:
        return {"error": "List is empty"}

    frequency = {}
    for item in lst:
        frequency[item] = frequency.get(item, 0) + 1

    max_count = max(frequency.values())
    for item in frequency:
        if frequency[item] == max_count:
            return {"most_frequent": item}
        
@app.get("/temperature-analysis", summary="Temperature Analysis", description="Analyzes 30 days of temperature data in Celsius.")
def get_temperature_stats():
    # Initialize an array of daily temperatures (30 days) in Celsius
    temperatures_celsius = np.array([
        20, 22, 19, 25, 28, 30, 18, 21, 23, 24, 
        26, 27, 29, 31, 17, 16, 20, 22, 25, 19, 
        23, 24, 26, 28, 30, 15, 18, 21, 27, 29
    ])

    # Convert to Fahrenheit
    temperatures_fahrenheit = (temperatures_celsius * 9/5) + 32

    # Perform analysis
    average_temp_celsius = round(np.mean(temperatures_celsius), 2)
    hottest_temp = int(np.max(temperatures_celsius))
    coldest_temp = int(np.min(temperatures_celsius))
    days_above_average = int(np.sum(temperatures_celsius > average_temp_celsius))

    # Return the analysis results
    return {
        "temperatures_celsius": temperatures_celsius.tolist(),
        "temperatures_fahrenheit": temperatures_fahrenheit.tolist(),
        "average_temp_celsius": average_temp_celsius,
        "hottest_temp": hottest_temp,
        "coldest_temp": coldest_temp,
        "days_above_average": days_above_average
    }