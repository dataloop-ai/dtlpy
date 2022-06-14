# from torch.utils.tensorboard import SummaryWriter, FileWriter
# from tensorboard.compat.proto.event_pb2 import Event, SessionLog
# import time
#
#
# class DtlpyFileWrite(FileWriter):
#     def __init__(self, snapshot, *args, **kwargs):
#         self.snapshot = snapshot
#         super(DtlpyFileWrite, self).__init__(*args, **kwargs)
#
#     def add_event(self, event, step=None, walltime=None):
#         event: Event
#         event.wall_time = time.time() if walltime is None else walltime
#         if step is not None:
#             # Make sure step is converted from numpy or other formats
#             # since protobuf might not convert depending on version
#             event.step = int(step)
#         self.event_writer.add_event(event)
#         # print(event)
#         # print(event.step)
#         # print(event.SerializeToString())
#         dtlpy_records = list()
#         for v in event.summary.value:
#             dtlpy_records.append({'time': event.wall_time,
#                                   'step': event.step,
#                                   'tag': v.tag,
#                                   'value': v.simple_value,
#                                   'image': v.image.encoded_image_string,
#                                   'string': v.tensor.string_val,
#                                   'plugin_name': v.metadata.plugin_data.plugin_name})
#         print(dtlpy_records)
#         # self.snapshot.add_event(event)
#
#
# class DtlpySummaryWriter(SummaryWriter):
#     def __init__(self, snapshot, *args, **kwargs):
#         self.snapshot = snapshot
#         super(DtlpySummaryWriter, self).__init__(*args, **kwargs)
#
#     def _get_file_writer(self):
#         """Returns the default FileWriter instance. Recreates it if closed."""
#         print(self.snapshot)
#         if self.all_writers is None or self.file_writer is None:
#             self.file_writer = DtlpyFileWrite(snapshot=self.snapshot,
#                                               log_dir=self.log_dir,
#                                               max_queue=self.max_queue,
#                                               flush_secs=self.flush_secs,
#                                               filename_suffix=self.filename_suffix)
#             self.all_writers = {self.file_writer.get_logdir(): self.file_writer}
#             if self.purge_step is not None:
#                 most_recent_step = self.purge_step
#                 self.file_writer.add_event(
#                     Event(step=most_recent_step, file_version='brain.Event:2'))
#                 self.file_writer.add_event(
#                     Event(step=most_recent_step, session_log=SessionLog(status=SessionLog.START)))
#                 self.purge_step = None
#         return self.file_writer
