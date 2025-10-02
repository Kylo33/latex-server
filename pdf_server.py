from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

import subprocess
import tempfile
import os
import io
import base64
import logging
import sys

import pdf2image

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

file_handler = logging.handlers.RotatingFileHandler("app.log", maxBytes=20_000_000)
file_handler.setLevel(logging.DEBUG)
logger.addHandler(file_handler)

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
logger.addHandler(console_handler)

formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Create the app, disable CORS protection
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class LatexModel(BaseModel):
    latex: str


def latex_to_images(source: str) -> str:
    """
    Creates a temporary file with the LaTeX source compiled,
    and returns the path to that file.
    """

    with tempfile.TemporaryDirectory() as working_dir:
        # Write the LaTeX source to a file
        source_file_path = os.path.join(working_dir, "input.tex")
        with open(source_file_path, "w") as source_file:
            source_file.write(source)

        logger.info(f"Wrote LaTeX source to {source_file_path}")

        # Compile the source to a PDF
        output_name = "output"

        subprocess.run(
            [
                "pdflatex",
                f"-jobname=output",
                "-interaction=nonstopmode",
                source_file_path,
            ],
            cwd=working_dir,
            stdout=subprocess.DEVNULL
        )
        
        # Convert the PDF to a list of Base64 encoded images
        output_path = os.path.join(working_dir, f"{output_name}.pdf")

        logger.info(f"Compiled PDF to {output_path}")

        images = pdf2image.convert_from_path(output_path)

    encoded_images = []
    for image in images:
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG")

        img_str = base64.b64encode(buffer.getvalue()).decode()
        encoded_images.append(img_str)

    logger.info(f"Encoded {len(encoded_images)} images with Base64 encoding")
    logger.debug(encoded_images)
    return encoded_images

# Image rendering endpoint
@app.post("/")
def generate_images(data: LatexModel):
    logger.info(f"Request to generate images from LaTeX source.")
    logger.debug(data.latex)
    images = latex_to_images(data.latex)
    return {"slides": images}


# LaTeX downloading endpoint
@app.post("/download")
def download_pdf(data: LatexModel, source: bool = False):
    if source:
        with open("output.tex", "w") as f:
            f.write(data.latex)
        return FileResponse("output.tex")

    LatexConvertor().convert_to_pdf(data.latex)
    return FileResponse("output.pdf")
