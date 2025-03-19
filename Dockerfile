FROM python:3.9-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY digital_front_desk/ ./digital_front_desk/

# Run the application
CMD ["uvicorn", "digital_front_desk.__main__:app", "--host", "0.0.0.0", "--port", "8000"] 