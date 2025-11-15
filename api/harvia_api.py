import requests



def get_api_configuration():
    response = requests.get("https://prod.api.harvia.io/endpoints")
    endpoints = response.json()["endpoints"]
    rest_api_base_url = endpoints["RestApi"]["generics"]["https"]
    print(rest_api_base_url)

    return {
        "rest_api_base_url": rest_api_base_url,
        "graphql": endpoints["GraphQL"],
    }


def sign_in_and_get_id_token(username: str, password: str) -> dict:
    config = get_api_configuration()
    response = requests.post(
        f"{config['rest_api_base_url']}/auth/token",
        headers={"Content-Type": "application/json"},
        json={"username": username, "password": password}
    )

    if not response.ok:
        error = response.json()
        raise Exception(error.get("message", f"Authentication failed: {response.status_code}"))

    tokens = response.json()
    return {
        "id_token": tokens["idToken"],
        "access_token": tokens["accessToken"],
        "refresh_token": tokens["refreshToken"],
        "expires_in": tokens["expiresIn"],
    }



if __name__ == "__main__":
    # Perform a GraphQL POST to a service endpoint
    config = get_api_configuration()
    tokens = sign_in_and_get_id_token("harviahackathon2025@gmail.com", "junction25!")
    print(f"ID Token: {tokens['id_token']}")
    base_url = config['rest_api_base_url']

    response = requests.get(
        base_url + "/devices",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {tokens['ac']}",
        },
    )
    print(response.json())
