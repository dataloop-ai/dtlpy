import json
import logging
import traceback
from . import PipelineBuilder


class PipelineRunner:
    def __init__(self, platform_interface, reporter):
        self.logger = logging.getLogger('dataloop.pipeline_runner')
        # login with input token
        self.platform_interface = platform_interface
        self.pipeline_builder = PipelineBuilder()
        self.reporter = reporter

    def from_dictionary(self, pipeline_dict):
        self.pipeline_builder.from_dict(pipeline_dict=pipeline_dict)

    def from_file(self, filename):
        self.pipeline_builder.from_file(filename=filename)

    def from_pipeline_id(self, pipeline_id):
        pipeline = self.platform_interface.pipelines.get(
            pipeline_id=pipeline_id)
        if pipeline is None:
            self.logger.exception(
                'Pipe length is more than 1. pipe_id: %s' % pipeline_id)
            assert False
        pipeline_str = pipeline.arch
        pipeline_dict = json.loads(pipeline_str)
        self.pipeline_builder.from_dict(pipeline_dict)

    def run(self, context):
        """
        Run a pipeline
        :param context:
        :param stages_to_run:
        :param stages_not_to_run:
        :return:
        """
        # sanity check - input arguments
        try:
            missing = False
            for in_param in self.pipeline_builder.inputs:
                if in_param not in context:
                    missing = True
                    self.logger.exception(
                        'Missing input parameter for pipe: %s' % in_param)
            if missing:
                raise ValueError(
                    'Input parameters missing. See above for information')

            all_stages = list()
            for stage in self.pipeline_builder.stages:
                all_stages.append(stage.type)

            ##################
            # Run all stages #
            ##################

            self.reporter.send_progress(
                {'status': 'in-progress',
                 'message': 'Initiating'})

            for i_stage, stage in enumerate(self.pipeline_builder.stages):
                ##################
                # load all steps #
                ##################
                try:
                    for step in stage.steps:
                        if step.type == 'custom':
                            # load class dynamically
                            step.load()
                except FileNotFoundError as err:
                    err_msg = '%s\n%s' % (traceback.format_exc(),
                                          'Custom file wasn\'t found. It needs to be is a different stage from the Unpack step')
                    self.logger.exception(err_msg)
                    raise FileNotFoundError(err_msg)

                # if stage is multiple - load all generator
                g_list = list()
                g_list_n_items = list()
                if stage.type.lower() == 'multiple':
                    ##############
                    # Generators #
                    ##############
                    for generator in stage.generators:
                        # take generator that was saved to context by previous stages
                        gen = context[generator['name']]
                        # count items in generator
                        n_batches = gen.items_count
                        # append to generators list
                        g_list.append(iter(gen))
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
                        n_batch_in_gen = 1
                        for i_generator, g in enumerate(g_list):
                            items_batch = next(g)
                            # put generators' outputs in kwargs dictionary
                            context[stage.generators[i_generator]['outputs'][0]['name']] = items_batch
                            # get total number of batches in generator
                            n_batch_in_gen = g_list_n_items[i_generator]

                        #################
                        # Run all steps #
                        #################
                        for i_step, step in enumerate(stage.steps):
                            msg = 'stage: {i_stage}/{n_stage} '.format(i_stage=i_stage + 1,
                                                                       n_stage=self.pipeline_builder.n_stages) + \
                                  'batch: {i_batch_in_gen}/{n_batch_in_gen} '.format(i_batch_in_gen=i_batch_in_gen + 1,
                                                                                     n_batch_in_gen=n_batch_in_gen) + \
                                  'step: {i_step}/{n_steps} '.format(i_step=i_step + 1,
                                                                     n_steps=len(stage.steps)) + \
                                  'name: {}'.format(step.name)
                            total_progress = (i_stage / self.pipeline_builder.n_stages) + \
                                             (i_batch_in_gen / n_batch_in_gen / self.pipeline_builder.n_stages) + \
                                             (i_step / len(stage.steps) / n_batch_in_gen / self.pipeline_builder.n_stages)

                            self.reporter.send_progress({'percent_complete': int(100 * total_progress),
                                                         'message': 'running ' + msg})
                            self.logger.info(msg)

                            # for debug
                            # self.logger.debug(context)
                            ################
                            # execute step #
                            ################
                            context = step.execute(context)
                            # Done step!

                            # check if stop pipe initiated
                            if 'stop_pipe' in context and context['stop_pipe']:
                                self.reporter.send_progress({'status': 'canceled'})
                                self.logger.info('Pipe stopped. stop_pipe initiated.')
                                return
                        i_batch_in_gen += 1
                        if stage.type.lower() != 'multiple':
                            ########################################
                            # if single step break from while loop #
                            ########################################
                            break

                except StopIteration:
                    pass
                finally:
                    for g in g_list:
                        del g
        except Exception as err:
            self.logger.exception(traceback.format_exc())
            self.logger.exception(err)
            self.reporter.send_progress({'status': 'failed',
                                         'error': '%s' % traceback.format_exc()})
            raise
        self.reporter.send_progress({'status': 'success',
                                     'percent_complete': 100})
        # return all arguments
        return context
