"""API client for backend communication."""
import requests
from typing import Dict, Any, Optional, List
import os
import time
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()


class APIError(Exception):
    """Base API error."""
    def __init__(self, message: str, status_code: Optional[int] = None, response: Optional[Dict] = None):
        self.message = message
        self.status_code = status_code
        self.response = response
        super().__init__(self.message)


class NetworkError(APIError):
    """Network-related errors."""
    pass


class ValidationError(APIError):
    """Validation errors."""
    pass


class APIClient:
    """Client for Road Safety API."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3,
    ):
        """Initialize API client."""
        self.base_url = base_url or os.getenv("API_URL", "http://localhost:8000")
        self.api_key = api_key or os.getenv("API_KEY", "")
        self.headers = {"X-API-Key": self.api_key, "Content-Type": "application/json"}
        self.timeout = timeout
        self.max_retries = max_retries

    def _make_request(
        self,
        method: str,
        url: str,
        retry_status_codes: List[int] = [500, 502, 503, 504],
        **kwargs
    ) -> requests.Response:
        """Make HTTP request with retry logic."""
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                # Add timeout to kwargs
                kwargs.setdefault("timeout", self.timeout)
                
                response = requests.request(method, url, headers=self.headers, **kwargs)
                
                # Check if we should retry
                if response.status_code in retry_status_codes and attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    time.sleep(wait_time)
                    continue
                
                # Raise for status if not a retryable error
                if response.status_code not in retry_status_codes:
                    response.raise_for_status()
                
                return response
                
            except requests.exceptions.Timeout as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
                    continue
                raise NetworkError(f"Request timeout after {self.timeout}s", response={"error": str(e)})
                
            except requests.exceptions.ConnectionError as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
                    continue
                raise NetworkError(f"Connection error: {str(e)}", response={"error": str(e)})
                
            except requests.exceptions.RequestException as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
                    continue
                raise NetworkError(f"Request failed: {str(e)}", response={"error": str(e)})
        
        # If we get here, all retries failed
        if last_exception:
            raise last_exception

    def _handle_error_response(self, response: requests.Response):
        """Handle error responses and raise appropriate exceptions."""
        status_code = response.status_code
        
        try:
            error_data = response.json()
            error_message = error_data.get("detail", error_data.get("error", "Unknown error"))
        except:
            error_message = response.text or f"HTTP {status_code} error"
        
        if status_code == 400:
            raise ValidationError(error_message, status_code=status_code, response=error_data if 'error_data' in locals() else None)
        elif status_code == 401:
            raise APIError("Unauthorized: Invalid API key", status_code=status_code)
        elif status_code == 429:
            raise APIError("Rate limit exceeded", status_code=status_code)
        elif status_code >= 500:
            raise APIError(f"Server error: {error_message}", status_code=status_code)
        else:
            raise APIError(error_message, status_code=status_code)

    def search(
        self,
        query: str,
        category: Optional[List[str]] = None,
        problem: Optional[List[str]] = None,
        speed_min: Optional[int] = None,
        speed_max: Optional[int] = None,
        strategy: str = "auto",
        max_results: int = 5,
    ) -> Dict[str, Any]:
        """Search for interventions."""
        url = f"{self.base_url}/api/v1/search"

        payload = {"query": query, "strategy": strategy, "max_results": max_results}

        # Add filters if provided
        filters = {}
        if category:
            filters["category"] = category
        if problem:
            filters["problem"] = problem
        if speed_min is not None:
            filters["speed_min"] = speed_min
        if speed_max is not None:
            filters["speed_max"] = speed_max

        if filters:
            payload["filters"] = filters

        try:
            response = self._make_request("POST", url, json=payload)
            return response.json()
        except requests.exceptions.HTTPError as e:
            if hasattr(e, 'response') and e.response is not None:
                self._handle_error_response(e.response)
            else:
                raise APIError(f"HTTP error: {str(e)}")
        except (NetworkError, APIError, ValidationError):
            raise
        except Exception as e:
            raise NetworkError(f"Unexpected error: {str(e)}")

    def get_intervention(self, intervention_id: str) -> Dict[str, Any]:
        """Get specific intervention by ID."""
        url = f"{self.base_url}/api/v1/interventions/{intervention_id}"

        try:
            response = self._make_request("GET", url)
            return response.json()
        except requests.exceptions.HTTPError as e:
            self._handle_error_response(e.response)
        except (NetworkError, APIError):
            raise

    def list_interventions(
        self, category: Optional[str] = None, problem: Optional[str] = None, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """List interventions with filters."""
        url = f"{self.base_url}/api/v1/interventions"

        params = {"limit": limit}
        if category:
            params["category"] = category
        if problem:
            params["problem"] = problem

        try:
            response = self._make_request("GET", url, params=params)
            return response.json()
        except requests.exceptions.HTTPError as e:
            self._handle_error_response(e.response)
        except (NetworkError, APIError):
            raise

    def get_categories(self) -> List[str]:
        """Get list of categories."""
        url = f"{self.base_url}/api/v1/interventions/categories/list"

        try:
            response = self._make_request("GET", url)
            return response.json()
        except requests.exceptions.HTTPError as e:
            self._handle_error_response(e.response)
        except (NetworkError, APIError):
            raise

    def get_problems(self) -> List[str]:
        """Get list of problem types."""
        url = f"{self.base_url}/api/v1/interventions/problems/list"

        try:
            response = self._make_request("GET", url)
            return response.json()
        except requests.exceptions.HTTPError as e:
            self._handle_error_response(e.response)
        except (NetworkError, APIError):
            raise

    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        url = f"{self.base_url}/stats"

        try:
            response = self._make_request("GET", url)
            return response.json()
        except requests.exceptions.HTTPError as e:
            self._handle_error_response(e.response)
        except (NetworkError, APIError):
            raise

    def health_check(self) -> Dict[str, Any]:
        """Check API health."""
        url = f"{self.base_url}/health"

        try:
            response = self._make_request("GET", url)
            return response.json()
        except requests.exceptions.HTTPError as e:
            self._handle_error_response(e.response)
        except (NetworkError, APIError):
            raise
