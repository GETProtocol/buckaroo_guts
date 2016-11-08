from huey.contrib.djhuey import task
import logging


logger = logging.getLogger("huey")


@task()
def buckaroo_api_call(*args, **kwargs):
    logger.info('Huey Buckaroo API call')
    print("Woohoo! Buckaroo HUEY call **********")
