from app.correction import dictionary_correct
from app.metrics import edit_distance, error_rate


def test_edit_distance():
    assert edit_distance(["a", "b"], ["a", "c"]) == 1


def test_fixed_wer_and_cer():
    assert error_rate("i ni ce", "i ni") == 1 / 3
    assert error_rate("abc", "adc", characters=True) == 1 / 3


def test_empty_reference_is_defined():
    assert error_rate("", "word") == 1.0


def test_bambara_dictionary_normalization():
    assert dictionary_correct("Ani sogoma", "bam") == "ani sɔgɔma"
    assert dictionary_correct("Ani sogoma", "dyu") == "Ani sogoma"
