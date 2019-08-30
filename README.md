Threaded Batching
=================

When training a neural network, sometimes constructing the batch may take longer than the actual forward & backward propogation steps.
On a lot of modern machines, there's a potential to speed up training (and evaluation) by constructing the batch in a separate thread.

Tensorflow has the `DataSet` class to do this, but I wanted to write a framework-agnostic class.

# How to use this

You subclass `ThreadedBatcher` and define the three abstract methods from the base class:
* `_get_next_batch_params` should do very little work. e.g. it should return the indices of the rows to use.
  Only one thread will call this at any time.
* `_get_batch_from_params` will take the output of `_get_next_batch_params` and return a "batch".
  Many threads may call this at one. All the heavy lifting should go in here.
* `_reset_batch_params` should reset any internal state so that subsequent calls to `_get_next_batch_params` start returning the next epoch.

