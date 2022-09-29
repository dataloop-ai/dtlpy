import behave
from time import sleep


@behave.then(u'I try to reset statistics with stop_if_running "{flag_status}"')
def step_impl(context, flag_status):
    if flag_status == "True":
        context.pipeline.reset(stop_if_running=True)
        sleep(2)
        # Checking that all statistics got rest
        for i in range(3):
            if context.pipeline.stats().node_averages[i].averages.avg_execution_per_day != 0:
                assert False
            if context.pipeline.stats().node_averages[i].averages.avg_time_per_execution != 0:
                assert False

        if context.pipeline.stats().pipeline_averages.avg_execution_per_day != 0:
            assert False
        if context.pipeline.stats().pipeline_averages.avg_time_per_execution != 0:
            assert False
        assert True
    else:
        try:
            context.pipeline.reset(stop_if_running=False)
            assert False
        except Exception as e:
            assert "Pipeline with installed status couldn't be updated" in e.args[1]
            assert True
