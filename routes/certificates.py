from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List
from database import get_db
from models.schema import Transaction, CreateTransactionRequest,history
import logging
import json
from sqlalchemy.ext.asyncio import AsyncSession
import asyncpg


router = APIRouter() 

@router.get("/certificate/retrieve", response_model=List[Transaction])
async def get_certificate_requests(db=Depends(get_db)):
    query = """
        SELECT transaction_id, student_id, email, certificate_type, certificate_details, purpose, status, date_requested
        FROM certificate_transactions
        INNER JOIN students ON certificate_transactions.student_id = students.id ORDER BY transaction_id;
    """
    return [dict(row) for row in await db.fetch(query)]

@router.post("/certificate/request")
async def create_certificate_request(request: CreateTransactionRequest, db=Depends(get_db)):
    try:
        # Convert dict to JSON string
        certificate_details_json = json.dumps(request.certificate_details)

        await db.execute(
            """
            INSERT INTO certificate_transactions 
            (student_id, certificate_type, certificate_details, purpose, status) 
            VALUES ($1, $2, $3, $4, $5)
            """,
            request.student_id,
            request.certificate_type,
            certificate_details_json,  # Pass JSON string here
            request.purpose,
            request.status
        )
        return {"message": "Certificate request submitted successfully."}
    except Exception as e:
        logging.error(f"❌ Certificate request error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.put("/certificate/request/{transaction_id}")
async def update_certificate_request(
    transaction_id: int,
    status: str = Query(...),
    db=Depends(get_db)  # this is likely an asyncpg connection
):
    try:
        result = await db.execute(
            "UPDATE certificate_transactions SET status = $1 WHERE transaction_id = $2",
            status, transaction_id
        )
        return {"message": "Certificate request updated successfully."}
    except Exception as e:
        logging.error(f"❌ Certificate update error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
@router.get("/grades/retrieve")
async def get_student_grades(student_id: int, academic_year: str, semester: str, db=Depends(get_db)):
    try:
        query = """
            SELECT subjects.subject_code, subjects.subject_name, grades.final_grade, subjects.units
            FROM grades
            INNER JOIN subjects ON grades.subject_code = subjects.subject_code
            WHERE grades.student_id = $1 AND grades.academic_year = $2 AND grades.semester = $3;
        """
        return [dict(row) for row in await db.fetch(query, student_id, academic_year, semester)]
    except Exception as e:
        logging.error(f"❌ Grade retrieval error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.get("/history/retrieve", response_model=List[history])
async def get_certificate_requests(db=Depends(get_db)):
    query = """
        SELECT transaction_id, student_id, email, certificate_type, certificate_details, purpose, status, date_requested,change_at
        FROM certificate_transactions_history
        INNER JOIN students ON certificate_transactions_history.student_id = students.id ORDER BY history_id DESC;
    """
    return [dict(row) for row in await db.fetch(query)]

@router.delete("/history/delete", response_model=bool)
async def delete_all_certificate_history(db=Depends(get_db)):
    query = """
        DELETE FROM certificate_transactions_history;
    """
    await db.execute(query)
    return True

@router.get("/certificate/by_student", response_model=List[history])
async def get_certificate_by_student(
    student_id: int = Query(..., description="The ID of the student"),
    db: asyncpg.Connection = Depends(get_db)
):
    query = """
     SELECT transaction_id, student_id, email, certificate_type, certificate_details, purpose, status, date_requested,change_at
        FROM certificate_transactions_history
        INNER JOIN students ON certificate_transactions_history.student_id = students.id 
         WHERE student_id = $1
        ORDER BY history_id DESC
       
    """
    rows = await db.fetch(query, student_id)
    return [dict(row) for row in rows]



@router.get("/summary/retrieve")
async def get_summary(db=Depends(get_db)):
    try:
        query = """
            SELECT 
                EXTRACT(YEAR FROM date_requested AT TIME ZONE 'Asia/Manila') AS year_local,
                EXTRACT(MONTH FROM date_requested AT TIME ZONE 'Asia/Manila') AS month,
                EXTRACT(WEEK FROM date_requested AT TIME ZONE 'Asia/Manila') AS week,
                COUNT(*) AS total_requests,
                SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END) AS completed,
                SUM(CASE WHEN status = 'Cancelled' THEN 1 ELSE 0 END) AS cancelled,
                SUM(CASE WHEN status = 'Reject' THEN 1 ELSE 0 END) AS rejected
            FROM certificate_transactions_history
            GROUP BY GROUPING SETS (
                (EXTRACT(YEAR FROM date_requested AT TIME ZONE 'Asia/Manila')),
                (EXTRACT(YEAR FROM date_requested AT TIME ZONE 'Asia/Manila'), EXTRACT(MONTH FROM date_requested AT TIME ZONE 'Asia/Manila')),
                (EXTRACT(YEAR FROM date_requested AT TIME ZONE 'Asia/Manila'), EXTRACT(WEEK FROM date_requested AT TIME ZONE 'Asia/Manila'))
            )
            ORDER BY year_local, month, week;
        """

        rows = await db.fetch(query)

        yearly_data = []
        monthly_data = []
        weekly_data = []

        month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                       "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

        for row in rows:
            year = str(int(row["year_local"])) if row["year_local"] is not None else None
            month = row["month"]
            week = row["week"]

            entry = {
                "year": year,
                "total_requests": row["total_requests"],
                "completed": row["completed"],
                "cancelled": row["cancelled"],
                "rejected": row["rejected"]
            }

            if year and month is None and week is None:
                yearly_data.append(entry)
            elif year and month is not None and week is None:
                entry["month"] = month_names[int(month) - 1]
                monthly_data.append(entry)
            elif year and week is not None and month is None:
                entry["week"] = f"Week {int(week)}"
                weekly_data.append(entry)

        return {
            "yearlyData": yearly_data,
            "monthlyData": monthly_data,
            "weeklyData": weekly_data
        }

    except Exception as e:
        print("Error retrieving summary:", e)
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.get("/accounts/retrieve")
async def get_accounts(db=Depends(get_db)):
    query = """
       SELECT email,student_id,verification_status FROM accounts WHERE student_id IS NOT NULL;
    """
    return [dict(row) for row in await db.fetch(query)]


@router.get("/summary")
async def get_summary(db: asyncpg.Connection = Depends(get_db)
):
    query = """
     SELECT
  COUNT(*) AS total_requests,
  COUNT(*) FILTER (WHERE status = 'Pending') AS pending_count,
  COUNT(*) FILTER (WHERE status = 'On Process') AS on_process_count,
  COUNT(*) FILTER (WHERE status = 'Ready To Claim') AS ready_to_claim_count
FROM certificate_transactions;

       
    """
    rows = await db.fetch(query)
    return [dict(row) for row in rows]