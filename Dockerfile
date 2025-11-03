FROM python:3.9-slim

COPY . .
RUN pip install --no-cache-dir --upgrade -r requirements.txt

RUN chmod +x ./start.sh

EXPOSE 8000

CMD ["./start.sh"]
