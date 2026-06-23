# Use an official Python runtime as the base image
FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code into the container
COPY app ./app

# Tell Docker that this container will listen on port 5000
EXPOSE 5000

# Run the Flask app when the container starts
CMD ["python", "app/main.py"]
