import json
from typing import List
import logging
import os

logger = logging.getLogger(name='dtlpy')


class Layer:
    def __init__(self, name, layer_type, url):
        self.name = name
        self.type = layer_type
        self.url = url


class ItemGis:
    def __init__(self,
                 name: str,
                 data: dict = None,
                 layer: Layer = None,
                 optional_layers: List[Layer] = None,
                 zoom: int = None,
                 min_zoom: int = None,
                 max_zoom: int = None,
                 epsg: str = None,
                 bounds: list = None,
                 aoi: list = None):
        self.name = name

        self.layer = layer or Layer(name=data.get('name', None), layer_type=data.get('type', None),
                                    url=data.get('url', None))
        if self.layer is None:
            raise ValueError('layer is required')
        elif self.layer is not None and isinstance(self.layer, dict):
            self.layer = Layer(name=self.layer.get('name', None), layer_type=self.layer.get('type', None), url=self.layer.get('url', None))


        self.optional_layers = optional_layers or [
            Layer(name=layer.get('name', None), layer_type=layer.get('type', None), url=layer.get('url', None)) for
            layer in data.get('optionalLayers', [])]

        if self.optional_layers is not None and isinstance(optional_layers, list):
            new_optional_layers = []
            for op_layer in self.optional_layers:
                if isinstance(op_layer, dict):
                    new_optional_layers.append(Layer(name=op_layer.get('name', None), layer_type=op_layer.get('type', None), url=op_layer.get('url', None)))
                else:
                    new_optional_layers.append(op_layer)
            self.optional_layers = new_optional_layers

        self.epsg = epsg or data.get('epsg', None)
        if self.epsg is None:
            raise ValueError('epsg is required')

        self.zoom = zoom or data.get('zoom', None)
        self.min_zoom = min_zoom or data.get('minZoom', None)
        self.max_zoom = max_zoom or data.get('maxZoom', None)
        self.bounds = bounds or data.get('bounds', None)
        self.aoi = aoi or data.get('aoi', None)

    def to_json(self):
        _json = {
            "type": "gis",
            "shebang": "dataloop",
            "metadata": {
                "dltype": "gis"
            },
            'layer': {
                'name': self.layer.name,
                'type': self.layer.type,
                'url': self.layer.url
            },
            "epsg": self.epsg
        }
        if self.optional_layers is not None:
            _json['optionalLayers'] = [
                {
                    'name': layer.name,
                    'type': layer.type,
                    'url': layer.url
                } for layer in self.optional_layers
            ]
        if self.zoom is not None:
            _json['zoom'] = self.zoom
        if self.min_zoom is not None:
            _json['minZoom'] = self.min_zoom
        if self.max_zoom is not None:
            _json['maxZoom'] = self.max_zoom
        if self.bounds is not None:
            _json['bounds'] = self.bounds
        if self.aoi is not None:
            _json['aoi'] = self.aoi
        return _json

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
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls(name=os.path.basename(filepath), data=data)