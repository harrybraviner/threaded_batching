from queue import Queue, Empty
from threading import Lock, Thread
from abc import ABC, abstractmethod
from typing import Callable, Iterable

class ThreadedSource:

    def __init__(self,
                 get_params_iterator: Callable[[], Iterable],
                 get_item_from_params: Callable,
                 num_enqueueing_threads=2, max_queue_size=10):
        self._num_enqueueing_threads = num_enqueueing_threads
        self._get_params_iterator = get_params_iterator
        self._get_item_from_params = get_item_from_params
    
        self._batch_queue = Queue(maxsize=max_queue_size)

        # This lock is used to ensure that only one consumer is dequeue-ing at any one time.
        self._iteration_lock = Lock()

        # This lock is used to ensure that only one thread is being assigned it batch params at any one time.
        self._batch_params_lock = Lock()

    def _reset_iteration(self):
        """
        Reset the iteration of batching parameters, and restart threads.
        """
        # Have we run out of data to enqueue?
        # If this variable is True, AND the Queue is empty, then we're done.
        self._iterator_exhausted = False

        # Need to reset this so that fresh params are delivered.
        self._iterator = iter(self._get_params_iterator())

        self._queueing_threads = [Thread(target=self._enqueue, args=(), daemon=True)
                                  for _ in range(self._num_enqueueing_threads)]
        for thread in self._queueing_threads:
            thread.start()

    def __iter__(self):
        self._reset_iteration()
        while True:
            try:
                yield self._next()
            except StopIteration:
                break

    # Don't need __next__, since the __iter__ generator supplies that.
    def _next(self):
        with self._iteration_lock: # Ensure that we are the only thread running this function
            if self._iterator_exhausted is False:
                # If we get here, there is still data to enqueue.
                # We can safely wait for the queue to be ready, since we are the only thing dequeueing.
                return self._batch_queue.get(block=True, timeout=None)
            else:
                # There is no data left to enqueue.
                try:
                    # Short pause to ensure that final batch has actually been enqueued.
                    return self._batch_queue.get(block=True, timeout=0.5)
                except Empty:
                    # Finished the iterator
                    raise StopIteration

    def _enqueue(self):
        """
        Function that gets run its own thread.
        Continues running until we run out of batches.
        """
        while self._iterator_exhausted is False:
            try:
                with self._batch_params_lock:
                    params = next(self._iterator)
                x = self._get_item_from_params(params)
                self._batch_queue.put(x, block=True, timeout=None)
            except StopIteration:
                self._iterator_exhausted = True

