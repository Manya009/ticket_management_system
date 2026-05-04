#Base Environment
FROM python:3.13.11

# Set the working directory
WORKDIR /app

#copy entire app directory to the working directory
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port the app runs on
EXPOSE 8000

# Start the FastAPI server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

