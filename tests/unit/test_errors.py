from chemiproof.errors import DESCRIPTIONS, ChemiProofError, StatusCode


def test_every_status_code_has_description():
    assert set(DESCRIPTIONS) == set(StatusCode)
    assert all(DESCRIPTIONS.values())


def test_error_carries_code_and_context():
    err = ChemiProofError(StatusCode.BAD_FILE_FORMAT, "oops", sample_id="s1")
    assert err.code is StatusCode.BAD_FILE_FORMAT and err.context == {"sample_id": "s1"}
    assert str(err) == "[BAD_FILE_FORMAT] oops"
