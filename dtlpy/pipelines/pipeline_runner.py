import yaml
import logging
import traceback
from . import PipelineProgress, PipelineBuilder


class PipelineRunner:
    def __init__(self, platform_interface):
        self.logger = logging.getLogger('dataloop.pipeline_runner')
        # login with input token
        self.platform_interface = platform_interface
        self.progress = PipelineProgress()
        self.pipeline_builder = PipelineBuilder()

    def from_file(self, filename):
        self.pipeline_builder.from_file(filename=filename)

    def from_pipeline_id(self, pipeline_id):
        pipeline = self.platform_interface.pipelines.get(pipeline_id=pipeline_id)
        if pipeline is None:
            self.logger.exception('Pipe length is more than 1. pipe_id: %s' % pipeline_id)
            assert False
        pipeline_str = pipeline.arch
        pipeline_dict = yaml.safe_load(pipeline_str)
        self.pipeline_builder.from_dict(pipeline_dict)

    def run(self, **kwargs):
        # all functions arguments
        pipeline_dict = dict()
        for k, v in kwargs.items():
            pipeline_dict[k] = v

        # sanity check - input arguments
        missing = False
        for in_param in self.pipeline_builder.inputs:
            if in_param not in pipeline_dict:
                missing = True
                self.logger.exception('Missing input parameter for pipe: %s' % in_param)
        if missing:
            raise ValueError('Input parameters missing. See above for information')

        ##################
        # Run all stages #
        ##################
        # set progress class
        self.progress.status = 'started'
        for i, stage in enumerate(self.pipeline_builder.stages):
            self.progress.stage_n_steps.append(stage.n_steps)
            self.progress.stage_i_step.append(0)
            self.progress.stage_status.append('pending')

        self.progress.status = 'running'
        for i_stage, stage in enumerate(self.pipeline_builder.stages):
            ##################
            # load all steps #
            ##################
            try:
                functions = list()
                for step in stage.steps:
                    if step.type == 'custom':
                        # load class dynamically
                        step.load()
            except FileNotFoundError:
                self.logger.exception(
                    'Custom file wasn\'t found. It needs to be is a different stage from the Unpack step')
                raise

            # if stage is multiple - load all generator
            g_list = list()
            g_list_n_items = list()
            if stage.type.lower() == 'multiple':
                ##############
                # Generators #
                ##############
                for generator in stage.generators:
                    # take generator that was saved to pipeline_dict by previous stages
                    gen = pipeline_dict[generator.name]
                    # count items in generator
                    g_temp = gen()
                    n_batches = 0
                    for _ in g_temp:
                        n_batches += 1
                    # append to generators list
                    g_list.append(gen())
                    g_list_n_items.append(n_batches)
            try:
                ###########################
                # Iterate over generators #
                ###########################
                # if single step the generator is empty and "while" will run only once
                i_batch_in_gen = 0
                while True:
                    #################################################
                    # Get input from generator to kwargs dictionary #
                    #################################################
                    n_batch_in_gen = 0
                    for i_generator, g in enumerate(g_list):
                        items_batch = next(g)
                        # put generators' outputs in kwargs dictionary
                        pipeline_dict[stage.generators[i_generator]['outputs'][0]['name']] = items_batch
                        # get total number of batches in generator
                        n_batch_in_gen = g_list_n_items[i_generator]

                    #################
                    # Run all steps #
                    #################
                    for i_step, step in enumerate(stage.steps):
                        self.progress.message = 'Progress: stage: %d/%d.\tbatch: %d/%d\tstep: %d/%d.\t name: %s' \
                                                % (i_stage, self.pipeline_builder.n_stages - 1,
                                                   i_batch_in_gen, n_batch_in_gen,
                                                   i_step, len(functions) - 1,
                                                   step.name)
                        self.logger.info(self.progress.message)

                        # for debug
                        # self.logger.debug(pipeline_dict)
                        ################
                        # execute step #
                        ################
                        pipeline_dict = step.execute(pipeline_dict)
                        self.progress.stage_i_step[-1] += 1
                        # check if stop pipe initiated
                        if 'stop_pipe' in pipeline_dict and pipeline_dict['stop_pipe']:
                            self.progress.status = 'stopped'
                            self.logger.info('Pipe stopped. stop_pipe initiated.')
                            return
                    i_batch_in_gen += 1
                    if stage.type == 'single':
                        ########################################
                        # if single step break from while loop #
                        ########################################
                        break

            except StopIteration:
                pass
            except Exception as err:
                self.logger.exception(traceback.format_exc())
                self.logger.exception(err)
                self.progress.status = 'error'
                self.progress.message = '%s' % traceback.format_exc()
                raise err
            finally:
                for g in g_list:
                    del g
        self.progress.status = 'done'
        # return all arguments
        return pipeline_dict
