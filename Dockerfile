# use a lightweight Python base image
FROM python:3.11-slim

# set working directory inside the container
WORKDIR /app

# environment settings for Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copy the rest of the application source code
COPY . .

# set Flask environment
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=5000

# expose port 5000 for the Flask app
EXPOSE 5000

# run the Flask server as required: flask run --host=0.0.0.0
CMD ["flask", "run", "--host=0.0.0.0"]
