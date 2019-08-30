Threaded Batching
=================

When training a neural network, sometimes constructing the batch may take longer than the actual forward & backward propogation steps.
On a lot of modern machines, there's a potential to speed up training (and evaluation) by constructing the batch in a separate thread.

Tensorflow has the `DataSet` class to do this, but I wanted to write a framework-agnostic class.
