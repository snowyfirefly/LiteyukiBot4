from pydantic import BaseModel


class Location(BaseModel):
    name: str
    id: str
    lat: str
    lon: str
    adm2: str
    adm1: str
    country: str
    tz: str
    utcOffset: str
    isDst: str
    type: str
    rank: str
    fxLink: str
    sources: str
    license: str