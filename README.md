Threaded Batching
=================

When training a neural network, sometimes constructing the batch may take longer than the actual forward & backward propogation steps.
On a lot of modern machines, there's a potential to speed up training (and evaluation) by constructing the batch in a separate thread.

Tensorflow has the `DataSet` class to do this, but I wanted to write a framework-agnostic class.

# How to use this

You need to create a `ThreadedSource` by passing two methods:
* `get_params_iterator` should return an `Iterable` (or an `Iterator`). That `Iterator` should return the "param" of the objects to be sourced. Computing these params should be cheap. e.g. for batches of data, this would randomly draw the rows to be used.
* `get_item_from_params` should be a function that transforms params into the objects you want to return. These will be run asynchronously, so any heavy lifting should go in here.
