FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV POETRY_VIRTUALENVS_CREATE=false
ENV POETRY_NO_INTERACTION=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    wget gnupg2 ca-certificates curl xvfb xauth python3-tk python3-dev \
    libnss3 libxss1 libasound2 libgbm1 libgtk-3-0 libx11-6 libx11-xcb1 libxcb1 \
    libxcomposite1 libxcursor1 libxdamage1 libxext6 libxfixes3 libxrandr2 libxrender1 \
    libxtst6 fonts-liberation libpangocairo-1.0-0 libpango-1.0-0 libgtk2.0-0 \
    && mkdir -p /etc/apt/keyrings \
    && wget -q -O- https://dl-ssl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /etc/apt/keyrings/google-chrome.gpg \
    && echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update && apt-get install -y --no-install-recommends google-chrome-stable \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir poetry

COPY pyproject.toml poetry.lock* /app/
RUN poetry install --no-interaction --no-ansi --without dev

RUN poetry run playwright install chromium

COPY . /app

RUN mkdir -p /root/.cache/seleniumbase /root/.local/share/seleniumbase \
    && chmod -R 777 /root /tmp

CMD ["sh", "-c", "env -u DISPLAY -u XDG_SESSION_TYPE -u WAYLAND_DISPLAY xvfb-run --server-args='-screen 0 1280x900x24 -ac -nolisten tcp -nocursor' poetry run scrapy crawl ifood 2>&1 | tee execucao.log"]