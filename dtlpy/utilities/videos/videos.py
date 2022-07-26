import asyncio
import time
import types

import numpy as np
import os
import logging
import dtlpy as dl
import shutil

logger = logging.getLogger(name='dtlpy')


##########
# Videos #
##########
class Videos:
    def __init__(self):
        pass

    @staticmethod
    def get_info(filepath):
        try:
            import ffmpeg
        except ImportError:
            logger.error(
                'Import Error! Cant import ffmpeg. '
                'Annotations operations will be limited. import manually and fix errors')
            raise
        probe = ffmpeg.probe(filepath)
        return probe

    @staticmethod
    def get_max_object_id(item):
        max_object_id = 1
        annotations_list = item.annotations.list().annotations
        if len(annotations_list) < 1:
            return 1
        for annotation in annotations_list:
            if annotation.object_id is not None:
                current_object_id = int(annotation.object_id)
                if current_object_id > max_object_id:
                    max_object_id = current_object_id
        return max_object_id

    @staticmethod
    def video_snapshots_generator(item_id=None, item=None, frame_interval=30, image_ext="png"):
        futures = Videos._async_video_snapshots_generator(item_id=item_id,
                                                          item=item,
                                                          frame_interval=frame_interval,
                                                          image_ext=image_ext)
        loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(futures)
        finally:
            try:
                loop.run_until_complete(loop.shutdown_asyncgens())
            finally:
                asyncio.set_event_loop(None)
                loop.close()

    @staticmethod
    async def _async_video_snapshots_generator(item_id=None, item=None, frame_interval=30, image_ext="png"):
        """
        Create video-snapshots

        :param item_id: item id for the video
        :param item: item id for the video
        :param frame_interval: number of frames to take next snapshot
        :param image_ext: png/jpg
        :return: the uploaded items
        """
        if item_id is not None:
            item = dl.items.get(item_id=item_id)

        if item is None:
            raise ValueError('Missing input item (or item_id)')

        if not isinstance(frame_interval, int):
            raise AttributeError('frame_interval is mast to be integer')

        if "video" not in item.mimetype:
            raise AttributeError("Got {} file type but only video files are supported".format(item.mimetype))

        video_path = item.download()

        # Get the time for single frame from metadata (duration/# of frames)
        if 'system' in item.metadata and \
                'ffmpeg' in item.metadata['system'] and \
                'duration' in item.metadata['system']['ffmpeg'] and \
                'nb_frames' in item.metadata['system']['ffmpeg']:
            nb_frames = int(item.metadata["system"]["ffmpeg"]["nb_frames"])
            duration = float(item.metadata["system"]["ffmpeg"]["duration"])
            video_fps = duration / nb_frames
        else:
            try:
                import cv2
            except (ImportError, ModuleNotFoundError):
                logger.error(
                    'Import Error! Cant import cv2. '
                    'Annotations operations will be limited. import manually and fix errors')
                raise

            video = cv2.VideoCapture(video_path)
            video_fps = video.get(cv2.CAP_PROP_FPS)
            nb_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = video_fps * nb_frames

        images_path = Videos.disassemble(filepath=video_path, frame_interval=frame_interval, image_ext=image_ext)
        snapshots_items = list()
        try:
            # rename files
            images = []
            video_basename = os.path.basename(video_path)
            for f in os.listdir(images_path):
                images.append(f)
            for image in images:
                image_split_name, ext = os.path.splitext(image)
                try:
                    frame = int(image_split_name) * frame_interval
                    file_frame_name = "{}.frame.{}{}".format(video_basename, frame, ext)
                    full_path = os.path.join(images_path, file_frame_name)
                    os.rename(os.path.join(images_path, image),
                              full_path)
                except Exception as e:
                    logger.debug("Rename {} has been failed: {}".format(os.path.join(images_path, image), e))

                remote_path = os.path.join(os.path.split(item.filename)[0], "snapshots")
                remote_url = '/items/{}/snapshots'.format(item.id)
                to_upload = open(full_path, 'rb')
                try:
                    response = await item._client_api.upload_file_async(to_upload=to_upload,
                                                                        item_type='file',
                                                                        item_size=os.stat(full_path).st_size,
                                                                        remote_url=remote_url,
                                                                        uploaded_filename=file_frame_name,
                                                                        remote_path=remote_path)
                except Exception:
                    raise
                finally:
                    to_upload.close()
                if response.ok:
                    snapshots_items.append(item.from_json(response.json(), item._client_api))
                else:
                    raise dl.PlatformException(response)

            # classification tpe annotation creation for each file
            builder = item.annotations.builder()
            annotation_itemlinks = []

            max_object_id = Videos().get_max_object_id(item=item)
            for snapshot_item in snapshots_items:
                max_object_id += 1
                item_frame = snapshot_item.name.rsplit("frame.", 1)[1].split(".")[0]
                if item_frame.isnumeric():
                    item_time = int(item_frame) * video_fps
                else:
                    item_frame = item_time = 0

                snapshot_item.metadata["system"]["itemLinks"] = [{"type": "snapshotFrom",
                                                                  "itemId": item.id,
                                                                  "frame": item_frame,
                                                                  "time": item_time}]

                annotation_itemlinks.append({"type": "snapshotTo",
                                             "itemId": snapshot_item.id,
                                             "frame": item_frame,
                                             "time": item_time})

                snapshot_item.update(system_metadata=True)
                annotation_definition = dl.Classification(label="Snapshot")
                builder.add(annotation_definition=annotation_definition,
                            frame_num=int(item_frame),
                            end_frame_num=nb_frames if int(item_frame) + int(video_fps) > nb_frames else int(
                                item_frame) + int(video_fps),
                            start_time=item_time,
                            end_time=duration if item_time + 1 > duration else item_time + 1,
                            object_id=max_object_id)

            annotations = item.annotations.upload(annotations=builder)

            # update system metadata for annotations
            count = 0
            for annotation in annotations:
                annotation.metadata["system"]["itemLinks"] = [annotation_itemlinks[count]]
                count += 1

            annotations.update(system_metadata=True)
        except Exception as err:
            logger.exception(err)
        finally:
            if os.path.isdir(images_path):
                shutil.rmtree(images_path)
            return snapshots_items

    @staticmethod
    def disassemble(filepath, fps=None, frame_interval=None, loglevel='panic', image_ext='jpg'):
        """
        Disassemble video to images

        :param filepath: input video filepath
        :param fps: rate of disassemble. e.g if 1 frame per second fps is 1. if None all frames will be extracted
        :param frame_interval: take image every frame # (if exists function ignore fps)
        :param image_ext: png/jpg
        :param loglevel: ffmpeg loglevel
        :return:
        """
        try:
            import ffmpeg
        except ImportError:
            logger.error(
                'Import Error! Cant import ffmpeg. '
                'Annotations operations will be limited. import manually and fix errors')
            raise
        # get video information
        video_props = Videos.get_info(filepath)
        if 'system' in video_props and \
                'nb_frames' in video_props['system'][0]:
            nb_frames = video_props['streams'][0]['nb_frames']
        else:
            try:
                import cv2
            except (ImportError, ModuleNotFoundError):
                logger.error(
                    'Import Error! Cant import cv2. '
                    'Annotations operations will be limited. import manually and fix errors')
                raise
            nb_frames = int(cv2.VideoCapture(filepath).get(cv2.CAP_PROP_FRAME_COUNT))

        if not os.path.isfile(filepath):
            raise IOError('File doesnt exists: {}'.format(filepath))
        basename, ext = os.path.splitext(filepath)
        # create folder for the frames
        if os.path.exists(basename):
            shutil.rmtree(basename)

        os.makedirs(basename, exist_ok=True)

        if fps is None:
            try:
                fps = eval(video_props['streams'][0]['avg_frame_rate'])
            except ZeroDivisionError:
                fps = 0
        num_of_zeros = len(str(nb_frames))
        # format the output filename
        output_regex = os.path.join(basename, '%0{}d.{}'.format(num_of_zeros, image_ext))

        try:
            if frame_interval is not None:
                frame_number = 0
                select = ""
                while frame_number < nb_frames:
                    if select != "":
                        select += '+'
                    select += 'eq(n\\,{})'.format(frame_number)
                    frame_number += frame_interval
                stream = ffmpeg.input(filepath, **{'loglevel': loglevel}).output(output_regex,
                                                                                 **{'start_number': '0',
                                                                                    'vf': 'select=\'{}'.format(select),
                                                                                    'vsync': 'vfr'})
            else:
                stream = ffmpeg.input(filepath, **{'loglevel': loglevel}).output(output_regex,
                                                                                 **{'start_number': '0',
                                                                                    'r': str(fps)})

            ffmpeg.overwrite_output(stream).run()
        except Exception:
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
        try:
            import ffmpeg
        except ImportError:
            logger.error(
                'Import Error! Cant import ffmpeg. '
                'Annotations operations will be limited. import manually and fix errors')
            raise
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
        try:
            import ffmpeg
        except ImportError:
            logger.error(
                'Import Error! Cant import ffmpeg. '
                'Annotations operations will be limited. import manually and fix errors')
            raise
        # https://www.ffmpeg.org/ffmpeg-formats.html#Examples-9

        if not os.path.isfile(filepath):
            raise IOError('File doesnt exists: {}'.format(filepath))
        logger.info('Extracting video information...')
        # call to ffmpeg to get frame rate
        probe = Videos.get_info(filepath)
        fps = eval(probe['streams'][0]['avg_frame_rate'])
        n_frames = eval(probe['streams'][0]['nb_frames'])
        video_length = eval(probe['streams'][0]['duration'])
        logger.info('Video frame rate: {}[fps]'.format(fps))
        logger.info('Video number of frames: {}'.format(n_frames))
        logger.info('Video length in seconds: {}[s]'.format(video_length))

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
        output_regex = os.path.join(basename, '%%03d.mp4')
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
        except Exception:
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
                logger.warning('File already exists. Overwriting!: {}'.format(new_filename))
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
