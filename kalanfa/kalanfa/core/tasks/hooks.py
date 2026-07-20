from abc import abstractmethod

from kalanfa.plugins.hooks import define_hook
from kalanfa.plugins.hooks import KalanfaHook


@define_hook
class JobHook(KalanfaHook):
    @abstractmethod
    def schedule(self, job, orm_job):
        pass

    @abstractmethod
    def update(self, job, orm_job, state=None, **kwargs):
        pass

    @abstractmethod
    def clear(self, job, orm_job):
        pass
