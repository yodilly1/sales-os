"""
Salesforce Bulk API 2.0 handler for large data operations.

Supports:
- Insert, Update, Upsert, Delete operations
- Automatic batching for large datasets
- Job monitoring and result retrieval
- CSV data format handling
"""

import asyncio
import csv
import io
from typing import Any, Optional

import httpx

from backend.app.models.salesforce import (
    BulkJobRequest,
    BulkJobResponse,
    BulkJobResult,
    BulkJobStatus,
    BulkOperation,
    SalesforceAPIError,
)


class SalesforceBulkAPI:
    """
    Handles Salesforce Bulk API 2.0 operations.

    The Bulk API is optimized for loading or deleting large sets of data.
    Use it to insert, update, upsert, or delete many records asynchronously.
    """

    # Bulk API limits
    MAX_RECORDS_PER_JOB = 150_000_000  # 150 million records per job
    MAX_FILE_SIZE_BYTES = 150 * 1024 * 1024  # 150 MB per file
    RECOMMENDED_BATCH_SIZE = 10_000  # Recommended batch size for optimal performance

    def __init__(
        self,
        instance_url: str,
        access_token: str,
        api_version: str = "v59.0",
    ):
        """
        Initialize the Bulk API handler.

        Args:
            instance_url: Salesforce instance URL
            access_token: Valid access token
            api_version: Salesforce API version
        """
        self.instance_url = instance_url.rstrip("/")
        self.access_token = access_token
        self.api_version = api_version
        self.base_url = f"{self.instance_url}/services/data/{api_version}/jobs/ingest"
        self._http_client: Optional[httpx.AsyncClient] = None

    @property
    def http_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(
                timeout=httpx.Timeout(60.0),
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json",
                },
            )
        return self._http_client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()

    def _records_to_csv(self, records: list[dict[str, Any]]) -> str:
        """
        Convert records to CSV format for Bulk API.

        Args:
            records: List of record dictionaries

        Returns:
            CSV string
        """
        if not records:
            return ""

        # Get all unique field names
        fieldnames = set()
        for record in records:
            fieldnames.update(record.keys())
        fieldnames = sorted(fieldnames)

        # Write CSV
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)

        return output.getvalue()

    def _csv_to_records(self, csv_content: str) -> list[dict[str, Any]]:
        """
        Convert CSV content to list of records.

        Args:
            csv_content: CSV string

        Returns:
            List of record dictionaries
        """
        if not csv_content.strip():
            return []

        reader = csv.DictReader(io.StringIO(csv_content))
        return list(reader)

    async def create_job(
        self,
        sobject_type: str,
        operation: BulkOperation,
        external_id_field: Optional[str] = None,
        line_ending: str = "LF",
    ) -> BulkJobResponse:
        """
        Create a new Bulk API job.

        Args:
            sobject_type: Salesforce object type (e.g., "Lead", "Contact")
            operation: Type of operation (insert, update, upsert, delete)
            external_id_field: Required for upsert operations
            line_ending: Line ending format (LF or CRLF)

        Returns:
            BulkJobResponse with job details

        Raises:
            SalesforceAPIError: If job creation fails
        """
        payload = {
            "object": sobject_type,
            "operation": operation.value,
            "contentType": "CSV",
            "lineEnding": line_ending,
        }

        if operation == BulkOperation.UPSERT:
            if not external_id_field:
                raise SalesforceAPIError(
                    message="external_id_field is required for upsert operations",
                    status_code=400,
                )
            payload["externalIdFieldName"] = external_id_field

        response = await self.http_client.post(self.base_url, json=payload)

        if response.status_code not in (200, 201):
            error_data = response.json()
            raise SalesforceAPIError(
                message=error_data.get("message", "Failed to create bulk job"),
                status_code=response.status_code,
            )

        data = response.json()
        return BulkJobResponse(
            job_id=data["id"],
            state=BulkJobStatus(data["state"]),
            sobject_type=data["object"],
            operation=data["operation"],
            created_by_id=data.get("createdById"),
            created_date=data.get("createdDate"),
        )

    async def upload_job_data(
        self,
        job_id: str,
        records: list[dict[str, Any]],
    ) -> bool:
        """
        Upload data to a bulk job.

        Args:
            job_id: The bulk job ID
            records: Records to upload

        Returns:
            True if upload was successful

        Raises:
            SalesforceAPIError: If upload fails
        """
        csv_data = self._records_to_csv(records)

        response = await self.http_client.put(
            f"{self.base_url}/{job_id}/batches",
            content=csv_data,
            headers={
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "text/csv",
            },
        )

        if response.status_code not in (200, 201):
            error_data = response.json() if response.content else {"message": "Upload failed"}
            raise SalesforceAPIError(
                message=error_data.get("message", "Failed to upload job data"),
                status_code=response.status_code,
            )

        return True

    async def close_job(self, job_id: str) -> BulkJobResponse:
        """
        Close a bulk job to begin processing.

        Args:
            job_id: The bulk job ID

        Returns:
            Updated job response

        Raises:
            SalesforceAPIError: If close fails
        """
        response = await self.http_client.patch(
            f"{self.base_url}/{job_id}",
            json={"state": "UploadComplete"},
        )

        if response.status_code != 200:
            error_data = response.json()
            raise SalesforceAPIError(
                message=error_data.get("message", "Failed to close bulk job"),
                status_code=response.status_code,
            )

        data = response.json()
        return BulkJobResponse(
            job_id=data["id"],
            state=BulkJobStatus(data["state"]),
            sobject_type=data["object"],
            operation=data["operation"],
            number_records_processed=data.get("numberRecordsProcessed", 0),
            number_records_failed=data.get("numberRecordsFailed", 0),
        )

    async def abort_job(self, job_id: str) -> BulkJobResponse:
        """
        Abort a bulk job.

        Args:
            job_id: The bulk job ID

        Returns:
            Updated job response

        Raises:
            SalesforceAPIError: If abort fails
        """
        response = await self.http_client.patch(
            f"{self.base_url}/{job_id}",
            json={"state": "Aborted"},
        )

        if response.status_code != 200:
            error_data = response.json()
            raise SalesforceAPIError(
                message=error_data.get("message", "Failed to abort bulk job"),
                status_code=response.status_code,
            )

        data = response.json()
        return BulkJobResponse(
            job_id=data["id"],
            state=BulkJobStatus(data["state"]),
            sobject_type=data["object"],
            operation=data["operation"],
        )

    async def get_job_status(self, job_id: str) -> BulkJobResponse:
        """
        Get the current status of a bulk job.

        Args:
            job_id: The bulk job ID

        Returns:
            Current job status

        Raises:
            SalesforceAPIError: If request fails
        """
        response = await self.http_client.get(f"{self.base_url}/{job_id}")

        if response.status_code != 200:
            error_data = response.json()
            raise SalesforceAPIError(
                message=error_data.get("message", "Failed to get job status"),
                status_code=response.status_code,
            )

        data = response.json()
        return BulkJobResponse(
            job_id=data["id"],
            state=BulkJobStatus(data["state"]),
            sobject_type=data["object"],
            operation=data["operation"],
            created_by_id=data.get("createdById"),
            created_date=data.get("createdDate"),
            system_modstamp=data.get("systemModstamp"),
            number_records_processed=data.get("numberRecordsProcessed", 0),
            number_records_failed=data.get("numberRecordsFailed", 0),
        )

    async def get_successful_results(self, job_id: str) -> list[dict[str, Any]]:
        """
        Get successful results from a completed job.

        Args:
            job_id: The bulk job ID

        Returns:
            List of successful record results

        Raises:
            SalesforceAPIError: If request fails
        """
        response = await self.http_client.get(
            f"{self.base_url}/{job_id}/successfulResults",
            headers={
                "Authorization": f"Bearer {self.access_token}",
                "Accept": "text/csv",
            },
        )

        if response.status_code != 200:
            raise SalesforceAPIError(
                message="Failed to get successful results",
                status_code=response.status_code,
            )

        return self._csv_to_records(response.text)

    async def get_failed_results(self, job_id: str) -> list[dict[str, Any]]:
        """
        Get failed results from a completed job.

        Args:
            job_id: The bulk job ID

        Returns:
            List of failed record results with error details

        Raises:
            SalesforceAPIError: If request fails
        """
        response = await self.http_client.get(
            f"{self.base_url}/{job_id}/failedResults",
            headers={
                "Authorization": f"Bearer {self.access_token}",
                "Accept": "text/csv",
            },
        )

        if response.status_code != 200:
            raise SalesforceAPIError(
                message="Failed to get failed results",
                status_code=response.status_code,
            )

        return self._csv_to_records(response.text)

    async def wait_for_completion(
        self,
        job_id: str,
        poll_interval_seconds: float = 5.0,
        timeout_seconds: float = 3600.0,
    ) -> BulkJobResponse:
        """
        Wait for a bulk job to complete.

        Args:
            job_id: The bulk job ID
            poll_interval_seconds: Time between status checks
            timeout_seconds: Maximum time to wait

        Returns:
            Final job status

        Raises:
            SalesforceAPIError: If job fails or times out
        """
        elapsed = 0.0
        terminal_states = {
            BulkJobStatus.JOB_COMPLETE,
            BulkJobStatus.ABORTED,
            BulkJobStatus.FAILED,
        }

        while elapsed < timeout_seconds:
            status = await self.get_job_status(job_id)

            if status.state in terminal_states:
                return status

            await asyncio.sleep(poll_interval_seconds)
            elapsed += poll_interval_seconds

        raise SalesforceAPIError(
            message=f"Bulk job {job_id} timed out after {timeout_seconds} seconds",
            status_code=408,
        )

    async def execute_bulk_operation(
        self,
        request: BulkJobRequest,
        wait_for_completion: bool = True,
        poll_interval_seconds: float = 5.0,
    ) -> BulkJobResult:
        """
        Execute a complete bulk operation.

        This is a convenience method that creates a job, uploads data,
        closes the job, and optionally waits for completion.

        Args:
            request: Bulk job request with records
            wait_for_completion: Whether to wait for job to finish
            poll_interval_seconds: Time between status checks if waiting

        Returns:
            BulkJobResult with operation results

        Raises:
            SalesforceAPIError: If any step fails
        """
        # Create the job
        job = await self.create_job(
            sobject_type=request.sobject_type,
            operation=request.operation,
            external_id_field=request.external_id_field,
        )

        try:
            # Upload data in batches if necessary
            records = request.records
            batch_size = self.RECOMMENDED_BATCH_SIZE

            for i in range(0, len(records), batch_size):
                batch = records[i : i + batch_size]
                await self.upload_job_data(job.job_id, batch)

            # Close the job to start processing
            await self.close_job(job.job_id)

            if wait_for_completion:
                # Wait for completion
                final_status = await self.wait_for_completion(
                    job.job_id,
                    poll_interval_seconds=poll_interval_seconds,
                )

                # Get results
                successful = await self.get_successful_results(job.job_id)
                failed = await self.get_failed_results(job.job_id)

                return BulkJobResult(
                    job_id=job.job_id,
                    state=final_status.state,
                    number_records_processed=final_status.number_records_processed,
                    number_records_failed=final_status.number_records_failed,
                    successful_records=successful,
                    failed_records=failed,
                )
            else:
                # Return immediately without waiting
                return BulkJobResult(
                    job_id=job.job_id,
                    state=BulkJobStatus.UPLOAD_COMPLETE,
                    number_records_processed=0,
                    number_records_failed=0,
                )

        except Exception as e:
            # Try to abort the job on error
            try:
                await self.abort_job(job.job_id)
            except Exception:
                pass  # Ignore abort errors
            raise e

    async def delete_job(self, job_id: str) -> bool:
        """
        Delete a bulk job and its data.

        Args:
            job_id: The bulk job ID

        Returns:
            True if deletion was successful

        Raises:
            SalesforceAPIError: If deletion fails
        """
        response = await self.http_client.delete(f"{self.base_url}/{job_id}")

        if response.status_code != 204:
            error_data = response.json() if response.content else {"message": "Delete failed"}
            raise SalesforceAPIError(
                message=error_data.get("message", "Failed to delete bulk job"),
                status_code=response.status_code,
            )

        return True

    async def list_jobs(
        self,
        is_pk_chunking_enabled: Optional[bool] = None,
        job_type: Optional[str] = None,
    ) -> list[BulkJobResponse]:
        """
        List all bulk jobs.

        Args:
            is_pk_chunking_enabled: Filter by PK chunking status
            job_type: Filter by job type (BigObjectIngest, Classic, V2Ingest)

        Returns:
            List of bulk jobs

        Raises:
            SalesforceAPIError: If request fails
        """
        params = {}
        if is_pk_chunking_enabled is not None:
            params["isPkChunkingEnabled"] = str(is_pk_chunking_enabled).lower()
        if job_type:
            params["jobType"] = job_type

        response = await self.http_client.get(self.base_url, params=params)

        if response.status_code != 200:
            error_data = response.json()
            raise SalesforceAPIError(
                message=error_data.get("message", "Failed to list bulk jobs"),
                status_code=response.status_code,
            )

        data = response.json()
        jobs = []

        for job_data in data.get("records", []):
            jobs.append(
                BulkJobResponse(
                    job_id=job_data["id"],
                    state=BulkJobStatus(job_data["state"]),
                    sobject_type=job_data["object"],
                    operation=job_data["operation"],
                    created_by_id=job_data.get("createdById"),
                    created_date=job_data.get("createdDate"),
                    system_modstamp=job_data.get("systemModstamp"),
                    number_records_processed=job_data.get("numberRecordsProcessed", 0),
                    number_records_failed=job_data.get("numberRecordsFailed", 0),
                )
            )

        return jobs
