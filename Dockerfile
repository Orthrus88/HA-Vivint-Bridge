FROM python:3.13-alpine

RUN addgroup -S bridge && adduser -S bridge -G bridge
WORKDIR /app
COPY src/vivint_bridge /app/vivint_bridge

USER bridge
EXPOSE 8099
CMD ["python", "-m", "vivint_bridge"]

