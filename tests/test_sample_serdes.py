import numpy as np
from pyq_engine import utils


def test_sample_serializer():
    samples = np.random.rand(10).view(dtype=np.complex128)
    store = utils.serialize_samples(samples)
    assert 'dtype' in store.keys()
    assert 'buffer' in store.keys()

    out = utils.deserialize_samples(store)

    assert samples.shape == out.shape
    assert np.array_equal(samples, out)
