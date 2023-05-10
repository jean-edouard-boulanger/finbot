from finbot.apps.finbotwsrv import schema
from finbot.core.schema import CredentialsPayloadType
from finbot.core.web_service import WebServiceClient


class FinbotwsrvClient(WebServiceClient):
    service_name = "finbotwsrv"

    def __init__(self, server_endpoint: str):
        super().__init__(server_endpoint)

    def get_financial_data(
        self,
        provider_id: str,
        credentials_data: CredentialsPayloadType,
        line_items: list[schema.LineItem],
    ) -> schema.GetFinancialDataResponse:
        return schema.GetFinancialDataResponse.parse_obj(
            self.post(
                "financial_data/",
                schema.GetFinancialDataRequest(
                    provider_id=provider_id,
                    credentials=credentials_data,
                    items=line_items,
                ),
            )
        )

    def validate_credentials(
        self,
        provider_id: str,
        credentials_data: CredentialsPayloadType,
    ) -> schema.ValidateCredentialsResponse:
        return schema.ValidateCredentialsResponse.parse_obj(
            self.post(
                "validate_credentials/",
                schema.ValidateCredentialsRequest(
                    provider_id=provider_id,
                    credentials=credentials_data,
                ),
            )
        )
