FROM python:3.8-slim-bullseye

EXPOSE 8000

#Set the current directory as the working directory
WORKDIR /app

# Copy only the necessary files for pip install
COPY requirements.txt /app

# Use the default Debian mirrors
RUN apt-get update && apt-get install -y libgl1 libgomp1 libglib2.0-0 libsm6 libxrender1 libxext6

# Clean apt-get cache
RUN apt-get clean && rm -rf /var/lib/apt/lists/*

# Upgrade pip to the latest version from the default PyPI
RUN python3 -m pip install --upgrade pip

# Install python-docx from the default PyPI
RUN pip3 install -r requirements.txt

# Copy the rest
COPY . /app

# CMD ["python3", "./main.py"]
CMD ["uvicorn", "main:app", "--host", "0.0.0.0"]
