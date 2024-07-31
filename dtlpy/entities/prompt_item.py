import logging
import enum
import json
import os.path
from dtlpy import entities, repositories
from dtlpy.services.api_client import client as client_api
import base64
import requests

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
        if not isinstance(value, str) and mimetype != PromptType.METADATA:
            raise ValueError(f'Expected str for Prompt element value, got {type(value)} instead')
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
            } for e in self.elements
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
                raise NotImplementedError('Video prompt is not supported yet')
            else:
                raise ValueError(f'Invalid mimetype: {element["mimetype"]}')
        return messages, self.key


class PromptItem:
    def __init__(self, name, item: entities.Item = None):
        # prompt item name
        self.name = name
        # list of user prompts in the prompt item
        self.prompts = list()
        # list of assistant (annotations) prompts in the prompt item
        self.assistant_prompts = dict()
        # Dataloop Item
        self._item = None

    @classmethod
    def from_item(cls, item: entities.Item):
        """
        Load a prompt item from the platform
        :param item : Item object
        :return: PromptItem object
        """
        if 'json' not in item.mimetype or item.system.get('shebang', dict()).get('dltype') != 'prompt':
            raise ValueError('Expecting a json item with system.shebang.dltype = prompt')
        # Not using `save_locally=False` to use the from_local_file method
        item_file_path = item.download()
        prompt_item = cls.from_local_file(file_path=item_file_path)
        if os.path.exists(item_file_path):
            os.remove(item_file_path)
        prompt_item._item = item
        return prompt_item

    @classmethod
    def from_local_file(cls, file_path):
        """
        Create a new prompt item from a file
        :param file_path: path to the file
        :return: PromptItem object
        """
        if os.path.exists(file_path) is False:
            raise FileNotFoundError(f'File does not exists: {file_path}')
        if 'json' not in os.path.splitext(file_path)[-1]:
            raise ValueError(f'Expected path to json item, got {os.path.splitext(file_path)[-1]}')
        prompt_item = cls(name=file_path)
        with open(file_path, 'r') as f:
            data = json.load(f)
        for prompt_key, prompt_values in data.get('prompts', dict()).items():
            prompt = Prompt(key=prompt_key)
            for val in prompt_values:
                if val['mimetype'] == PromptType.METADATA:
                    _ = val.pop('mimetype')
                    prompt.add_element(value=val, mimetype=PromptType.METADATA)
                else:
                    prompt.add_element(mimetype=val['mimetype'], value=val['value'])
            prompt_item.add_prompt(prompt=prompt, update_item=False)
        return prompt_item

    def get_assistant_messages(self, annotations: entities.AnnotationCollection):
        """
        Get all the annotations in the item for the assistant messages
        """
        # clearing the assistant prompts from previous annotations that might not belong
        self.assistant_prompts = dict()
        for annotation in annotations:
            prompt_id = annotation.metadata.get('system', dict()).get('promptId', None)
            if annotation.type == 'ref_image':
                prompt = Prompt(key=prompt_id)
                prompt.add_element(value=annotation.coordinates.get('ref'), mimetype=PromptType.IMAGE)
                self.assistant_prompts[annotation.id] = prompt
            elif annotation.type == 'text':
                prompt = Prompt(key=prompt_id)
                prompt.add_element(value=annotation.coordinates, mimetype=PromptType.TEXT)
                self.assistant_prompts[annotation.id] = prompt

    def get_assistant_prompts(self, model_name):
        """
        Get assistant prompts
        :return:
        """
        if self._item is None:
            logger.warning('Item is not loaded, skipping annotations context')
            return
        filters = entities.Filters(resource=entities.FiltersResource.ANNOTATION)
        filters.add(field='metadata.user.model.name', values=model_name)
        annotations = self._item.annotations.list(filters=filters)
        self.get_assistant_messages(annotations=annotations)

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
                prompts_json["prompts"][prompt_key].append({'metadata'})

        return prompts_json

    def add_prompt(self, prompt: Prompt, update_item=True):
        """
            add a prompt to the prompt item
            prompt: a dictionary. keys are prompt message id, values are prompt messages
            responses: a list of annotations representing responses to the prompt
        """
        self.prompts.append(prompt)
        if update_item is True:
            if self._item is not None:
                self._item._Item__update_item_binary(_json=self.to_json())
            else:
                logger.warning('Item is not loaded, skipping upload')

    def messages(self, model_name=None):
        """
        return a list of messages in the prompt item
        messages are returned following the openai SDK format
        """
        if model_name is not None:
            self.get_assistant_prompts(model_name=model_name)
        else:
            logger.warning('Model name is not provided, skipping assistant prompts')

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

        for ann_id, prompt in self.assistant_prompts.items():
            if prompt.key not in all_prompts_messages:
                logger.warning(f'Prompt key {prompt.key} is not found in the user prompts, skipping Assistant prompt')
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
        return res

    def add_responses(self, annotation: entities.BaseAnnotationDefinition, model: entities.Model):
        """
        Add an annotation to the prompt item
        :param annotation: Annotation object
        :param model: Model object
        """
        if self._item is None:
            raise ValueError('Item is not loaded, cannot add annotation')
        annotation_collection = entities.AnnotationCollection()
        annotation_collection.add(annotation_definition=annotation,
                                  prompt_id=self.prompts[-1].key,
                                  model_info={
                                      'name': model.name,
                                      'model_id': model.id,
                                      'confidence': 1.0
                                  })
        annotations = self._item.annotations.upload(annotations=annotation_collection)
        self.get_assistant_messages(annotations=annotations)
