from fastapi import APIRouter, Depends
from typing import List
from database import get_db
from models.schema import Enrollment

router = APIRouter()

@router.get("/enrollments", response_model=List[Enrollment])
async def get_enrollments(db=Depends(get_db)):
    query = """
        SELECT * FROM enrollments
        INNER JOIN students ON enrollments.student_id = students.id
        INNER JOIN programs ON enrollments.program_id = programs.id;
    """
    return [dict(row) for row in await db.fetch(query)]

@router.get("/enrollments/{student_id}", response_model=List[dict])
async def get_enrollments_by_student(student_id: int, db=Depends(get_db)):
    query = """
        SELECT enrollments.*, students.*, programs.*
        FROM enrollments
        INNER JOIN students ON enrollments.student_id = students.id
        INNER JOIN programs ON enrollments.program_id = programs.id
        WHERE students.id = $1;
    """
    return [dict(row) for row in await db.fetch(query, student_id)]
