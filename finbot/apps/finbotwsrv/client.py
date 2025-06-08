from finbot.core.schema import CredentialsPayloadType, CurrencyCode
from finbot.core.web_service import WebServiceClient
from finbot.services.financial_data_fetcher import schema


class FinbotwsrvClient(WebServiceClient):
    service_name = "finbotwsrv"

    def __init__(self, server_endpoint: str):
        super().__init__(server_endpoint)

    def get_financial_data(
        self,
        provider_id: str,
        credentials_data: CredentialsPayloadType,
        line_items: list[schema.LineItem],
        user_account_currency: CurrencyCode,
    ) -> schema.GetFinancialDataResponse:
        return schema.GetFinancialDataResponse.model_validate(
            self.post(
                "financial_data/",
                schema.GetFinancialDataRequest(
                    provider_id=provider_id,
                    credentials=credentials_data,
                    items=line_items,
                    user_account_currency=user_account_currency,
                ),
            )
        )

    def validate_credentials(
        self,
        provider_id: str,
        credentials_data: CredentialsPayloadType,
        user_account_currency: CurrencyCode,
    ) -> schema.ValidateCredentialsResponse:
        return schema.ValidateCredentialsResponse.model_validate(
            self.post(
                "validate_credentials/",
                schema.ValidateCredentialsRequest(
                    provider_id=provider_id,
                    credentials=credentials_data,
                    user_account_currency=user_account_currency,
                ),
            )
        )
