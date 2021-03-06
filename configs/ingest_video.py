#!/usr/bin/env python

import sys
import os
import argparse
import contextlib
import itertools
import signal
import subprocess

sys.dont_write_bytecode = True

import aggregate_plots
import database_tool

# Helper class to list files with a given extension in a directory
def list_files_in_dir( folder ):
  return [
    os.path.join(folder, f) for f in sorted(os.listdir(folder))
    if not f.startswith('.')
  ]

def list_files_in_dir_w_ext( folder, extension ):
  return [f for f in list_files_in_dir(folder) if f.endswith(extension)]

# Create a directory if it doesn't exist
def create_dir( dirname, logging=True ):
  if not os.path.exists( dirname ):
    if logging:
      print( "Creating " + dirname )
    os.makedirs( dirname )

def execute_command( cmd, stdout=None, stderr=None ):
  return subprocess.call(cmd, stdout=stdout, stderr=stderr)

def get_script_path():
  return os.path.dirname( os.path.realpath( sys.argv[0] ) )

def get_pipeline_cmd( debug=False ):
  if os.name == 'nt':
    if debug:
      return ['pipeline_runner.exe']
    else:
      return ['pipeline_runner.exe']
  else:
    if debug:
      return ['gdb', '--args', 'pipeline_runner']
    else:
      return ['pipeline_runner']

def exit_with_error( error_str ):
  print( error_str )
  sys.exit(0)

def check_file( filename ):
  if not os.path.exists( filename ):
    exit_with_error( "Unable to find: " + filename )
  return filename

@contextlib.contextmanager
def get_log_output_files( output_prefix ):
  if os.name == 'nt':
    with open(output_prefix + '.out.txt', 'w') as fo, \
         open(output_prefix + '.err.txt', 'w') as fe:
      yield dict(stdout=fo, stderr=fe)
  else:
    with open(output_prefix + '.txt', 'w') as fo:
      yield dict(stdout=fo, stderr=fo)

def find_file( filename ):
  if( os.path.exists( filename ) ):
    return filename
  elif os.path.exists( get_script_path() + "/" + filename ):
    return get_script_path() + "/" + filename
  else:
    exit_with_error( "Unable to find " + filename )

# Other helpers
def signal_handler( signal, frame ):
  exit_with_error( 'Ingest aborted, see you next time' )

def fset( setting_str ):
  return ['-s', setting_str]

def video_output_settings_list( basename ):
  return list(itertools.chain(
    fset( 'detector_writer:file_name=database/' + basename + '.csv' ),
    fset( 'track_writer:file_name=database/' + basename + '_tracks.csv' ),
    fset( 'track_writer:stream_identifier=' + basename ),
    fset( 'track_writer_db:writer:db:video_name=' + basename ),
    fset( 'track_writer_kw18:file_name=database/' + basename + '.kw18' ),
    fset( 'descriptor_writer_db:writer:db:video_name=' + basename ),
    fset( 'track_descriptor:uid_basename=' + basename ),
    fset( 'kwa_writer:output_directory=database ' ),
    fset( 'kwa_writer:base_filename=' + basename ),
    fset( 'kwa_writer:stream_id=' + basename ),
  ))

def archive_dimension_settings_list( options ):
  if len( options.archive_width ) > 0:
    return list(itertools.chain(
      fset( 'kwa_writer:fixed_col_count=' + options.archive_width ),
      fset( 'kwa_writer:fixed_row_count=' + options.archive_height ),
    ))
  return []

def video_frame_rate_settings_list( options ):
  output = []
  if len( options.frame_rate ) > 0:
    output += fset( 'downsampler:target_frame_rate=' + options.frame_rate )
  if len( options.batch_size ) > 0:
    output += fset( 'downsampler:burst_frame_count=' + options.batch_size )
  if len( options.batch_skip ) > 0:
    output += fset( 'downsampler:burst_frame_break=' + options.batch_skip )
  return output

def remove_quotes( input_str ):
  return input_str.replace( "\"", "" )

# Process a single video
def process_video_kwiver( input_name, options, is_image_list=False, base_ovrd='' ):

  sys.stdout.write( 'Processing: ' + input_name + "... " )
  sys.stdout.flush()

  # Get video name without extension and full path
  if len( base_ovrd ) > 0:
    basename = base_ovrd
  else:
    basename = os.path.splitext( os.path.basename( input_name ) )[0]

  # Formulate input setting string
  if is_image_list:
    input_setting = fset( 'input:image_list_file=' + input_name )
  else:
    input_setting = fset( 'input:video_filename=' + input_name )

  # Formulate command
  command = (get_pipeline_cmd( options.debug ) +
             ['-p', find_file( options.pipeline )] +
             input_setting)

  if not is_image_list:
    command += video_frame_rate_settings_list( options )

  command += video_output_settings_list( basename )
  command += archive_dimension_settings_list( options )

  if len( options.input_detections ) > 0:
    command += fset( "detection_reader:file_name=" + options.input_detections )

  if len( options.extra_options ) > 0:
    for extra_option in options.extra_options:
      command += fset( extra_option )

  # Process command, possibly with logging
  if len( options.log_dir ) > 0 and not options.debug:
    with get_log_output_files(options.log_dir + '/' + basename) as kwargs:
      res = execute_command(command, **kwargs)
  else:
    res = execute_command(command)

  if res == 0:
    print( 'Success' )
  else:
    print( 'Failure' )
    exit_with_error( '\nIngest failed, check database/Log files, terminating.\n' )

