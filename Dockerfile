FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . /app

RUN mkdir /app/uploads

CMD ["bash", "-lc", "streamlit run app.py --server.port $PORT --server.address 0.0.0.0"]
