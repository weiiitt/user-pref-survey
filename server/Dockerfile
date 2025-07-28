# ================================== BUILDER ===================================
ARG INSTALL_PYTHON_VERSION=${INSTALL_PYTHON_VERSION:-PYTHON_VERSION_NOT_SET}
ARG INSTALL_NODE_VERSION=${INSTALL_NODE_VERSION:-NODE_VERSION_NOT_SET}

FROM node:${INSTALL_NODE_VERSION:-18}-bullseye-slim AS node
FROM python:${INSTALL_PYTHON_VERSION:-3.10}-slim-bullseye AS builder

WORKDIR /app

COPY --from=node /usr/local/bin/ /usr/local/bin/
COPY --from=node /usr/lib/ /usr/lib/
# See https://github.com/moby/moby/issues/37965
RUN true
COPY --from=node /usr/local/lib/node_modules /usr/local/lib/node_modules
COPY requirements requirements
COPY server server

RUN apt-get update && apt-get install -y \
    sqlite3 \
    python3-numpy \
    python3-setuptools \
    python3-pip \
    python3-dev \
    zlib1g-dev \
    libjpeg-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache -r requirements/prod.txt

COPY package.json ./
RUN npm install

COPY webpack.config.js autoapp.py ./
COPY assets assets
COPY .env.example .env
RUN npm run-script build

# ================================= PRODUCTION =================================
FROM python:${INSTALL_PYTHON_VERSION:-3.10}-slim-bullseye as production

WORKDIR /app

RUN useradd -m sid

ENV PATH="/home/sid/.local/bin:${PATH}"

COPY --from=builder --chown=sid:sid /app/server/static /app/server/static
COPY requirements requirements
COPY server server

COPY . .

RUN apt-get update && apt-get install -y \
    python3-numpy \
    python3-setuptools \
    python3-pip \
    python3-dev \
    zlib1g-dev \
    libjpeg-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache --user -r requirements/prod.txt

RUN chown -R sid:sid /app
USER sid

COPY supervisord.conf /etc/supervisor/supervisord.conf
COPY supervisord_programs /etc/supervisor/conf.d

EXPOSE 5000
ENTRYPOINT ["/bin/bash", "shell_scripts/supervisord_entrypoint.sh"]
CMD ["-c", "/etc/supervisor/supervisord.conf"]


# ================================= DEVELOPMENT ================================
FROM builder AS development

RUN apt-get update && apt-get install -y \
    sqlite3 \
    python3-numpy \
    python3-setuptools \
    python3-pip \
    python3-dev \
    zlib1g-dev \
    libjpeg-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache -r requirements/dev.txt

EXPOSE 2992
EXPOSE 5000
CMD [ "npm", "start" ]
