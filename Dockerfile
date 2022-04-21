FROM ubuntu:latest

ENV TZ=Asia/Kolkata
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN apt update --fix-missing && apt upgrade -y
RUN apt install python3 python3-pip python-is-python3 gunicorn -y

WORKDIR /usr/src/app
COPY . .
RUN pip install -r requirements.txt

CMD ["gunicorn" , "--bind", "0.0.0.0:5000", "app:app"]