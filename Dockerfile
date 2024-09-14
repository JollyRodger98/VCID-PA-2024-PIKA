ARG PYTHON_VERSION=3.12.3

FROM python:${PYTHON_VERSION}-slim
LABEL authors="tim"

ENV TZ=Europe/Zurich

# Prevents Python from writing pyc files.
ENV PYTHONDONTWRITEBYTECODE=1

# Keeps Python from buffering stdout and stderr to avoid situations where
# the application crashes without emitting any logs due to buffering.
ENV PYTHONUNBUFFERED=1


# Install NodeJS package manager
RUN apt-get update -yq
RUN apt-get install npm -y

# Install python dependencies
WORKDIR /application
RUN --mount=type=cache,target=/root/.cache/pip \
    --mount=type=bind,source=requirements/prod-req.txt,target=prod-req.txt \
    python -m pip install -r prod-req.txt

# Copy application code
COPY pika/ pika/

# Install flask application as package
COPY pyproject.toml .
RUN pip install -e .

# Install node modules
RUN (cd pika/static ; npm install)

# Compile translation files
RUN pybabel compile -d pika/translations

# Copy config and entry files
COPY setup_script.py .
COPY config.toml .
COPY gunicorn.conf.py .
COPY wsgi.py .

EXPOSE 8000

ENTRYPOINT ["gunicorn", "wsgi:app"]