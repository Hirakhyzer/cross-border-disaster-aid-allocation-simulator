from aidalloc.synthetic import AID_TYPES, SyntheticAidConfig, generate_synthetic_aid_data


def test_synthetic_shapes_and_keys():
    data = generate_synthetic_aid_data(SyntheticAidConfig(regions=12, warehouses=3, seed=3))
    assert set(data) == {"regions", "warehouses", "inventory", "needs", "routes", "actors"}
    assert len(data["regions"]) == 12
    assert len(data["warehouses"]) == 3
    assert data["needs"]["aid_type"].nunique() == len(AID_TYPES)
    assert data["routes"].shape[0] == 12 * 3


def test_invalid_config_rejected():
    try:
        SyntheticAidConfig(regions=4, warehouses=1)
    except ValueError:
        assert True
    else:
        raise AssertionError("invalid config should fail")
