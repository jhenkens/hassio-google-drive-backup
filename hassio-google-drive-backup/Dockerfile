ARG BUILD_FROM
FROM $BUILD_FROM
WORKDIR /app
COPY . /app
RUN chmod +x addon_deps.sh
RUN ./addon_deps.sh
RUN /app/venv/bin/pip install .
COPY config.json /app/venv/lib/python3.11/site-packages/config.json

EXPOSE 1627
EXPOSE 8099
ENTRYPOINT ["/app/venv/bin/python", "-m", "backup"]