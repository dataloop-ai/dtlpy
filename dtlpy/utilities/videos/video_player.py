import logging
import tkinter
import json
import time
import cv2
import os
import PIL.ImageTk
import PIL.Image
import numpy as np

from dtlpy import PlatformInterface
from dtlpy.utilities.annotations import VideoAnnotation


class VideoPlayer:
    """
    Video Player GUI.
    """

    def __init__(self, project_name=None, project_id=None,
                 dataset_name=None, dataset_id=None,
                 item_filepath=None, item_id=None):
        self.logger = logging.getLogger('dataloop.videoplayer')
        # init tkinter window
        self.window = tkinter.Tk()
        self.window.title('Dataloop Player')

        self.video_source = None
        self.video_annotations = None
        self.local_annotations_filename = None
        self.classes = None
        self.project = None
        self.dataset = None
        self.item = None
        self.platform_interface = PlatformInterface()
        #############################
        # load video and annotation #
        #############################
        self.platform_params = {'project_name': project_name, 'project_id': project_id,
                                'dataset_name': dataset_name, 'dataset_id': dataset_id,
                                'item_filepath': item_filepath, 'item_id': item_id}
        self.from_platform()

        # load video
        self.photo = None
        self.vid = None
        self.load_video()

        # canvas to put frames on
        self.canvas = tkinter.Canvas(self.window, width=self.vid.width, height=self.vid.height)
        self.canvas.pack()
        self.canvas.bind('<Configure>', self._resize_image)

        ########################
        # create buttons panel #
        ########################
        self.window_width = self.vid.width
        self.window_height = self.vid.height
        self.buttons_window = tkinter.Tk()
        self.buttons_window.title('Controls')
        self.buttons_window.geometry()

        button_frame = tkinter.Frame(self.buttons_window)
        button_frame.grid(sticky="W", row=0, column=0)

        ###############
        # information #
        ###############
        txt_dataset_name = tkinter.Label(button_frame)
        txt_dataset_name.grid(sticky="W", row=2, column=0, columnspan=10)
        txt_dataset_name.configure(text='Dataset name: %s' % self.dataset.name)
        txt_item_name = tkinter.Label(button_frame)
        txt_item_name.grid(sticky="W", row=3, column=0, columnspan=10)
        txt_item_name.configure(text='Item name: %s' % self.item.name)
        ###############
        # Exit Button #
        ###############
        btn_exit = tkinter.Button(button_frame, text="Close", command=self.close).grid(sticky="W", row=17, column=0)
        ################
        # Play / Pause #
        ################
        btn_play = tkinter.Button(button_frame, text="Play", command=self.play).grid(sticky="W", row=4, column=0)
        btn_pause = tkinter.Button(button_frame, text="Pause", command=self.pause).grid(sticky="W", row=4, column=1)
        ###################
        # Next prev frame #
        ###################
        btn_next_frame = tkinter.Button(button_frame, text="Next frame", command=self.next_frame).grid(sticky="W",
                                                                                                       row=4,
                                                                                                       column=2)
        btn_prev_frame = tkinter.Button(button_frame, text="Prev frame", command=self.prev_frame).grid(sticky="W",
                                                                                                       row=4,
                                                                                                       column=3)
        btn_toggle_frame_num = tkinter.Button(button_frame, text="Show/hide frame number",
                                              command=self.toggle_show_frame_number).grid(sticky="W", row=5, column=0,
                                                                                          columnspan=10)
        btn_toggle_annotations = tkinter.Button(button_frame, text="Show/hide annotations",
                                                command=self.toggle_show_annotations) \
            .grid(sticky="W", row=6, column=0, columnspan=10)
        btn_toggle_label = tkinter.Button(button_frame, text="Show/hide label", command=self.toggle_show_label) \
            .grid(sticky="W", row=7, column=0, columnspan=10)
        #################
        # Export button #
        #################
        tkinter.Button(button_frame, text="Export video", command=self.export) \
            .grid(sticky="W", row=16, column=2, columnspan=2)
        ################
        # Apply button #
        ################
        btn_apply_offset_fix = tkinter.Button(button_frame, text="Apply offset fix", command=self.apply_offset_fix) \
            .grid(sticky="W", row=16, column=0, columnspan=2)
        btn_reset = tkinter.Button(button_frame, text="Reset", command=self.reset) \
            .grid(sticky="W", row=4, column=4)
        #####################
        # Annotation Offset #
        #####################
        tkinter.Label(button_frame, text="Annotation offset (in frames):") \
            .grid(sticky="W", row=13, column=0,
                  columnspan=10)
        self.annotations_offset_entry = tkinter.Entry(button_frame)
        self.annotations_offset_entry.bind("<Return>", self.set_annotation_offset)
        self.annotations_offset_entry.grid(sticky="W", row=14, column=0, columnspan=10)
        self.annotation_offset_text = tkinter.Label(button_frame)
        self.annotation_offset_text.grid(sticky="W", row=15, column=0, columnspan=10)
        ##############
        # Set Frames #
        ##############
        tkinter.Label(button_frame, text="Set frame (in frames):") \
            .grid(sticky="W", row=10, column=0, columnspan=10)
        self.current_frame_entry = tkinter.Entry(button_frame)
        self.current_frame_entry.bind("<Return>", self.set_current_frame)
        self.current_frame_entry.grid(sticky="W", row=11, column=0, columnspan=10)
        self.current_frame_text = tkinter.Label(button_frame)
        self.current_frame_text.grid(sticky="W", row=12, column=0, columnspan=10)
        #########################
        # Timestamp information #
        #########################
        self.frame_timestamp_text = tkinter.Label(button_frame)
        self.frame_timestamp_text.grid(sticky="W", row=8, column=0, columnspan=10)
        self.annotations_timestamp_text = tkinter.Label(button_frame)
        self.annotations_timestamp_text.grid(sticky="W", row=9, column=0, columnspan=10)

        ##############
        # Parameters #
        ##############
        self.delay = None
        self.annotations_timestamp = None
        self.annotations_offset = None
        self.annotations_timestamp = None
        self.show_frame_num = True
        self.show_annotations = True
        self.show_label = True
        self.playing = False
        self.init_all_params()
        self.show_frame(0)

        ###############
        # Start video #
        ###############
        self.delay = int(1000 * 1 / self.vid.fps)
        self.update()
        button_frame.lift()
        self.window.mainloop()

    def _resize_image(self, event):
        """
        Resize frame to match window size
        :param event:
        :return:
        """
        self.window_width = event.width
        self.window_height = event.height

    def reset(self):
        """
        Reset video and annotation
        :return:
        """
        self.from_platform()
        self.load_video()
        self.init_all_params()
        self.show_frame(0)

    def export(self):
        """
        Create an annotated video saved to file
        :return:
        """
        from tkinter import ttk
        # start progress bar
        p, ext = os.path.splitext(self.video_source)
        output_filename = p + '_out.mp4'

        # read input video
        reader = cv2.VideoCapture(self.video_source)
        width = int(reader.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(reader.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = int(reader.get(cv2.CAP_PROP_FPS))
        encoding = int(reader.get(cv2.CAP_PROP_FOURCC))
        n_frames = int(reader.get(cv2.CAP_PROP_FRAME_COUNT))
        writer = cv2.VideoWriter(output_filename, cv2.VideoWriter_fourcc(*'MP4V'), fps, (width, height))

        # create popup
        popup = tkinter.Toplevel()
        tkinter.Label(popup, text='Exporting to\n%s' % output_filename).grid(row=0, column=0)
        progress_var = tkinter.DoubleVar()
        progress_bar = ttk.Progressbar(popup, variable=progress_var, maximum=n_frames)
        progress_bar.grid(row=1, column=0)  # .pack(fill=tk.X, expand=1, side=tk.BOTTOM)
        popup.pack_slaves()

        i_frame = 0
        while reader.isOpened():
            popup.update()
            ret, frame = reader.read()
            if not ret:
                break
            # mark on frame
            annotations_timestamp = i_frame / fps
            annotation = self.video_annotations.get_snapshots_by_time(second=annotations_timestamp)
            for ann in annotation:
                top_left = (int(ann['data'][0]['x']), int(ann['data'][0]['y']))
                bottom_right = (int(ann['data'][1]['x']), int(ann['data'][1]['y']))
                color = self.get_class_color(ann['label'])
                frame = cv2.rectangle(frame, top_left, bottom_right, color=color, thickness=2)
                frame = cv2.putText(frame, text=ann['label'], org=top_left, color=color,
                                    fontFace=cv2.FONT_HERSHEY_DUPLEX, fontScale=2, thickness=2)

            # write
            writer.write(frame)
            i_frame += 1
            progress_var.set(i_frame)
        reader.release()
        writer.release()
        popup.destroy()

    def load_video(self):
        """
        Load VideoCapture instance
        :return:
        """
        self.vid = VideoCapture(self.video_source)

    def init_all_params(self):
        """
        Reset all initial variables
        :return:
        """
        self.annotations_timestamp = 0
        self.annotations_offset = 0
        self.annotation_offset_text.configure(text='Current: %d' % self.annotations_offset)
        self.annotations_timestamp_text.configure(text='Annotation timestamp:\n %d' % self.annotations_timestamp)
        self.annotations_timestamp_text.grid(sticky="W", row=9, column=0, columnspan=10)
        # set text frames
        self.annotations_offset_entry.delete(0, 'end')
        self.annotations_offset_entry.insert(0, str(self.annotations_offset))
        self.current_frame_entry.delete(0, 'end')
        self.current_frame_entry.insert(0, str(self.vid.frame_number))

    def from_local(self):
        """
        Load local video and annotation
        :return:
        """
        self.video_annotations = VideoAnnotation()
        if self.local_annotations_filename is not None:
            with open(self.local_annotations_filename, 'r') as f:
                annotations = json.load(f)
            self.video_annotations.annotations = annotations['annotations']

    def from_platform(self):
        """
        Load video and annotations from platform
        :return:
        """
        project_name = self.platform_params['project_name']
        project_id = self.platform_params['project_id']
        dataset_name = self.platform_params['dataset_name']
        dataset_id = self.platform_params['dataset_id']
        item_filepath = self.platform_params['item_filepath']
        item_id = self.platform_params['item_id']

        # load remote item
        self.project = self.platform_interface.projects.get(project_name=project_name, project_id=project_id)
        if self.project is None:
            self.logger.exception('Project doesnt exists. name: %s, id: %s', project_name, project_id)
            raise ValueError('Project doesnt exists. name: %s, id: %s' % (project_name, project_id))
        self.dataset = self.project.datasets.get(dataset_name=dataset_name, dataset_id=dataset_id)
        if self.dataset is None:
            self.logger.exception('Dataset doesnt exists. name: %s, id: %s', dataset_name, dataset_id)
            raise ValueError('Dataset doesnt exists. name: %s, id: %s' % (dataset_name, dataset_id))
        self.item = self.dataset.items.get(filepath=item_filepath, item_id=item_id)
        if self.item is None:
            self.logger.exception('Item doesnt exists. name: %s, id: %s', item_filepath, item_id)
            raise ValueError('Item doesnt exists. name: %s, id: %s' % (item_filepath, item_id))
        self.classes = self.dataset.classes
        _, ext = os.path.splitext(self.item.filename[1:])
        video_filename = os.path.join(self.dataset.__get_local_path__(), self.item.filename[1:])
        if not os.path.isdir(os.path.dirname(video_filename)):
            os.makedirs(os.path.dirname(video_filename))
        if not os.path.isfile(video_filename):
            self.dataset.items.download(item_id=self.item.id, local_path=video_filename)
        annotations = [ann.entity_dict for ann in self.item.annotations.list()]
        self.video_source = video_filename
        self.video_annotations = VideoAnnotation()
        self.video_annotations.annotations = annotations

    def close(self):
        """
        Terminate window and application
        :return:
        """
        self.window.destroy()
        self.buttons_window.destroy()

    def set_annotation_offset(self, entry):
        """
        Set annotations offset to video start time
        :param entry:
        :return:
        """
        self.annotations_offset = int(self.annotations_offset_entry.get())
        self.annotation_offset_text.configure(text='Current: %d' % self.annotations_offset)

    def set_current_frame(self, entry):
        """
        Go to specific frame
        :param entry:
        :return:
        """
        input_frame = int(self.current_frame_entry.get())
        self.show_frame(frame_number=input_frame)

    def toggle_show_frame_number(self):
        """
        Show/hide frame number on frames
        :return:
        """
        self.show_frame_num = not self.show_frame_num

    def toggle_show_annotations(self):
        """
        Show/hide annotations from frame
        :return:
        """
        self.show_annotations = not self.show_annotations

    def toggle_show_label(self):
        """
        Show/hide label per annotations
        :return:
        """
        self.show_label = not self.show_label

    def get_class_color(self, label):
        """
        Color of label
        :param label:
        :return:
        """
        if label not in self.classes:
            print('[WARNING] label not in dataset labels: %s' % label)
            return (255, 0, 0)
        color = self.classes[label]
        if isinstance(color, str):
            if color.startswith('rgb'):
                color = tuple(eval(color.lstrip('rgb')))
            elif color.startswith('#'):
                color = tuple(int(color.lstrip('#')[i:i + 2], 16) for i in (0, 2, 4))
            else:
                print('[WARNING] Unknown color scheme: %s' % color)
                color = (255, 0, 0)
        return color

    def get_annotations(self, frame):
        """
        Get all annotations of frame
        :param frame:
        :return:
        """
        self.annotations_timestamp = (self.vid.frame_number + self.annotations_offset) / self.vid.fps
        annotation = self.video_annotations.get_snapshots_by_time(second=self.annotations_timestamp)
        timestamps_list = list()
        for ann in annotation:
            if ann['type'] == 'box':
                top_left = (int(ann['data'][0]['x']), int(ann['data'][0]['y']))
                bottom_right = (int(ann['data'][1]['x']), int(ann['data'][1]['y']))
                color = self.get_class_color(ann['label'])
                frame = cv2.rectangle(frame, top_left, bottom_right, color=color, thickness=2)
                if self.show_label:
                    text = '%s-%s' % (ann['label'], ','.join(ann['attributes']))
                    frame = cv2.putText(frame, text=text, org=top_left, color=color,
                                        fontFace=cv2.FONT_HERSHEY_DUPLEX, fontScale=1, thickness=2)
                timestamps_list.append(str(ann['startTime']))
            elif ann['type'] == 'point':
                x = int(ann['data']['x'])
                y = int(ann['data']['y'])
                color = self.get_class_color(ann['label'])
                frame = cv2.circle(frame, center=(x, y),radius=5, color=color, thickness=2)
                if self.show_label:
                    text = '%s-%s' % (ann['label'], ','.join(ann['attributes']))
                    frame = cv2.putText(frame, text=text, org=(x, y), color=color, fontFace=cv2.FONT_HERSHEY_DUPLEX, fontScale=1, thickness=2)
                timestamps_list.append(str(ann['startTime']))

        self.annotations_timestamp_text.configure(text='Annotations timestamp[s]:\n%s' % '\n'.join(timestamps_list))
        self.annotations_timestamp_text.grid(sticky="W", row=9, column=0)
        return frame

    def play(self):
        """
        Start play move
        :return:
        """
        self.playing = True

    def pause(self):
        """
        Pause movie
        :return:
        """
        self.playing = False

    def next_frame(self):
        """
        Get next frame
        :return:
        """
        self.show_frame()

    def prev_frame(self):
        """
        Get previous frame
        :return:
        """
        self.show_frame(self.vid.frame_number - 1)

    def apply_offset_fix(self):
        """
        Apply offset to platform
        :return:
        """
        # delete annotations from platform
        for annotation in self.video_annotations.annotations:
            self.item.annotations.delete(annotations_id=annotation.id)

        # apply annotations fix
        new_annotations = list()
        for annotation in self.video_annotations.annotations:
            new_annotation = annotation.copy()
            for i in range(len(new_annotation['metadata']['snapshots_'])):
                new_annotation['metadata']['snapshots_'][i]['startTime'] -= (self.annotations_offset / self.vid.fps)
                new_annotation['metadata']['snapshots_'][i]['frameNum'] = int(
                    new_annotation['metadata']['snapshots_'][i]['startTime'] * self.vid.fps)
            new_annotations.append(json.dumps(new_annotation))

        # upload annotations
        self.item.annotation.upload(annotation=[new_annotations])

    def show_frame(self, frame_number=None):
        """
        Get a frame from the video source
        :param frame_number:
        :return:
        """
        ret, frame = self.vid.get_frame(frame_number)
        if ret:
            if self.show_annotations:
                frame = self.get_annotations(frame)
            if self.show_frame_num:
                text = '%d - %d' % (self.vid.frame_number, np.round(self.annotations_timestamp * self.vid.fps))
                frame = cv2.putText(frame, text=text, org=(100, 100), color=(0, 0, 255),
                                    fontFace=cv2.FONT_HERSHEY_DUPLEX, fontScale=2, thickness=3)
            self.photo = PIL.ImageTk.PhotoImage(
                image=PIL.Image.fromarray(frame).resize((self.window_width, self.window_height)))
            self.canvas.create_image(0, 0, image=self.photo, anchor=tkinter.NW)
            # set timestamp
            self.current_frame_text.configure(text='Frame number:\n%d' % self.vid.frame_number)
            self.current_frame_text.grid(sticky="W", row=12, column=0, columnspan=10)
            self.frame_timestamp_text.configure(text='Frame timestamp[s]:\n%f' % (self.vid.frame_number / self.vid.fps))
            self.frame_timestamp_text.grid(sticky="W", row=8, column=0, columnspan=10)

    def update(self):
        """
        Playing the movie. Get frames at the FPS and show
        :return:
        """
        tic = time.time()
        if self.playing:
            self.show_frame()
        add_delay = np.maximum(1, self.delay - int(1000 * (time.time() - tic)))
        self.window.after(ms=add_delay, func=self.update)


class VideoCapture:
    """
    Video class using cv2 to play video
    """

    def __init__(self, source=0):
        # Open the video source
        self.vid = cv2.VideoCapture(source)
        if not self.vid.isOpened():
            raise ValueError("Unable to open video source", source)

        # Get video source width and height
        self.width = self.vid.get(cv2.CAP_PROP_FRAME_WIDTH)
        self.height = self.vid.get(cv2.CAP_PROP_FRAME_HEIGHT)
        self.fps = self.vid.get(cv2.CAP_PROP_FPS)
        self.frame_number = self.vid.get(cv2.CAP_PROP_POS_FRAMES)

    def get_frame(self, frame_number=None):
        """
        get the frame from video
        :param frame_number:
        :return:
        """
        if self.vid.isOpened():
            if self.frame_number is None:
                self.frame_number = self.vid.get(cv2.CAP_PROP_POS_FRAMES)
            else:
                self.frame_number += 1
            if frame_number is not None:
                self.frame_number = frame_number
                self.vid.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            ret, frame = self.vid.read()

            if ret:
                # Return a boolean success flag and the current frame converted to BGR
                return (ret, cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            else:
                return (ret, None)
        else:
            return (False, None)

    # Release the video source when the object is destroyed
    def __del__(self):
        if self.vid.isOpened():
            self.vid.release()


if __name__ == '__main__':
    def test():
        v = VideoPlayer(project_name='Feb19_shelf_zed', dataset_name='try1', item_id='5c922994507c2b001cb2e5ce')
    test()
