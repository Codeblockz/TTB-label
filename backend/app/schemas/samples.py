from pydantic import BaseModel


class SampleLabel(BaseModel):
    filename: str
    brand_name: str
    class_type: str
    alcohol_content: str
    net_contents: str
    bottler_name_address: str
    country_of_origin: str
    description: str
    expected_verdict: str
    image_url: str


class SampleLabelsResponse(BaseModel):
    samples: list[SampleLabel]