# Plot settings strings
def plot_settings_list( basename ):
  return list(itertools.chain(
    fset( 'detector_writer:file_name=database/' + basename + '_detections.csv' ),
    fset( 'kwa_writer:output_directory=database ' ),
    fset( 'kwa_writer:base_filename=' + basename ),
    fset( 'kwa_writer:stream_id=' + basename ),
  ))

# Main Function
if __name__ == "__main__" :

  parser = argparse.ArgumentParser(description="Ingest new videos",
                       formatter_class=argparse.ArgumentDefaultsHelpFormatter)

  parser.add_argument("-v", dest="input_video", default="",
                      help="Input single video to ingest")

  parser.add_argument("-d", dest="input_dir", default="",
                      help="Input directory to ingest")

  parser.add_argument("-l", dest="input_list", default="",
                      help="Input list of image or video files to ingest")

  parser.add_argument("-p", dest="pipeline", default="pipelines/ingest_video.tut.pipe",
                      help="Input pipeline for ingesting video or image data")

  parser.add_argument("-e", dest="extra_options", default="",
                      help="Extra command line arguments for the pipeline runner")

  parser.add_argument("-id", dest="input_detections", default="",
                      help="Input detections around which to create descriptors")

  parser.add_argument("-frate", dest="frame_rate", default="",
                      help="Frame rate over-ride to process videos at")

  parser.add_argument("-fbatch", dest="batch_size", default="",
                      help="Optional number of frames to process in batches")

  parser.add_argument("-fskip", dest="batch_skip", default="",
                      help="If batching frames, number of frames to skip between batches")

  parser.add_argument("-species", dest="species", default="fish",
                      help="Species to generate plots for")

  parser.add_argument("-threshold", dest="threshold", default="0.25",
                      help="Threshold to generate plots for")

  parser.add_argument("-smooth", dest="smooth", default="1",
                      help="Smoothing factor for plots")

  parser.add_argument("-archive-height", dest="archive_height", default="",
                      help="Advanced: Optional video archive height over-ride")

  parser.add_argument("-archive-width", dest="archive_width", default="",
                      help="Advanced: Optional video archive width over-ride")

  parser.add_argument("-logs", dest="log_dir", default="database/Logs",
                      help="Directory for log files, if empty will not use files")

  parser.add_argument("--init-db", dest="init_db", action="store_true",
                      help="Re-initialize database")

  parser.add_argument("--build-index", dest="build_index", action="store_true",
                      help="Build searchable index on completion")

  parser.add_argument("--ball-tree", dest="ball_tree", action="store_true",
                      help="Use a ball tree for the searchable index")

  parser.add_argument("--debug", dest="debug", action="store_true",
                      help="Run with debugger attached to process")

  parser.add_argument("--detection-plots", dest="detection_plots", action="store_true",
                      help="Produce per-video detection plot summaries")

  parser.add_argument("-install", dest="install_dir", default="",
                      help="Optional install dir over-ride for all application "
                      "binaries. If this is not specified, it is expected that all "
                      "viame binaries are already in our path.")

  args = parser.parse_args()

  # Error checking
  process_data = True

  number_input_args = sum(len(inp_x) > 0 for inp_x in [args.input_video, args.input_dir, args.input_list])
  if number_input_args == 0:
    if not args.build_index and not args.detection_plots:
      exit_with_error( "Either input video or input directory must be specified" )
    else:
      process_data = False

  elif number_input_args > 1:
    exit_with_error( "Only one of input video, directory, or list should be specified, not more" )

  signal.signal( signal.SIGINT, signal_handler )

  # Initialize database
  if args.init_db:
    database_tool.init()

  # Identify all videos to process
  video_list = []

  if process_data:

    if len( args.input_list ) > 0:
      video_list.append( args.input_list )
      is_image_list = True
    elif len( args.input_dir ) > 0:
      video_list = list_files_in_dir( args.input_dir )
      is_image_list = False
    else:
      video_list.append( args.input_video )
      is_image_list = False

    if len( video_list ) == 0:
      exit_with_error( "No videos found for ingest in given folder, exiting.\n" )
    elif not is_image_list:
      print( "\nIngesting " + str( len( video_list ) ) + " videos\n" )

    # Get required paths
    pipeline_loc = args.pipeline

    if len( args.log_dir ) > 0:
      create_dir( args.log_dir )
      sys.stdout.write( "\n" )

    # Process videos
    for video_name in video_list:
      if os.path.exists( video_name ) and os.path.isfile( video_name ):
        process_video_kwiver( video_name, args, is_image_list )
      else:
        print( "Skipping " + video_name )

  # Build out final analytics
  if args.detection_plots:
    print( "Generating data plots" )
    aggregate_plots.fish_aggregate( "database", args.species.split(","),
                                    float( args.threshold ),
                                    float( args.frame_rate ),
                                    int( args.smooth ) )

  # Build index
  if args.build_index:
    print( "\n\nBuilding searchable index\n" )
    if args.ball_tree:
      database_tool.build_balltree_index( remove_quotes( args.install_dir ) )
    else:
      database_tool.build_standard_index( remove_quotes( args.install_dir ) )

  # Output complete message
  print( "\n\nIngest complete\n" )
