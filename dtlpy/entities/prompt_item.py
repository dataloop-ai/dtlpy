import requests
import logging
import base64
import enum
import json
import io
import os
from typing import List, Optional

from concurrent.futures import ThreadPoolExecutor
from .. import entities, repositories
from dtlpy.services.api_client import client as client_api

logger = logging.getLogger(name='dtlpy')


class PromptType(str, enum.Enum):
    TEXT = 'application/text'
    IMAGE = 'image/*'
    AUDIO = 'audio/*'
    VIDEO = 'video/*'
    METADATA = 'metadata'


class Prompt:
    def __init__(self, key, role='user'):
        """
        Create a single Prompt. Prompt can contain multiple mimetype elements, e.g. text sentence and an image.
        :param key: unique identifier of the prompt in the item
        """
        self.key = key
        self.elements = list()
        # to avoid broken stream of json files - DAT-75653
        client_api.default_headers['x-dl-sanitize'] = '0'
        self._items = repositories.Items(client_api=client_api)
        self.metadata = {'role': role}

    def add_element(self, value, mimetype='application/text'):
        """

        :param value: url or string of the input
        :param mimetype: mimetype of the input. options: `text`, `image/*`, `video/*`, `audio/*`
        :return:
        """
        allowed_prompt_types = [prompt_type for prompt_type in PromptType]
        if mimetype not in allowed_prompt_types:
            raise ValueError(f'Invalid mimetype: {mimetype}. Allowed values: {allowed_prompt_types}')
        if mimetype == PromptType.METADATA and isinstance(value, dict):
            self.metadata.update(value)
        else:
            self.elements.append({'mimetype': mimetype,
                                  'value': value})

    def to_json(self):
        """
        Convert Prompt entity to the item json

        :return:
        """
        elements_json = [
            {
                "mimetype": e['mimetype'],
                "value": e['value'],
            } for e in self.elements if not e['mimetype'] == PromptType.METADATA
        ]
        elements_json.append({
            "mimetype": PromptType.METADATA,
            "value": self.metadata
        })
        return {
            self.key: elements_json
        }

    def _convert_stream_to_binary(self, image_url: str):
        """
        Convert a stream to binary
        :param image_url: dataloop image stream url
        :return: binary object
        """
        image_buffer = None
        if '.' in image_url and 'dataloop.ai' not in image_url:
            # URL and not DL item stream
            try:
                response = requests.get(image_url, stream=True)
                response.raise_for_status()  # Raise an exception for bad status codes

                # Check for valid image content type
                if response.headers["Content-Type"].startswith("image/"):
                    # Read the image data in chunks to avoid loading large images in memory
                    image_buffer = b"".join(chunk for chunk in response.iter_content(1024))
            except requests.exceptions.RequestException as e:
                logger.error(f"Failed to download image from URL: {image_url}, error: {e}")

        elif '.' in image_url and 'stream' in image_url:
            # DL Stream URL
            item_id = image_url.split("/stream")[0].split("/items/")[-1]
            image_buffer = self._items.get(item_id=item_id).download(save_locally=False).getvalue()
        else:
            # DL item ID
            image_buffer = self._items.get(item_id=image_url).download(save_locally=False).getvalue()

        if image_buffer is not None:
            encoded_image = base64.b64encode(image_buffer).decode()
        else:
            logger.error(f'Invalid image url: {image_url}')
            return None

        return f'data:image/jpeg;base64,{encoded_image}'

    def messages(self):
        """
        return a list of messages in the prompt item,
        messages are returned following the openai SDK format https://platform.openai.com/docs/guides/vision
        """
        messages = []
        for element in self.elements:
            if element['mimetype'] == PromptType.TEXT:
                data = {
                    "type": "text",
                    "text": element['value']
                }
                messages.append(data)
            elif element['mimetype'] == PromptType.IMAGE:
                image_url = self._convert_stream_to_binary(element['value'])
                data = {
                    "type": "image_url",
                    "image_url": {
                        "url": image_url
                    }
                }
                messages.append(data)
            elif element['mimetype'] == PromptType.AUDIO:
                raise NotImplementedError('Audio prompt is not supported yet')
            elif element['mimetype'] == PromptType.VIDEO:
                data = {
                    "type": "video_url",
                    "video_url": {
                        "url": element['value']
                    }
                }
                messages.append(data)
            else:
                raise ValueError(f'Invalid mimetype: {element["mimetype"]}')
        return messages, self.key


