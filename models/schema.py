from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import List
from typing import Dict, Any
import pytz

class CreateUserRequest(BaseModel):
    student_id: int
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class verificationRequest(BaseModel):
    email: EmailStr
    code: int


class admin(BaseModel):
    email: str
    password: str

class Enrollment(BaseModel):
    id: int
    student_id: int
    program_id: int
    academic_year: str
    semester: str
    status: str
    enrollment_date: datetime
    firstname: str = Field(alias="fName")
    middlename: str = Field(alias="mName")
    lastname: str = Field(alias="lName")
    address: str
    contact: str
    email: str
    programcode: str = Field(alias="program_code")
    programname: str = Field(alias="program_name")

class Transaction(BaseModel):
    transaction_id: int
    student_id: int
    email: EmailStr
    certificate_type: str
    certificate_details: str
    purpose: str
    status: str
    date_requested: datetime

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: (
                v.replace(tzinfo=pytz.utc) if v.tzinfo is None else v
            ).astimezone(pytz.timezone("Asia/Manila")).strftime("%m/%d/%Y %I:%M %p")
        }

class UpdateUserRequest(BaseModel):
    studentid: int
    email: str

class history(BaseModel):
    transaction_id: int
    student_id: int
    email: EmailStr
    certificate_type: str
    certificate_details: str
    purpose: str
    status: str
    date_requested: datetime
    change_at:datetime

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: (
                v.replace(tzinfo=pytz.utc) if v.tzinfo is None else v
            ).astimezone(pytz.timezone("Asia/Manila")).strftime("%m/%d/%Y %I:%M %p")
        }

class CreateTransactionRequest(BaseModel):
    student_id: int
    certificate_type: str
    certificate_details: Dict[str, Any]  # Accepts JSON object
    purpose: str
    status: str

class CertificateRequest(BaseModel):
    fullname: str
    yearlevel: str
    courses: str
    semester: str
    year: str
    purpose: str

