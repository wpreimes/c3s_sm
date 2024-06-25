FROM mambaorg/micromamba:1.3.1-alpine
MAINTAINER Wolfgang Preimesberger <wolfgang.preimesberger@geo.tuwien.ac.at>

USER root

ARG GIT_BRANCH_TAG_COMMIT
ARG GIT_URL

RUN apk update && \
    apk upgrade && \
    apk add git && \
    apk add build-base && \
    apk add g++ && \
    apk add bsd-compat-headers && \
    apk add tiff

# Check out the SMECV code at the chose tag using your credentials
RUN echo "$GIT_URL@$$GIT_BRANCH_TAG_COMMIT"
RUN git clone $GIT_URL && \
    cd c3s_sm && \
    git checkout $GIT_BRANCH_TAG_COMMIT

ARG MAMBA_DOCKERFILE_ACTIVATE=1

# Other dependencies are installed from the conda yml file with mamba
RUN cp c3s_sm/environment.yml .
RUN micromamba install -y -n base -f c3s_sm/environment.yml &&  \
    pip install ./c3s_sm && \
    micromamba clean --all --yes

# Clean up the src code, as it is installed now
RUN rm -rf c3s_sm

ENTRYPOINT ["/usr/local/bin/_entrypoint.sh"]
