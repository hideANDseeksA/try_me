from docx import Document
from io import BytesIO

def generate_certificate(data: dict, template_path: str = "templates/certificate_template.docx") -> BytesIO:
    doc = Document(template_path)

    for paragraph in doc.paragraphs:
        for key, value in data.items():
            placeholder = f"{{{{{key}}}}}"
            if placeholder in paragraph.text:
                paragraph.text = paragraph.text.replace(placeholder, str(value))

    output = BytesIO()
    doc.save(output)
    output.seek(0)
    return output
