from taskiq import TaskiqScheduler
from taskiq.schedule_sources import LabelScheduleSource
from taskiq_redis import RedisAsyncResultBackend, RedisStreamBroker

from kworkflow.main.config import config

result_backend = RedisAsyncResultBackend(
    redis_url=config.redis.connection_url,
    result_ex_time=3600,
)
broker = RedisStreamBroker(
    url=config.redis.connection_url,
).with_result_backend(result_backend)

scheduler = TaskiqScheduler(broker, sources=[LabelScheduleSource(broker)])
