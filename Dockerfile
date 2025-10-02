# Use Python base image
FROM python:3.12-slim

# Install dependencies for TeX Live
RUN apt-get update && \
    apt-get install -y \
    texlive-latex-recommended \
    texlive-latex-extra \
    texlive-fonts-recommended \
    texlive-fonts-extra \
    texlive-xetex \
    dvipng \
    latexmk && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy all files
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port
EXPOSE 80

# Start FastAPI server
CMD ["uvicorn", "pdf_server:app", "--host", "0.0.0.0", "--port", "80"]
