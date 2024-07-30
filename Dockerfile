# ---------------------------------------------------------------------------- #
#                      example usage for docker and poetry                     #
# ---------------------------------------------------------------------------- #


# ---------------------------------------------------------------------------- #
#                            global build arguments                            #
# ---------------------------------------------------------------------------- #

# Global ARG, available to all stages (if renewed)
ARG WORKDIR="/src"

# global username
ARG USERNAME=bluesmonk
ARG USER_UID=1000
ARG USER_GID=1000

# tag used in all images
ARG PYTHON_VERSION=3.12.2

# ---------------------------------------------------------------------------- #
#                                  build stage                                 #
# ---------------------------------------------------------------------------- #

FROM python:${PYTHON_VERSION}-slim AS builder

# Renew args
ARG WORKDIR
ARG USERNAME
ARG USER_UID
ARG USER_GID

# Poetry version
ARG POETRY_VERSION=1.8.3

# Pipx version
ARG PIPX_VERSION=1.6.0

# prepare the $PATH
ENV PATH=/usr/local/bin:/opt/pipx/bin:${WORKDIR}/.venv/bin:$PATH \
    PIPX_BIN_DIR=/opt/pipx/bin \
    PIPX_HOME=/opt/pipx/home \
    PIPX_VERSION=$PIPX_VERSION \
    POETRY_VERSION=$POETRY_VERSION \
    PYTHONPATH=${WORKDIR} \
    # Don't buffer `stdout`
    PYTHONUNBUFFERED=1 \
    # Don't create `.pyc` files:
    PYTHONDONTWRITEBYTECODE=1 \
    # make poetry create a .venv folder in the project
    POETRY_VIRTUALENVS_IN_PROJECT=true

# ------------------------------ add user ----------------------------- #

RUN groupadd --gid $USER_GID "${USERNAME}" \
    && useradd --uid $USER_UID --gid $USER_GID -m "${USERNAME}"

# -------------------------- add python dependencies ------------------------- #

# Install Pipx using pip
RUN python -m pip install --no-cache-dir --upgrade pip pipx==${PIPX_VERSION}
#RUN apt-get update && \
#apt-get install --no-install-suggests --no-install-recommends --yes pipx
RUN pipx ensurepath && pipx --version

# Install Poetry using pipx
RUN pipx install --force poetry==${POETRY_VERSION}

RUN pipx inject poetry poetry-plugin-bundle
# ---------------------------- add code specifics ---------------------------- #

# Copy everything to the container
# we filter out what we don't need using .dockerignore
WORKDIR ${WORKDIR}

# make sure the user owns /app
RUN chown -R ${USER_UID}:${USER_GID} ${WORKDIR}

# Copy only the files needed for installing dependencies
COPY --chown=${USER_UID}:${USER_GID} pyproject.toml poetry.lock ${WORKDIR}/

USER ${USERNAME}


# ---------------------------------------------------------------------------- #
#                                 app-pre stage                                #
# ---------------------------------------------------------------------------- #

FROM builder AS app-pre

# Install dependencies and creates a a virtualenv at /app/.venv
# RUN poetry install --no-root --only main
RUN poetry bundle venv --python=/usr/local/bin/python3 --only=main /.venv

# ---------------------------------------------------------------------------- #
#                                   app stage                                  #
# ---------------------------------------------------------------------------- #

# We don't want to use alpine because porting from debian is challenging
# https://stackoverflow.com/a/67695490/5819113
FROM python:${PYTHON_VERSION}-slim AS app

# refresh global arguments
ARG WORKDIR
ARG USERNAME
ARG USER_UID
ARG USER_GID

# refresh PATH
ENV PATH=/usr/local/bin:/opt/pipx/bin:${WORKDIR}/.venv/bin:$PATH \
    POETRY_VERSION=$POETRY_VERSION \
    PYTHONPATH=${WORKDIR} \
    # Don't buffer `stdout`
    PYTHONUNBUFFERED=1 \
    # Don't create `.pyc` files:
    PYTHONDONTWRITEBYTECODE=1

# ------------------------------ user management ----------------------------- #

RUN groupadd --gid $USER_GID "${USERNAME}" \
    && useradd --uid $USER_UID --gid $USER_GID -m "${USERNAME}"

# ------------------------------- app specific ------------------------------- #

WORKDIR ${WORKDIR}

RUN chown -R ${USER_UID}:${USER_GID} ${WORKDIR}

COPY --from=app-pre --chown=${USER_UID}:${USER_GID} ${WORKDIR} ${WORKDIR}

USER ${USERNAME}

#ENTRYPOINT [ "python3" ]
#CMD [ "--version" ]
ENTRYPOINT ["/.venv/bin/hypermodern_python"]

# ---------------------------------------------------------------------------- #
#                                   dev stage                                  #
# ---------------------------------------------------------------------------- #

FROM app-pre AS dev

# refresh global arguments
ARG WORKDIR
ARG USERNAME
ARG USER_UID
ARG USER_GID


USER root

# Add USERNAME to sudoers. Omit if you don't need to install software after connecting.
RUN apt-get update \
    && apt-get install -y sudo git iputils-ping wget \
    && echo ${USERNAME} ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/${USERNAME} \
    && chmod 0440 /etc/sudoers.d/${USERNAME}

USER ${USERNAME}

# install all remaning dependencies
RUN poetry install --no-root

USER ${USERNAME}
