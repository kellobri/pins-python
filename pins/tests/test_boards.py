import pytest
import pandas as pd

from pins.tests.helpers import DEFAULT_CREATION_DATE

# using pytest cases, so that we can pass in fixtures as parameters
from pytest_cases import fixture, parametrize


@fixture
def board(backend):
    yield backend.create_tmp_board()
    backend.teardown()


@fixture
def df():
    return pd.DataFrame({"x": [1, 2, 3], "y": ["a", "b", "c"]})


# High level pins functionality -----------------------------------------------


def test_board_pin_write_default_title(board):

    df = pd.DataFrame({"x": [1, 2, 3], "y": [4, 5, 6]})
    meta = board.pin_write(df, "df_csv", title=None, type="csv")
    assert meta.title == "A pinned 3 x 2 CSV"


def test_board_pin_write_prepare_pin(board, tmp_dir2):

    df = pd.DataFrame({"x": [1, 2, 3], "y": [4, 5, 6]})

    meta = board.prepare_pin_version(
        str(tmp_dir2), df, "df_csv", title=None, type="csv"
    )
    assert meta.file == "df_csv"
    assert (tmp_dir2 / "data.txt").exists()
    assert (tmp_dir2 / "df_csv").exists()
    assert not (tmp_dir2 / "df_csv").is_dir()


def test_board_pin_write_roundtrip(board):

    df = pd.DataFrame({"x": [1, 2, 3], "y": [4, 5, 6]})

    assert not board.pin_exists("df_csv")

    board.pin_write(df, "df_csv", type="csv")

    assert board.pin_exists("df_csv")

    loaded_df = board.pin_read("df_csv")
    assert loaded_df.equals(df)


def test_board_pin_write_type_not_specified_error(board):
    class C:
        pass

    with pytest.raises(NotImplementedError):
        board.pin_write(C(), "cool_pin")


def test_board_pin_write_type_error(board):
    class C:
        pass

    with pytest.raises(NotImplementedError) as exc_info:
        board.pin_write(C(), "cool_pin", type="MY_TYPE")

    assert "MY_TYPE" in exc_info.value.args[0]


def test_board_pin_write_rsc_index_html(board, tmp_dir2, snapshot):
    if board.fs.protocol != "rsc":
        pytest.skip()

    df = pd.DataFrame({"x": [1, 2, 3], "y": ["a", "b", "c"]})

    pin_name = "test_rsc_pin"

    board.prepare_pin_version(
        str(tmp_dir2),
        df,
        pin_name,
        type="csv",
        title="some pin",
        description="some description",
        created=DEFAULT_CREATION_DATE,
    )

    snapshot.assert_equal_dir(tmp_dir2)


# pin_write against different types -------------------------------------------


@parametrize(
    "obj, type_", [(df, "csv"), (df, "joblib"), ({"a": 1, "b": [2, 3]}, "joblib")]
)
def test_board_pin_write_type(board, obj, type_, request):
    meta = board.pin_write(obj, "test_pin", type=type_, title="some title")
    dst_obj = board.pin_read("test_pin")

    assert meta.type == type_

    if isinstance(obj, pd.DataFrame):
        assert obj.equals(dst_obj)

    obj == dst_obj
