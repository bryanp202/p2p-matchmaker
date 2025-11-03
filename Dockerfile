FROM python:3.9-slim

COPY . .
RUN pip install --no-cache-dir --upgrade -r requirements.txt

EXPOSE 8000

CMD ["./start.sh"]
