#!/bin/bash

export VIAME_INSTALL=/opt/noaa/viame

source ${VIAME_INSTALL}/setup_viame.sh

python ${VIAME_INSTALL}/configs/launch_query_gui.py \
  -qp pipelines/query_retrieval_and_iqr.res.pipe
