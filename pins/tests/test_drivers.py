import fsspec
import pytest
import pandas as pd

from pathlib import Path

from pins.tests.helpers import rm_env

from pins.meta import MetaRaw
from pins.config import PINS_ENV_INSECURE_READ
from pins.drivers import load_data, save_data, default_title
from pins.errors import PinsInsecureReadError


@pytest.fixture
def some_joblib(tmp_dir2):
    import joblib

    p_obj = tmp_dir2 / "some.joblib"
    joblib.dump({"a": 1}, p_obj)

    return p_obj


# default title ---------------------------------------------------------------


class ExC:
    class D:
        pass


@pytest.mark.parametrize(
    "obj, dst_title",
    [
        (pd.DataFrame({"x": [1, 2]}), "somename: a pinned 2 x 1 DataFrame"),
        (pd.DataFrame({"x": [1], "y": [2]}), "somename: a pinned 1 x 2 DataFrame"),
        (ExC(), "somename: a pinned ExC object"),
        (ExC().D(), "somename: a pinned ExC.D object"),
        ([1, 2, 3], "somename: a pinned list object"),
    ],
)
def test_default_title(obj, dst_title):
    res = default_title(obj, "somename")
    assert res == dst_title


@pytest.mark.parametrize(
    "type_",
    [
        "csv",
        "feather",
        "parquet",
    ],
)
def test_driver_roundtrip(tmp_dir2, type_):
    # TODO: I think this test highlights the challenge of getting the flow
    # between metadata, drivers, and the metafactory right.
    # There is the name of the data (relative to the pin directory), and the full
    # name of data in its temporary directory.
    import pandas as pd

    df = pd.DataFrame({"x": [1, 2, 3]})

    fname = "some_df"
    full_file = f"{fname}.{type_}"

    p_obj = tmp_dir2 / fname
    res_fname = save_data(df, p_obj, type_)

    assert Path(res_fname).name == full_file

    meta = MetaRaw(full_file, type_, "my_pin")
    obj = load_data(meta, fsspec.filesystem("file"), tmp_dir2)

    assert df.equals(obj)


@pytest.mark.skip("TODO: complete once driver story is fleshed out")
def test_driver_roundtrip_joblib(tmp_dir2):
    pass


def test_driver_pickle_read_fail_explicit(some_joblib):
    meta = MetaRaw(some_joblib.name, "joblib", "my_pin")
    with pytest.raises(PinsInsecureReadError):
        load_data(
            meta, fsspec.filesystem("file"), some_joblib.parent, allow_pickle_read=False
        )


def test_driver_pickle_read_fail_default(some_joblib):
    meta = MetaRaw(some_joblib.name, "joblib", "my_pin")
    with rm_env(PINS_ENV_INSECURE_READ), pytest.raises(PinsInsecureReadError):
        load_data(
            meta, fsspec.filesystem("file"), some_joblib.parent, allow_pickle_read=False
        )


def test_driver_apply_suffix_false(tmp_dir2):
    import pandas as pd

    df = pd.DataFrame({"x": [1, 2, 3]})

    fname = "some_df"
    type_ = "csv"

    p_obj = tmp_dir2 / fname
    res_fname = save_data(df, p_obj, type_, apply_suffix=False)

    assert Path(res_fname).name == "some_df"
