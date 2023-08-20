from abc import ABC, abstractmethod
from typing import List


class RendererBase(ABC):
    render_queue: List = []

    @classmethod
    @abstractmethod
    def add_job(cls):
        pass

    @classmethod
    @abstractmethod
    def render_jobs(cls):
        # for job in self.render_queue:
        #     self.output_path = job.output_path
        #     self.add_render_pass(job.render_pass)
        #     self._render()
        pass
