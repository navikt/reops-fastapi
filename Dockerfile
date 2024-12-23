# Use the official Python image from the Docker Hub
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt


# Copy the application code into the container
# COPY app/main.py ./app/main.py

# Copy the application code and other necessary files into the container
COPY . .

# Copy the SSL certificates into the container
COPY /var/run/secrets/nais.io/sqlcertificate /var/run/secrets/nais.io/sqlcertificate

# Command to run the FastAPI app using uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]