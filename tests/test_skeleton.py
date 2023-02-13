
from pysaleryd.skeleton import main

__author__ = "Björn Dalfors"
__copyright__ = "Björn Dalfors"
__license__ = "MIT"


def test_main(capsys):
    """CLI Tests"""
    # capsys is a pytest fixture that allows asserts against stdout/stderr
    # https://docs.pytest.org/en/stable/capture.html
    main(["--host", "192.168.1.151", "--port", "3001", "--listen", "-t", "3"])
    captured = capsys.readouterr()
    assert not captured.err

    main(["--host", "192.168.1.151", "--port", "3001", "--send", "--key", "MF", "--data", "0"])
    captured = capsys.readouterr()
    assert not captured.err
