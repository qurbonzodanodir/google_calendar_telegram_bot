# Use official Python runtime
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Expose port 8080 (standard for Cloud Run / Render)
EXPOSE 8080

# Run the application (Webhook Mode)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
