FROM v2fly/v2fly-core:latest
WORKDIR /etc/v2ray
COPY config.json .
EXPOSE 8080
ENTRYPOINT ["v2ray"]
CMD ["run", "-c", "config.json"]
