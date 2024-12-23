import asyncio
from contextlib import contextmanager


@contextmanager
def task_manager(*args, cancel_on_exit=False, **kwargs):
    """Context manager for tasks

    :param cancel_on_exit: cancel tasks on exit context, defaults to False
    :type cancel_on_exit: bool, optional
    :yield: the task list
    :rtype: TaskList
    """
    task_list = TaskList(*args, **kwargs)
    try:
        yield task_list
    finally:
        if cancel_on_exit:
            task_list.cancel()


class TaskList:
    """Helper class to keep references and work with Tasks"""

    def __init__(self):
        self.tasks: list[asyncio.Task] = []

    def append(self, *tasks: asyncio.Task, remove_when_done=True):
        """Add reference to tasks

        :param tasks: tasks to add
        :type tasks: `~asyncio.Task`
        :param remove_when_done: remove reference when task completes, defaults to True
        :type remove_when_done: bool, optional
        """
        for task in tasks:
            if remove_when_done:
                task.add_done_callback(self.remove)
                self.tasks.append(task)

    def remove(self, *tasks: asyncio.Task):
        """Remove references to tasks
        :param tasks: tasks to remove
        :type tasks: asyncio.Task
        """
        for task in tasks:
            try:
                self.tasks.remove(task)
            except ValueError:
                pass

    async def wait(self, *args, **kwargs):
        """Wait for tasks. Wrapper around :func:`~asyncio.wait`"""
        try:
            return await asyncio.wait(self.tasks, *args, **kwargs)
        except ValueError:
            pass

    def cancel(self):
        """Cancel all tasks"""
        for task in self.tasks:
            task.cancel()
