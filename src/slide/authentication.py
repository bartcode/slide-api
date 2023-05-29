"""Methods that facilitate authentication for the Slide API."""
import hashlib
import os
import re
import time
from dataclasses import dataclass


@dataclass
class DigestAuthenticationHeader:
    """Fields from the Digest authentication header."""

    nonce: str
    realm: str
    qop: str
    nc: str  # pylint: disable=invalid-name
    cnonce_count: int
    algorithm: str = "MD5"


def parse_response_header(
    header_data: str, cnonce_count: int
) -> DigestAuthenticationHeader:
    """Parse response header into parameters used when calculating the digest."""
    nonce = re.findall(r'nonce="(.*?)"', header_data)[0]
    realm = re.findall(r'realm="(.*?)"', header_data)[0]
    qop = re.findall(r'qop="(.*?)"', header_data)[0]

    return DigestAuthenticationHeader(
        nonce=nonce,
        realm=realm,
        qop=qop,
        nc="00000001",
        cnonce_count=cnonce_count,
    )


def calculate_digest_key(
    username: str,
    password: str,
    uri: str,
    request_type: str,
    digest_info: DigestAuthenticationHeader,
) -> str:
    """Calculate digest key."""
    # Create a hash object based on the specified algorithm
    if not hasattr(hashlib, digest_info.algorithm.lower()):
        raise ValueError(f"Unsupported algorithm: {digest_info.algorithm}")

    if digest_info.qop == "auth" or "auth" in digest_info.qop.split(","):
        raise ValueError(f"Invalid digest authentication qop={digest_info.qop} found.")

    hash_object = getattr(hashlib, digest_info.algorithm.lower())

    cnonce = hashlib.sha1(
        str(digest_info.cnonce_count).encode("utf-8")
        + digest_info.nonce.encode("utf-8")
        + time.ctime().encode("utf-8")
        + os.urandom(8)
    ).hexdigest()[:8]

    # calculate hash 1
    hash_1 = hash_object(
        ":".join(
            [
                username,
                digest_info.realm,
                password,
            ]
        ).encode("utf-8")
    ).hexdigest()

    # calculate hash 2
    hash_2 = hash_object(":".join([request_type, uri]).encode("utf-8")).hexdigest()

    # Concatenate the username, password, and realm with a colon separator
    credentials = ":".join(
        [hash_1, digest_info.nonce, digest_info.nc, cnonce, digest_info.qop, hash_2]
    )

    # Convert the concatenated string to bytes and calculate the hash
    response = hash_object(credentials.encode("utf-8")).hexdigest()

    return (
        f'Digest username="{username}", '
        f'realm="{digest_info.realm}", '
        f'nonce="{digest_info.nonce}", '
        f'uri="{uri}", '
        f'algorithm="{digest_info.algorithm}", '
        f"qop={digest_info.qop}, "
        f"nc={digest_info.nc}, "
        f'cnonce="{cnonce}", '
        f'response="{response}"'
    )
