from fastapi import APIRouter, Response
from fastapi.responses import StreamingResponse
from services.docx_enrollment import generate_certificate
from services.docx_grades import generate_grades_certificate
from io import BytesIO
from fastapi import Body

router = APIRouter()



@router.post("/generate-certificate")
def create_certificate(data: dict = Body(...)):
    docx_file: BytesIO = generate_certificate(data)  # ensure this returns BytesIO
    fullname = data.get("fullname", "recipient").replace(" ", "_")

    return StreamingResponse(
        docx_file,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": f"attachment; filename=certificate_{fullname}.docx"
        }
    )

@router.post("/generate/grades")
def generate_grades(data: dict):
    docx_file = generate_grades_certificate(data)
    return Response(content=docx_file.getvalue(), media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document", headers={
        "Content-Disposition": "attachment; filename=certificate_of_grades.docx"
    })