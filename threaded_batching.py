from queue import Queue, Empty
from threading import Lock, Thread
from abc import ABC, abstractmethod

class ThreadedBatcher(ABC):
    
    def __init__(self, num_enqueueing_threads=2):
        self._num_enqueueing_threads = num_enqueueing_threads
        
        self._batch_queue = Queue(maxsize=10) # FIXME - maxsize should be a param
        
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
        self._data_exhausted = False

        # Need to reset this so that fresh params are delivered.
        self._reset_batch_params()

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
        
    def _next(self):
        with self._iteration_lock: # Ensure that we are the only thread running this function
            if self._data_exhausted is False:
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

    @abstractmethod
    def _reset_batch_params(self):
        raise NotImplementedError

    @abstractmethod
    def _get_next_batch_params(self):
        raise NotImplementedError
    
    @abstractmethod
    def _get_batch_from_params(self, params):
        raise NotImplementedError        
            
    def _enqueue(self):
        """
        Function that gets run its own thread.
        Continues running until we run out of batches.
        """
        while self._data_exhausted is False:
            with self._batch_params_lock:
                batch_params = self._get_next_batch_params()
            if batch_params is None:
                self._data_exhausted = True
            else:
                this_batch = self._get_batch_from_params(batch_params)
                self._batch_queue.put(this_batch, block=True, timeout=None)
