#!/bin/sh

export VIAME_INSTALL=./../..

source ${VIAME_INSTALL}/setup_viame.sh

python ${VIAME_INSTALL}/configs/ingest_video.py --init -d INPUT_DIRECTORY \
  --detection-plots -species fish -threshold 0.25 -frate 2 -smooth 2 \
  -p pipelines/ingest_video.mouss_count.pipe

# Timestamp adjustment hack (will be removed in future iterations), converts milliseconds to seconds
for f in database/*.kw18; do
    awk '{print $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18 / 1e6, $19, $20}' < ${f}.bckup > ${f}
done
