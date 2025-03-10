class MWAAAPIError(Exception):
    """
    Raised when boto can connect to MWAA, but the Airflow API returns
    an error
    """

    def __init__(self, request, status_code, api_response):
        self.request = request
        self.status_code = status_code
        self.response = api_response
        super().__init__(
            f"MWAA API Error for request {self.request}: {self.status_code} - "
            f"{self.response}",
        )
