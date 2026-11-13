import re

_CLASSIC_ADDRESS = re.compile(r"^r[1-9A-HJ-NP-Za-km-z]{24,34}$")


def is_valid_classic_address(address: str) -> bool:
    return bool(_CLASSIC_ADDRESS.fullmatch(address))
