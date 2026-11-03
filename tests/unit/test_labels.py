import unicodedata

import pytest

from chemiproof.data import labels
from chemiproof.errors import ChemiProofError, StatusCode


@pytest.mark.parametrize(("raw", "frac"), [("10：1", 10 / 11), ("1：10", 1 / 11), ("8：3", 8 / 11)])
def test_ratio_is_olive_parts_over_eleven(raw, frac):
    a, b, y = labels.parse_ratio_dir(raw)
    assert a + b == 11 and y == pytest.approx(frac)


def test_label_range_matches_published_9_09_to_90_91_percent():
    ys = [labels.parse_ratio_dir(f"{a}：{11 - a}")[2] for a in range(1, 11)]
    assert round(min(ys) * 100, 2) == 9.09 and round(max(ys) * 100, 2) == 90.91


@pytest.mark.parametrize("raw", ["5：5", "0：11", "11：0", "a：b", "10:1:1", "", "12：-1"])
def test_bad_ratios_rejected(raw):
    with pytest.raises(ChemiProofError) as e:
        labels.parse_ratio_dir(raw)
    assert e.value.code is StatusCode.UNVERIFIED_LABEL


@pytest.mark.parametrize("form", ["NFC", "NFD"])
def test_group_names_accept_either_unicode_form(form):
    name = unicodedata.normalize(form, "欧丽薇兰特级初榨混家香味花生油")
    assert labels.parse_group_dir(name) == ("olivera", "peanut")


def test_all_known_groups_and_rounds():
    assert labels.parse_group_dir("鲁花特级初榨混晟麦核桃油") == ("luhua", "walnut")
    assert labels.parse_group_dir("伯爵特级初榨混西王玉米胚芽油") == ("earl_grey", "corn")
    assert labels.parse_group_dir("鲁花特级初榨混家乡味花生油") == ("luhua", "peanut")
    assert [labels.parse_round_dir(r) for r in ("第一轮", "第二轮", "第三轮")] == [1, 2, 3]


@pytest.mark.parametrize("name", ["某某牌特级初榨混金龙鱼菜籽油", "鲁花特级初榨混未知油", "x"])
def test_unknown_group_is_unverified_not_guessed(name):
    with pytest.raises(ChemiProofError) as e:
        labels.parse_group_dir(name)
    assert e.value.code is StatusCode.UNVERIFIED_LABEL
