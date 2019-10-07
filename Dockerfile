FROM python:3.7-slim
COPY ./service /service
WORKDIR /service
RUN pip install -r requirements.txt
EXPOSE 5001/tcp
ENTRYPOINT ["python"]
CMD ["sap-hana-service.py"]
