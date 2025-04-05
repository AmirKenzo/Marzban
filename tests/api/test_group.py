import random
from fastapi import status
from tests.api import client
from tests.api.test_admin import test_admin_login


group_names = ["testgroup", "testgroup2", "testgroup3"]


def test_group_create():
    """Test that the group create route is accessible."""

    access_token = test_admin_login()
    inbounds = client.get(
        url="/api/inbounds",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert inbounds.status_code == status.HTTP_200_OK
    for group_name in group_names:
        random_inbound = random.sample(
            inbounds.json(),
            k=min(3, len(inbounds.json())),
        )
        response = client.post(
            url="/api/group",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"name": group_name, "inbound_tags": random_inbound},
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["name"] == group_name
        assert response.json()["inbound_tags"] == random_inbound


def test_group_get():
    """Test that the group get route is accessible."""
    access_token = test_admin_login()
    response = client.get(
        url="/api/groups",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["total"] == len(group_names)


def test_group_update():
    """Test that the group update route is accessible."""
    access_token = test_admin_login()
    response = client.put(
        url="/api/group/1",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"name": "testgroup4", "is_disabled": True},
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["name"] == "testgroup4"
    assert response.json()["is_disabled"] is True


def test_group_delete():
    """Test that the group delete route is accessible."""
    access_token = test_admin_login()
    response = client.delete(
        url="/api/group/1",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_group_get_by_id():
    """Test that the group get by id route is accessible."""
    access_token = test_admin_login()
    response = client.get(
        url="/api/group/2",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["name"] == "testgroup2"
