###
# Model training examples, old API
##

set( example_files
  format_data_for_training.py
  generate_headers.py
  create_dir.py )

if( WIN32 )
  set( example_files
    ${example_files}
    habcam_training_example.bat
    training_on_many_datasets.bat )
else()
  set( example_files
    ${example_files}
    habcam_training_example.sh
    training_on_many_datasets.sh )
endif()

install( FILES       ${example_files}
         DESTINATION examples/detector_training_old_api )

if( VIAME_DOWNLOAD_MODELS )
  DownloadExtractAndInstall(
    https://data.kitware.com/api/v1/file/58d325ca8d777f0aef5d88ed/download
    b5497368fb79c74f8172213b14a08f7d
    ${VIAME_DOWNLOAD_DIR}/training_data_set1.tar.gz
    ${CMAKE_CURRENT_SOURCE_DIR}
    examples/detector_training_old_api
    training_data )
endif()

install( FILES       config_files/FRCNN.prototxt
                     config_files/YOLOv2.cfg
         DESTINATION examples/detector_training_old_api/config_files )
