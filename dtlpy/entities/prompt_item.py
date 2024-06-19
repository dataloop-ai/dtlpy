import logging
import io
import enum
import json

logger = logging.getLogger(name='dtlpy')


class PromptType(str, enum.Enum):
    TEXT = 'application/text'
    IMAGE = 'image/*'
    AUDIO = 'audio/*'
    VIDEO = 'video/*'


class Prompt:
    def __init__(self, key):
        """
        Create a single Prompt. Prompt can contain multiple mimetype elements, e.g. text sentence and an image.

        :param key: unique identifier of the prompt in the item
        """
        self.key = key
        self.elements = list()

    def add(self, value, mimetype='text'):
        """

        :param value: url or string of the input
        :param mimetype: mimetype of the input. options: `text`, `image/*`, `video/*`, `audio/*`
        :return:
        """
        self.elements.append({'mimetype': mimetype,
                              'value': value})

    def to_json(self):
        """
        Convert Prompt entity to the item json

        :return:
        """
        return {
            self.key: [
                {
                    "mimetype": e['mimetype'],
                    "value": e['value']
                } for e in self.elements
            ]
        }


class PromptItem:
    def __init__(self, name):
        """
        Create a new Prompt Item. Single item can have multiple prompt, e.g. a conversation.

        :param name: name of the item (filename)
        """
        self.name = name
        self.type = "prompt"
        self.prompts = list()

    def to_json(self):
        """
        Convert the entity to a platform item.

        :return:
        """
        prompts_json = {
            "shebang": "dataloop",
            "metadata": {
                "dltype": self.type
            },
            "prompts": {}
        }
        for prompt in self.prompts:
            for prompt_key, prompt_values in prompt.to_json().items():
                prompts_json["prompts"][prompt_key] = prompt_values
        return prompts_json

    @classmethod
    def from_json(cls, _json):
        inst = cls(name='dummy')
        for prompt_key, prompt_values in _json["prompts"].items():
            prompt = Prompt(key=prompt_key)
            for val in prompt_values:
                prompt.add(mimetype=val['mimetype'], value=val['value'])
            inst.prompts.append(prompt)
        return inst

    def to_bytes_io(self):
        byte_io = io.BytesIO()
        byte_io.name = self.name
        byte_io.write(json.dumps(self.to_json()).encode())
        byte_io.seek(0)
        return byte_io

    def add(self, prompt):
        """
            add a prompt to the prompt item
            prompt: a dictionary. keys are prompt message id, values are prompt messages
            responses: a list of annotations representing responses to the prompt
        """
        self.prompts.append(prompt)
