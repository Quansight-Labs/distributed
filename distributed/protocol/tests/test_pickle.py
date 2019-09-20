from functools import partial
import gc
from operator import add
import weakref

import pytest

from distributed.protocol.pickle import dumps, loads
from distributed.utils_test import captured_logger


def test_pickle_data():
    data = [1, b"123", "123", [123], {}, set()]
    for d in data:
        assert loads(dumps(d)) == d


def test_pickle_numpy():
    np = pytest.importorskip("numpy")
    x = np.ones(5)
    assert (loads(dumps(x)) == x).all()

    x = np.ones(5000)
    assert (loads(dumps(x)) == x).all()


def test_pickle_functions():
    def make_closure():
        value = 1

        def f(x):  # closure
            return x + value

        return f

    def funcs():
        yield make_closure()
        yield (lambda x: x + 1)
        yield partial(add, 1)

    for func in funcs():
        wr = weakref.ref(func)
        func2 = loads(dumps(func))
        wr2 = weakref.ref(func2)
        assert func2(1) == func(1)
        del func, func2
        gc.collect()
        assert wr() is None
        assert wr2() is None


def test_pickle_deserialize_unsubscriptable():
    # Regression test for https://github.com/dask/distributed/issues/2971
    with captured_logger("distributed.protocol.pickle") as logger:
        try:
            loads(123)  # Raises deserialization error
        except TypeError:
            pass
    out = logger.getvalue()
    assert "a bytes-like object is required" in out
