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
RUN git clone --recursive $GIT_URL && \
    cd c3s_sm && \
    git checkout $GIT_BRANCH_TAG_COMMIT

ARG MAMBA_DOCKERFILE_ACTIVATE=1

RUN micromamba install -y -n base -c conda-forge python=3.12
RUN cd c3s_sm &&  \
    pip install . &&\
    pip uninstall repurpose --yes && \
    pip install git+https://github.com/TUW-GEO/repurpose@e2d0d3ce8e666a4fbcd24de34a874d8850d2894a

RUN micromamba clean --all --yes

# Clean up the src code, as it is installed now
RUN rm -rf c3s_sm

ENTRYPOINT ["/usr/local/bin/_entrypoint.sh"]
