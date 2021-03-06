#!/bin/bash

export VIAME_INSTALL=./../../..

source ${VIAME_INSTALL}/setup_viame.sh

pipeline_runner -p ${VIAME_INSTALL}/configs/pipelines/database_use_svm_models.pipe \
                -s reader:reader:db:video_name=input_list \
                -s descriptors:video_name=input_list
                

