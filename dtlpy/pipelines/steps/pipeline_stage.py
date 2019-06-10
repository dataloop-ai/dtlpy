from ..steps import *

mapping = {
    # annotations
    'AnnotationsGet': AnnotationsGetStep,
    'AnnotationsGetBatch': AnnotationsGetBatchStep,
    'AnnotationsUpload': AnnotationsUploadStep,
    'AnnotationsUploadBatch': AnnotationsUploadBatchStep,
    'AnnotationsUpdate': AnnotationsUpdateStep,
    'AnnotationsEdit': AnnotationsUpdateStep,
    # artifacts
    'ArtifactsDownload': ArtifactsDownloadStep,
    'ArtifactsUpload': ArtifactsUploadStep,
    # keras callbacks
    'CallbacksGet': CallbacksGetStep,
    # datasets
    'DatasetsGet': DatasetsGetStep,
    'DatasetsDownload': DatasetsDownloadStep,
    # items
    'ItemsGet': ItemsGetStep,
    'ItemsDownload': ItemsDownloadStep,
    'ItemsDownloadBatch': ItemsDownloadBatchStep,
    'ItemsUpdate': ItemsUpdateStep,
    'ItemsEdit': ItemsUpdateStep,
    'ItemsList': ItemsListStep,
    'ItemsUpload': ItemsUploadStep,
    'ItemsUploadBatch': ItemsUploadBatchStep,
    # packages
    'PackagesProjectsUnpack': PackagesProjectsUnpackStep,
    # sessions
    'SessionsGet': SessionsGetStep,
    # python builtins
    'BuiltinFunc': BuiltinFuncStep}


class PipelineStage(object):
    """
    Stage creator
    """

    def __init__(self, stage_dict=None):
        self.steps = list()
        # define stage type
        self.type = 'single'
        self.generators = list()

        if stage_dict is not None:
            self.from_dict(stage_dict)
            # self.type = 'multiple'
            # self.generators = [{'name': '',  # from all_kwargs
            #                     'outputs': [{'name': '', 'type': ''},  # where to save outputs
            #                                 {'name': '', 'type': ''},
            #                                 {'name': '', 'type': ''}]},
            #                    {'name': '',
            #                     'outputs': [{'name': '', 'type': ''},
            #                                 {'name': '', 'type': ''},
            #                                 {'name': '', 'type': ''}]}
            #                    ]

    @property
    def n_steps(self):
        return len(self.steps)

    def add_step(self, step):
        self.steps.append(step)

    def from_dict(self, stage_dict):
        if 'generators' in stage_dict:
            self.generators = stage_dict['generators']
        if 'type' in stage_dict:
            self.type = stage_dict['type']

        for step_dict in stage_dict['steps']:
            if step_dict['type'].lower() == 'custom':
                self.steps.append(CustomPipelineStep(step_dict))
            else:
                # load platform step
                self.steps.append(mapping[step_dict['name']](step_dict))

    def to_dict(self):
        stage = {'steps': self.steps,
                 'type': self.type,
                 'generators': self.generators}
        return stage
