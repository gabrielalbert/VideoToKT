FROM python:3.9
RUN apt-get update && apt-get install -y libgl1-mesa-glx tesseract-ocr ffmpeg libaom-dev libdav1d-dev libavcodec-extra  && apt-get clean
ENV PYTHONUNBUFFERED 1
WORKDIR /app
COPY requirements.txt requirements.txt
# RUN pip install --no-cache-dir --upgrade --force-reinstall -r requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]