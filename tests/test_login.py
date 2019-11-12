import dtlpy as dl
import sys


if __name__ == "__main__":
    args = sys.argv
    username = args[1]
    password = args[2]
    client_id = args[3]
    client_secret = args[4]

    dl.setenv('dev')
    dl.login_secret(
        email=username,
        password=password,
        client_id=client_id,
        client_secret=client_secret
    )

    if dl.token_expired():
        sys.exit(1)
    else:
        sys.exit(0)
