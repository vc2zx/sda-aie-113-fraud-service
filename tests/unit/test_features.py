from math import log1p

import pytest


@pytest.mark.unit
def test_feature_extraction(sample_txn):
    features = sample_txn.to_features()

    assert features["amount_log"] == pytest.approx(log1p(250.0))
    assert features["channel"] == "ecom"
    assert features["mcc"] == "ELECTRONICS"
    assert features["hour_of_day"] == 3
    assert features["is_night"] == 1


@pytest.mark.unit
def test_merchant_category_normalisation(sample_txn):
    from dataclasses import replace

    txn = replace(sample_txn, merchant_category=" home goods ")

    assert txn.to_features()["mcc"] == "HOME_GOODS"
