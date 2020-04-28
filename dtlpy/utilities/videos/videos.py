import time
import numpy as np
import os
import logging

logger = logging.getLogger(name=__name__)


##########
# Videos #
##########
class Videos:
    def __init__(self):
        pass

    @staticmethod
    def get_info(filepath):
        import ffmpeg
        probe = ffmpeg.probe(filepath)
        return probe

    @staticmethod
    def disassemble(filepath, fps=None, loglevel='panic'):
        """
        Disassemble video to images

        :param filepath: input video filepath
        :param fps: rate of disassemble. e.g if 1 frame per second fps is 1. if None all frames will be extracted
        :param loglevel: ffmpeg loglevel
        :return:
        """
        import ffmpeg
        if not os.path.isfile(filepath):
            raise IOError('File doesnt exists: {}'.format(filepath))
        basename, ext = os.path.splitext(filepath)
        # create folder for the frames
        if not os.path.exists(basename):
            os.makedirs(basename, exist_ok=True)
        # get video information
        video_props = Videos.get_info(filepath)
        if fps is None:
            fps = eval(video_props['streams'][0]['avg_frame_rate'])
        num_of_zeros = len(video_props['streams'][0]['nb_frames'])
        # format the output filename
        output_regex = os.path.join(basename, '%%0%dd.jpg' % num_of_zeros)

        try:
            stream = ffmpeg.input(filepath, **{'loglevel': loglevel}).output(output_regex,
                                                                             **{'start_number': '0',
                                                                                'r': str(fps)})
            ffmpeg.overwrite_output(stream).run()
        except Exception as e:
            logger.error('ffmpeg error in disassemble:')
            raise
        return basename

    @staticmethod
    def reencode(filepath, loglevel='panic'):
        """
        Re-encode video as mp4, remove start offset and set bframes to 0

        :param filepath: input video file
        :param loglevel: ffmpeg loglevel
        :return:
        """
        import ffmpeg
        if not os.path.isfile(filepath):
            raise IOError('File doesnt exists: {}'.format(filepath))
        # re encode video without b frame and as mp4
        basename, ext = os.path.splitext(filepath)
        output_filepath = os.path.join(basename, os.path.basename(filepath).replace(ext, '.mp4'))
        if not os.path.isdir(os.path.dirname(output_filepath)):
            os.makedirs(os.path.dirname(output_filepath))
        try:
            stream = ffmpeg.input(filepath, **{'loglevel': loglevel}).output(output_filepath,
                                                                             **{'x264opts': 'bframes=0',
                                                                                'f': 'mp4'})
            ffmpeg.overwrite_output(stream).run()
        except Exception as e:
            logger.exception('ffmpeg error in disassemble:')
            raise

        output_probe = Videos.get_info(output_filepath)
        start_time = eval(output_probe['streams'][0]['start_time'])
        fps = eval(output_probe['streams'][0]['avg_frame_rate'])
        has_b_frames = output_probe['streams'][0]['has_b_frames']
        start_frame = fps * start_time
        if start_time != 0:
            logger.warning('Video start_time is not 0!')
        if has_b_frames != 0:
            logger.warning('Video still has b frames!')
        return output_filepath

    @staticmethod
    def split_and_upload(filepath,
                         # upload parameters
                         project_name=None, project_id=None, dataset_name=None, dataset_id=None, remote_path=None,
                         # split parameters
                         split_seconds=None, split_chunks=None, split_pairs=None,
                         loglevel='panic'):
        """
        Split video to chunks and upload to platform

        :param filepath: input video file
        :param project_name:
        :param project_id:
        :param dataset_name:
        :param dataset_id:
        :param remote_path:
        :param split_seconds: split by seconds per chunk. each chunk's length will be this in seconds
        :param split_chunks: split by number of chunks.
        :param split_pairs: a list od (start, stop) segments to split in seconds . e.g [(0,400), (600,800)]
        :param loglevel: ffmpeg loglevel
        :return:
        """
        import ffmpeg
        # https://www.ffmpeg.org/ffmpeg-formats.html#Examples-9

        if not os.path.isfile(filepath):
            raise IOError('File doesnt exists: {}'.format(filepath))
        logger.info('Extracting video information...')
        # call to ffmpeg to get frame rate
        probe = Videos.get_info(filepath)
        fps = eval(probe['streams'][0]['avg_frame_rate'])
        n_frames = eval(probe['streams'][0]['nb_frames'])
        video_length = eval(probe['streams'][0]['duration'])
        logger.info('Video frame rate: %d[fps]' % fps)
        logger.info('Video number of frames: %d' % n_frames)
        logger.info('Video length in seconds: %d[s]' % video_length)

        # check split params and calc split params for ffmpeg
        if split_seconds is not None:
            # split by seconds
            split_length = split_seconds
            if split_length <= 0:
                raise ValueError('"split_length" can\'t be 0')
            split_count = int(np.ceil(video_length / split_length))
            list_frames_to_split = [fps * split_length * n for n in range(1, split_count)]
        elif split_chunks is not None:
            # split for known number of chunks
            split_count = split_chunks
            if split_chunks <= 0:
                raise ValueError('"split_chunks" size can\'t be 0')
            split_length = int(np.ceil(video_length / split_chunks))
            list_frames_to_split = [fps * split_length * n for n in range(1, split_count)]
        elif split_pairs is not None:
            if not isinstance(split_pairs, list):
                raise ValueError('"split_times" must be a list of tuples to split at.')
            if not (isinstance(split_pairs[0], list) or isinstance(split_pairs[0], tuple)):
                raise ValueError('"split_times" must be a list of tuples to split at.')
            list_frames_to_split = [fps * split_second for segment in split_pairs for split_second in segment]
            split_count = len(list_frames_to_split)
        else:
            raise ValueError('Must input one split option ("split_chunks", "split_time" or "split_pairs")')
        if split_count == 1:
            raise ValueError('Video length is less than the target split length.')
        # to integers
        list_frames_to_split = [int(i) for i in list_frames_to_split]
        # remove 0 if in the first segmetn
        if list_frames_to_split[0] == 0:
            list_frames_to_split.pop(0)
        # add last frames if not exists
        if list_frames_to_split[-1] != n_frames:
            list_frames_to_split = list_frames_to_split + [n_frames]
        logger.info('Splitting to %d chunks' % split_count)

        basename, ext = os.path.splitext(filepath)
        output_regex = os.path.join(basename, '%%03d%s' % '.mp4')
        # create folder
        if not os.path.exists(basename):
            os.makedirs(basename, exist_ok=True)
        # run ffmpeg
        try:
            stream = ffmpeg.input(filepath, **{'loglevel': loglevel}).output(output_regex,
                                                                             **{'x264opts': 'bframes=0',
                                                                                'f': 'segment',
                                                                                'reset_timestamps': '1',
                                                                                'map': '0',
                                                                                'segment_frames': ','.join(
                                                                                    [str(i) for i in
                                                                                     list_frames_to_split])
                                                                                })
            ffmpeg.overwrite_output(stream).run(capture_stdout=True)
        except Exception as e:
            logger.exception('ffmpeg error in disassemble:')
            raise

        # split_cmd = 'ffmpeg -y -i "%s" -b 0 -f mp4 -reset_timestamps 1 -map 0 -f segment -segment_frames %s "%s"' % (
        #     filepath, ','.join([str(int(i)) for i in list_frames_to_split]), output_regex)
        # logger.info('About to run: %s' % split_cmd)
        # subprocess.check_call(shlex.split(split_cmd), universal_newlines=True)

        # rename
        list_frames_to_split = [0] + list_frames_to_split
        filenames = list()
        for n in range(split_count):
            old_filename = output_regex.replace('%03d', '%03d' % n)
            new_filename = output_regex.replace('%03d', '%s__%s' %
                                                (time.strftime('%H_%M_%S', time.gmtime(list_frames_to_split[n] / fps)),
                                                 time.strftime('%H_%M_%S',
                                                               time.gmtime(list_frames_to_split[n + 1] / fps))))
            filenames.append(new_filename)
            # rename to informative name
            if os.path.isfile(new_filename):
                logger.warning('File already exists. Overwriting!: %s' % new_filename)
                os.remove(new_filename)
            os.rename(old_filename, new_filename)
            # check if in pairs, if not - delete
            if split_pairs is not None:
                start_frames = [pair[0] for pair in split_pairs]
                end_frames = [pair[1] for pair in split_pairs]
                if (list_frames_to_split[n] // fps) in start_frames and (
                            list_frames_to_split[n + 1] // fps) in end_frames:
                    # keep video
                    pass
                else:
                    os.remove(new_filename)
        Videos.upload_to_platform(project_name=project_name,
                                  project_id=project_id,
                                  dataset_name=dataset_name,
                                  dataset_id=dataset_id,
                                  remote_path=remote_path,
                                  local_path=basename)

    @staticmethod
    def upload_to_platform(project_name=None, project_id=None, dataset_name=None, dataset_id=None,
                           local_path=None, remote_path=None):

        import dtlpy as dlp
        if project_id is not None or project_name is not None:
            project = dlp.projects.get(project_name=project_name, project_id=project_id)
            dataset = project.get(dataset_name=dataset_name, dataset_id=dataset_id)
            dataset.items.upload(dataset_name=dataset_name,
                                 dataset_id=dataset_id,
                                 local_path=local_path,
                                 remote_path=remote_path,
                                 file_types=['.mp4'])
        else:
            dataset = dlp.datasets.get(dataset_name=dataset_name, dataset_id=dataset_id)
            dataset.items.upload(local_path=local_path,
                                 remote_path=remote_path,
                                 file_types=['.mp4'])