class PromptItem:
    def __init__(self, name, item: entities.Item = None, role_mapping=None):
        if role_mapping is None:
            role_mapping = {'user': 'item',
                            'assistant': 'annotation'}
        if not isinstance(role_mapping, dict):
            raise ValueError(f'input role_mapping must be dict. type: {type(role_mapping)}')
        self.role_mapping = role_mapping
        # prompt item name
        self.name = name
        # list of user prompts in the prompt item
        self.prompts = list()
        self.assistant_prompts = list()
        # list of assistant (annotations) prompts in the prompt item
        # Dataloop Item
        self._item: entities.Item = item
        self._messages = []
        self._annotations: entities.AnnotationCollection = None
        if item is not None:
            if 'json' not in item.mimetype or item.system.get('shebang', dict()).get('dltype') != 'prompt':
                raise ValueError('Expecting a json item with system.shebang.dltype = prompt')
            self._items = item.items
            self.fetch()
        else:
            self._items = repositories.Items(client_api=client_api)

        # to avoid broken stream of json files - DAT-75653
        self._items._client_api.default_headers['x-dl-sanitize'] = '0'

    @classmethod
    def from_messages(cls, messages: list):
        ...

    @classmethod
    def from_item(cls, item: entities.Item):
        """
        Load a prompt item from the platform
        :param item : Item object
        :return: PromptItem object
        """
        if 'json' not in item.mimetype or item.system.get('shebang', dict()).get('dltype') != 'prompt':
            raise ValueError('Expecting a json item with system.shebang.dltype = prompt')
        return cls(name=item.name, item=item)

    @classmethod
    def from_local_file(cls, filepath):
        """
        Create a new prompt item from a file
        :param filepath: path to the file
        :return: PromptItem object
        """
        if os.path.exists(filepath) is False:
            raise FileNotFoundError(f'File does not exists: {filepath}')
        if 'json' not in os.path.splitext(filepath)[-1]:
            raise ValueError(f'Expected path to json item, got {os.path.splitext(filepath)[-1]}')
        prompt_item = cls(name=filepath)
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        prompt_item.prompts = prompt_item._load_item_prompts(data=data)
        return prompt_item

    @staticmethod
    def _load_item_prompts(data):
        prompts = list()
        for prompt_key, prompt_elements in data.get('prompts', dict()).items():
            content = list()
            for element in prompt_elements:
                content.append({'value': element.get('value', dict()),
                                'mimetype': element['mimetype']})
            prompt = Prompt(key=prompt_key, role="user")
            for element in content:
                prompt.add_element(value=element.get('value', ''),
                                   mimetype=element.get('mimetype', PromptType.TEXT))
            prompts.append(prompt)
        return prompts

    @staticmethod
    def _load_annotations_prompts(annotations: entities.AnnotationCollection):
        """
        Get all the annotations in the item for the assistant messages
        """
        # clearing the assistant prompts from previous annotations that might not belong
        assistant_prompts = list()
        for annotation in annotations:
            prompt_id = annotation.metadata.get('system', dict()).get('promptId', None)
            model_info = annotation.metadata.get('user', dict()).get('model', dict())
            annotation_id = annotation.id
            if annotation.type == 'ref_image':
                prompt = Prompt(key=prompt_id, role='assistant')
                prompt.add_element(value=annotation.annotation_definition.coordinates.get('ref'),
                                   mimetype=PromptType.IMAGE)
            elif annotation.type == 'text':
                prompt = Prompt(key=prompt_id, role='assistant')
                prompt.add_element(value=annotation.annotation_definition.coordinates,
                                   mimetype=PromptType.TEXT)
            else:
                raise ValueError(f"Unsupported annotation type: {annotation.type}")

            prompt.add_element(value={'id': annotation_id,
                                      'model_info': model_info},
                               mimetype=PromptType.METADATA)
            assistant_prompts.append(prompt)
        return assistant_prompts

    def to_json(self):
        """
        Convert the entity to a platform item.

        :return:
        """
        prompts_json = {
            "shebang": "dataloop",
            "metadata": {
                "dltype": 'prompt'
            },
            "prompts": {}
        }
        for prompt in self.prompts:
            for prompt_key, prompt_values in prompt.to_json().items():
                prompts_json["prompts"][prompt_key] = prompt_values
        return prompts_json

    def to_messages(self, model_name=None, include_assistant=True):
        all_prompts_messages = dict()
        for prompt in self.prompts:
            if prompt.key not in all_prompts_messages:
                all_prompts_messages[prompt.key] = list()
            prompt_messages, prompt_key = prompt.messages()
            messages = {
                'role': prompt.metadata.get('role', 'user'),
                'content': prompt_messages
            }
            all_prompts_messages[prompt.key].append(messages)
        if include_assistant is True:
            # reload to filer model annotations
            for prompt in self.assistant_prompts:
                prompt_model_name = prompt.metadata.get('model_info', dict()).get('name')
                if model_name is not None and prompt_model_name != model_name:
                    continue
                if prompt.key not in all_prompts_messages:
                    logger.warning(
                        f'Prompt key {prompt.key} is not found in the user prompts, skipping Assistant prompt')
                    continue
                prompt_messages, prompt_key = prompt.messages()
                assistant_messages = {
                    'role': 'assistant',
                    'content': prompt_messages
                }
                all_prompts_messages[prompt.key].append(assistant_messages)
        res = list()
        for prompts in all_prompts_messages.values():
            for prompt in prompts:
                res.append(prompt)
        self._messages = res
        return self._messages

    def to_bytes_io(self):
        # Used for item upload, do not delete
        byte_io = io.BytesIO()
        byte_io.name = self.name
        byte_io.write(json.dumps(self.to_json()).encode())
        byte_io.seek(0)
        return byte_io

    def fetch(self):
        if self._item is None:
            raise ValueError('Missing item, nothing to fetch..')
        self._item = self._items.get(item_id=self._item.id)
        self._annotations = self._item.annotations.list()
        self.prompts = self._load_item_prompts(data=json.load(self._item.download(save_locally=False)))
        self.assistant_prompts = self._load_annotations_prompts(self._annotations)

    def build_context(self, nearest_items, add_metadata=None) -> str:
        """
        Create a context stream from nearest items list.
        add_metadata is a list of location in the item.metadata to add to the context, for instance ['system.document.source']
        :param nearest_items: list of item ids
        :param add_metadata: list of metadata location to add metadata to context
        :return:
        """
        if add_metadata is None:
            add_metadata = list()

        def stream_single(w_id):
            context_item = self._items.get(item_id=w_id)
            buf = context_item.download(save_locally=False)
            text = buf.read().decode(encoding='utf-8')
            m = ""
            for path in add_metadata:
                parts = path.split('.')
                value = context_item.metadata
                part = ""
                for part in parts:
                    if isinstance(value, dict):
                        value = value.get(part)
                    else:
                        value = ""

                m += f"{part}:{value}\n"
            return text, m

        pool = ThreadPoolExecutor(max_workers=32)
        context = ""
        if len(nearest_items) > 0:
            # build context
            results = pool.map(stream_single, nearest_items)
            for res in results:
                context += f"\n<source>\n{res[1]}\n</source>\n<text>\n{res[0]}\n</text>"
        return context

    def add(self,
            message: dict,
            prompt_key: str = None,
            model_info: dict = None):
        """
        add a prompt to the prompt item
        prompt: a dictionary. keys are prompt message id, values are prompt messages
        responses: a list of annotations representing responses to the prompt

        :param message:
        :param prompt_key:
        :param model_info:
        :return:
        """
        role = message.get('role', 'user')
        content = message.get('content', list())

        if self.role_mapping.get(role, 'item') == 'item':
            if prompt_key is None:
                prompt_key = str(len(self.prompts) + 1)
            # for new prompt we need a new key
            prompt = Prompt(key=prompt_key, role=role)
            for element in content:
                prompt.add_element(value=element.get('value', ''),
                                   mimetype=element.get('mimetype', PromptType.TEXT))

            # create new prompt and add to prompts
            self.prompts.append(prompt)
            if self._item is not None:
                self._item._Item__update_item_binary(_json=self.to_json())
        else:
            if prompt_key is None:
                prompt_key = str(len(self.prompts))
            assistant_message = content[0]
            assistant_mimetype = assistant_message.get('mimetype', PromptType.TEXT)
            uploaded_annotation = None

            # find if prompt
            if model_info is None:
                # dont search for existing if there's no model information
                existing_prompt = None
            else:
                existing_prompts = list()
                for prompt in self.assistant_prompts:
                    prompt_id = prompt.key
                    model_name = prompt.metadata.get('model_info', dict()).get('name')
                    if prompt_id == prompt_key and model_name == model_info.get('name'):
                        # TODO how to handle multiple annotations
                        existing_prompts.append(prompt)
                if len(existing_prompts) > 1:
                    assert False, "shouldn't be here! more than 1 annotation for a single model"
                elif len(existing_prompts) == 1:
                    # found model annotation to upload
                    existing_prompt = existing_prompts[0]
                else:
                    # no annotation found
                    existing_prompt = None

            if existing_prompt is None:
                prompt = Prompt(key=prompt_key)
                if assistant_mimetype == PromptType.TEXT:
                    annotation_definition = entities.FreeText(text=assistant_message.get('value'))
                    prompt.add_element(value=annotation_definition.to_coordinates(None),
                                       mimetype=PromptType.TEXT)
                elif assistant_mimetype == PromptType.IMAGE:
                    annotation_definition = entities.RefImage(ref=assistant_message.get('value'))
                    prompt.add_element(value=annotation_definition.to_coordinates(None).get('ref'),
                                       mimetype=PromptType.IMAGE)
                else:
                    raise NotImplementedError('Only images of mimetype image and text are supported')
                metadata = {'system': {'promptId': prompt_key},
                            'user': {'model': model_info}}
                prompt.add_element(mimetype=PromptType.METADATA,
                                   value={"model_info": model_info})

                existing_annotation = entities.Annotation.new(item=self._item,
                                                              metadata=metadata,
                                                              annotation_definition=annotation_definition)
                uploaded_annotation = existing_annotation.upload()
                prompt.add_element(mimetype=PromptType.METADATA,
                                   value={"id": uploaded_annotation.id})
                existing_prompt = prompt
                self.assistant_prompts.append(prompt)

            existing_prompt_element = [element for element in existing_prompt.elements if
                                       element['mimetype'] != PromptType.METADATA][-1]
            existing_prompt_element['value'] = assistant_message.get('value')
            if uploaded_annotation is None:
                # Creating annotation with old dict to match platform dict
                annotation_definition = entities.FreeText(text='')
                metadata = {'system': {'promptId': prompt_key},
                            'user': {'model': existing_prompt.metadata.get('model_info')}}
                annotation = entities.Annotation.new(item=self._item,
                                                     metadata=metadata,
                                                     annotation_definition=annotation_definition
                                                     )
                annotation.id = existing_prompt.metadata['id']
                # set the platform dict to match the old annotation for the dict difference check, otherwise it won't
                # update
                annotation._platform_dict = annotation.to_json()
                # update the annotation with the new text
                annotation.annotation_definition.text = existing_prompt_element['value']
                self._item.annotations.update(annotation)

    def update(self):
        """
        Update the prompt item in the platform. 
        """
        if self._item is not None:
            self._item._Item__update_item_binary(_json=self.to_json())
            self._item = self._item.update()
        else:
            raise ValueError('Cannot update PromptItem without an item.')

    # Properties
    @property
    def item(self) -> Optional['entities.Item']:
        """
        Get the underlying Item object.

        :return: The Item object associated with this PromptItem, or None.
        :rtype: Optional[dtlpy.entities.Item]
        """
        return self._item

    @item.setter
    def item(self, item: Optional['entities.Item']):
        """
        Set the underlying Item object.

        :param item: The Item object to associate with this PromptItem, or None.
        :type item: Optional[dtlpy.entities.Item]
        """
        if item is not None and not isinstance(item, entities.Item):
            raise ValueError(f"Expected dtlpy.entities.Item or None, got {type(item)}")
        self._item = item


    @property
    def metadata(self) -> dict:
        """
        Get the metadata from the underlying Item object.

        :return: Metadata dictionary from the item, or empty dict if no item exists.
        :rtype: dict
        """
        if self._item is not None:
            return self._item.metadata
        else:
            raise ValueError('No item found, cannot get metadata, to set item use prompt_item.item = item')