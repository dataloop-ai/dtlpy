class PipelineProgress(object):
    def __init__(self):
        self.message = ''
        self.status = ''
        self.stage_status = list()
        self.stage_n_steps = list()
        self.stage_i_step = list()
        self.i_stage = None
        self.n_stages = None
