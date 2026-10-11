

# --- a bad id in the query string is a 400, never a 500 ------------------------------------------

import pytest  # noqa: E402


@pytest.mark.parametrize("path", [
    "/api/v1/districts?regionId=abc",
    "/api/v1/districts?regionId=1'",
    "/api/v1/districts?regionId=1%20OR%201=1",
    "/api/v1/quarters?districtId=1;DROP%20TABLE%20x--",
])
def test_a_non_numeric_id_is_a_400_not_a_500(client, db, path):
    res = client.get(path)

    assert res.status_code == 400
