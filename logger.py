#!/usr/bin/env python3
"""
Nature Remo Temperature Logger

This script fetches temperature data from Nature Remo API and saves it to
a CSV file.
"""

import os
import time
import logging
import requests
from typing import Optional, Callable, TypeVar


# Configure logging
class SanitizingFormatter(logging.Formatter):
    """
    Custom formatter that sanitizes sensitive information from log messages.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record with sanitization.

        Args:
            record: Log record to format

        Returns:
            str: Formatted and sanitized log message
        """
        # Format the message first
        formatted = super().format(record)
        
        # Sanitize the formatted message
        token = os.environ.get('NATURE_REMO_TOKEN')
        if token:
            # Replace full token
            formatted = formatted.replace(token, '[REDACTED]')
            
            # Also create a masked version for partial matches
            if len(token) > 8:
                masked = f"{token[:4]}***{token[-4:]}"
                formatted = formatted.replace(token, masked)
        
        return formatted


def setup_logging(level: str = "INFO") -> logging.Logger:
    """
    Set up logging configuration.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)

    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger("temperature_logger")
    
    # Avoid adding multiple handlers if called multiple times
    if logger.handlers:
        return logger
    
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    # Create console handler with formatting
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    
    # Create formatter with sanitization
    formatter = SanitizingFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
    
    logger.addHandler(handler)
    
    return logger


# Initialize logger
logger = setup_logging(os.environ.get('LOG_LEVEL', 'INFO'))


class APIError(Exception):
    """Exception raised for API-related errors."""
    pass


class AuthenticationError(APIError):
    """Exception raised for authentication errors."""
    pass


class TimeoutError(APIError):
    """Exception raised for timeout errors."""
    pass


class RetryableError(APIError):
    """Exception raised for errors that can be retried."""
    pass


T = TypeVar('T')


def is_retryable_error(error: Exception) -> bool:
    """
    Determine if an error is retryable.

    Args:
        error: The exception to check

    Returns:
        bool: True if the error can be retried, False otherwise
    """
    # RetryableError is always retryable
    if isinstance(error, RetryableError):
        return True

    # Timeout errors are retryable
    if isinstance(error, TimeoutError):
        return True

    # Authentication errors are not retryable
    if isinstance(error, AuthenticationError):
        return False

    # Check for specific error patterns in APIError
    if isinstance(error, APIError):
        error_msg = str(error)
        # Client errors (4xx) are not retryable
        if "Client error: 4" in error_msg:
            return False

    return False


def retry_with_backoff(
    func: Callable[[], T],
    max_retries: int = 3,
    initial_delay: float = 1.0
) -> T:
    """
    Execute a function with exponential backoff retry logic.

    Args:
        func: The function to execute
        max_retries: Maximum number of retry attempts (default: 3)
        initial_delay: Initial delay in seconds (default: 1.0)

    Returns:
        The return value of the function

    Raises:
        The last exception if all retries fail
    """
    last_exception = None
    
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            last_exception = e
            
            # Check if error is retryable
            if not is_retryable_error(e):
                logger.error(
                    f"Non-retryable error occurred: {type(e).__name__} - {e}"
                )
                raise
            
            # If this was the last attempt, raise the exception
            if attempt == max_retries - 1:
                logger.error(
                    f"All {max_retries} retry attempts failed. "
                    f"Last error: {type(e).__name__} - {e}"
                )
                raise
            
            # Calculate exponential backoff delay
            delay = initial_delay * (2 ** attempt)
            
            # Log retry attempt
            logger.warning(
                f"Retryable error occurred: {type(e).__name__} - {e}. "
                f"Retry attempt {attempt + 1}/{max_retries} "
                f"after {delay}s delay"
            )
            
            # Wait before retrying
            time.sleep(delay)
    
    # This should never be reached, but just in case
    if last_exception:
        raise last_exception
    raise RuntimeError("Unexpected error in retry logic")


def sanitize_log(message: str, token: Optional[str] = None) -> str:
    """
    Sanitize log message to remove sensitive information.

    Replaces API tokens with a masked placeholder to prevent
    accidental exposure in logs.

    Args:
        message: Log message to sanitize
        token: API token to mask (optional). If None, attempts to get
               from environment variable.

    Returns:
        str: Sanitized log message with tokens masked
    """
    if not message:
        return message
    
    # Get token from environment if not provided
    if token is None:
        token = os.environ.get('NATURE_REMO_TOKEN')
    
    # If no token to sanitize, return original message
    if not token:
        return message
    
    # Replace token with masked placeholder
    sanitized = message.replace(token, '[REDACTED]')
    
    # Also mask partial tokens (first/last few characters visible)
    # This handles cases where token might be in different formats
    if len(token) > 8:
        # Show first 4 and last 4 characters
        masked_token = f"{token[:4]}***{token[-4:]}"
        sanitized = sanitized.replace(token, masked_token)
    else:
        # For short tokens, just use asterisks
        sanitized = sanitized.replace(token, '***')
    
    return sanitized


def mask_token(token: str) -> str:
    """
    Mask an API token for safe display in logs.

    Args:
        token: API token to mask

    Returns:
        str: Masked token string
    """
    if not token:
        return ''
    
    if len(token) <= 8:
        return '***'
    
    # Show first 4 and last 4 characters
    return f"{token[:4]}***{token[-4:]}"


def get_api_token() -> str:
    """
    Get API token from environment variable.

    Returns:
        str: API access token

    Raises:
        AuthenticationError: If token is not found in environment
    """
    token = os.environ.get('NATURE_REMO_TOKEN')
    
    if not token:
        error_msg = "NATURE_REMO_TOKEN environment variable not set"
        logger.error(error_msg)
        raise AuthenticationError(error_msg)
    
    logger.debug("Successfully retrieved API token from environment")
    return token


def load_config() -> dict:
    """
    Load configuration from environment variables with default values.

    Returns:
        dict: Configuration dictionary with the following keys:
            - format: Output format ('csv' or 'json'), default 'csv'
            - output_dir: Output directory path, default 'data'
            - csv_file: CSV file path, default 'data/temperature.csv'
            - timeout: API request timeout in seconds, default 30
            - max_retries: Maximum retry attempts, default 3
            - log_level: Logging level, default 'INFO'
    """
    config = {
        'format': os.environ.get('OUTPUT_FORMAT', 'csv'),
        'output_dir': os.environ.get('OUTPUT_DIR', 'data'),
        'timeout': int(os.environ.get('API_TIMEOUT', '30')),
        'max_retries': int(os.environ.get('MAX_RETRIES', '3')),
        'log_level': os.environ.get('LOG_LEVEL', 'INFO'),
    }
    
    # Construct CSV file path from output_dir
    config['csv_file'] = os.path.join(
        config['output_dir'],
        'temperature.csv'
    )
    
    logger.debug(f"Loaded configuration: {config}")
    return config


def get_temperature(token: Optional[str] = None, timeout: int = 30) -> float:
    """
    Fetch current temperature from Nature Remo API.

    Args:
        token: API access token. If None, reads from environment variable.
        timeout: Request timeout in seconds (default: 30)

    Returns:
        float: Temperature in Celsius

    Raises:
        APIError: If API call fails
        AuthenticationError: If authentication fails
        TimeoutError: If request times out
        ValueError: If response parsing fails
    """
    if token is None:
        token = os.environ.get('NATURE_REMO_TOKEN')

    if not token:
        logger.error("API token not provided")
        raise AuthenticationError("API token not provided")

    api_url = "https://api.nature.global/1/devices"
    headers = {
        "Authorization": f"Bearer {token}"
    }

    logger.debug(f"Sending request to {api_url}")

    try:
        response = requests.get(api_url, headers=headers, timeout=timeout)

        logger.debug(
            f"Received response with status code: {response.status_code}"
        )

        # Handle authentication errors
        if response.status_code == 401:
            logger.error(
                "Authentication failed: Invalid or expired API token"
            )
            raise AuthenticationError("Invalid or expired API token")

        # Handle other client errors
        if response.status_code >= 400 and response.status_code < 500:
            error_msg = (
                f"Client error: {response.status_code} - {response.text}"
            )
            logger.error(error_msg)
            raise APIError(error_msg)

        # Handle server errors
        if response.status_code >= 500:
            error_msg = (
                f"Server error: {response.status_code} - {response.text}"
            )
            logger.error(error_msg)
            raise RetryableError(error_msg)

        # Parse successful response
        if response.status_code == 200:
            data = response.json()

            if not data or len(data) == 0:
                logger.error("No devices found in API response")
                raise ValueError("No devices found in API response")

            # Extract temperature from first device
            device = data[0]
            if 'newest_events' not in device:
                logger.error("No newest_events in device data")
                raise ValueError("No newest_events in device data")

            if 'te' not in device['newest_events']:
                logger.error("No temperature event in device data")
                raise ValueError("No temperature event in device data")

            temperature = device['newest_events']['te']['val']

            if not isinstance(temperature, (int, float)):
                logger.error(f"Invalid temperature value: {temperature}")
                raise ValueError(f"Invalid temperature value: {temperature}")

            logger.info(
                f"Successfully retrieved temperature: {temperature}°C"
            )
            return float(temperature)

        error_msg = f"Unexpected status code: {response.status_code}"
        logger.error(error_msg)
        raise APIError(error_msg)

    except requests.exceptions.Timeout:
        error_msg = f"Request timed out after {timeout} seconds"
        logger.error(error_msg)
        raise TimeoutError(error_msg)
    except requests.exceptions.RequestException as e:
        error_msg = f"Network error: {e}"
        logger.error(error_msg)
        raise RetryableError(error_msg)


def get_temperature_with_retry(
    token: Optional[str] = None,
    timeout: int = 30,
    max_retries: int = 3
) -> float:
    """
    Fetch current temperature from Nature Remo API with retry logic.

    Args:
        token: API access token. If None, reads from environment variable.
        timeout: Request timeout in seconds (default: 30)
        max_retries: Maximum number of retry attempts (default: 3)

    Returns:
        float: Temperature in Celsius

    Raises:
        APIError: If API call fails after all retries
        AuthenticationError: If authentication fails
        TimeoutError: If request times out after all retries
        ValueError: If response parsing fails
    """
    return retry_with_backoff(
        lambda: get_temperature(token=token, timeout=timeout),
        max_retries=max_retries
    )


def validate_temperature(temperature: float) -> tuple[bool, str]:
    """
    Validate temperature value.

    Checks if the temperature is a number and within a reasonable range.
    Logs a warning if the temperature is outside the normal range
    (-50°C to 50°C).

    Args:
        temperature: Temperature value to validate

    Returns:
        tuple[bool, str]: (is_valid, error_message)
            - is_valid: True if temperature is a valid number,
              False otherwise
            - error_message: Empty string if valid, error description
              if invalid
    """
    # Check if temperature is a number
    if not isinstance(temperature, (int, float)):
        error_msg = (
            f"Temperature must be a number, got "
            f"{type(temperature).__name__}"
        )
        logger.error(error_msg)
        return False, error_msg

    # Check for NaN or infinity
    if temperature != temperature:  # NaN check
        error_msg = "Temperature cannot be NaN"
        logger.error(error_msg)
        return False, error_msg

    try:
        if abs(temperature) == float('inf'):
            error_msg = "Temperature cannot be infinity"
            logger.error(error_msg)
            return False, error_msg
    except (ValueError, OverflowError):
        pass

    # Check if temperature is within reasonable range
    if temperature < -50.0 or temperature > 50.0:
        warning_msg = (
            f"Temperature {temperature}°C is outside normal range "
            f"(-50°C to 50°C)"
        )
        logger.warning(warning_msg)
        # Still valid, just outside normal range

    return True, ""


def validate_timestamp(timestamp: str) -> tuple[bool, str]:
    """
    Validate timestamp format.

    Checks if the timestamp is in ISO 8601 format.

    Args:
        timestamp: Timestamp string to validate

    Returns:
        tuple[bool, str]: (is_valid, error_message)
            - is_valid: True if timestamp is valid ISO 8601 format,
              False otherwise
            - error_message: Empty string if valid, error description
              if invalid
    """
    from datetime import datetime

    if not isinstance(timestamp, str):
        error_msg = (
            f"Timestamp must be a string, got "
            f"{type(timestamp).__name__}"
        )
        logger.error(error_msg)
        return False, error_msg

    try:
        # Try to parse as ISO 8601 format
        datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        return True, ""
    except ValueError as e:
        error_msg = f"Invalid timestamp format: {e}"
        logger.error(error_msg)
        return False, error_msg


def format_timestamp(dt=None) -> str:
    """
    Format a datetime object as ISO 8601 string with timezone.

    Args:
        dt: datetime object to format. If None, uses current time.

    Returns:
        str: ISO 8601 formatted timestamp string with timezone
    """
    from datetime import datetime, timezone

    if dt is None:
        dt = datetime.now(timezone.utc)

    # Ensure timezone info is present
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    return dt.isoformat()


def check_duplicate_timestamp(timestamp: str, csv_file: str) -> bool:
    """
    Check if a timestamp already exists in the CSV file.

    Args:
        timestamp: Timestamp to check for duplicates
        csv_file: Path to the CSV file

    Returns:
        bool: True if timestamp is a duplicate, False otherwise
    """
    import csv

    # If file doesn't exist, no duplicates possible
    if not os.path.exists(csv_file):
        return False

    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('timestamp') == timestamp:
                    logger.warning(
                        f"Duplicate timestamp detected: {timestamp}"
                    )
                    return True
    except Exception as e:
        logger.error(
            f"Error reading CSV file for duplicate check: {e}"
        )
        # If we can't read the file, assume no duplicates to allow saving
        return False

    return False


def validate_csv_format(csv_file: str) -> tuple[bool, str]:
    """
    Validate CSV file format.

    Checks that the file:
    - Is valid CSV format
    - Has correct headers (timestamp, temperature)
    - Uses UTF-8 encoding without BOM

    Args:
        csv_file: Path to the CSV file to validate

    Returns:
        tuple[bool, str]: (is_valid, error_message)
            - is_valid: True if CSV format is valid, False otherwise
            - error_message: Empty string if valid, error description
              if invalid
    """
    import csv

    # If file doesn't exist, it's valid (will be created)
    if not os.path.exists(csv_file):
        return True, ""

    try:
        # Check for BOM
        with open(csv_file, 'rb') as f:
            first_bytes = f.read(3)
            if first_bytes == b'\xef\xbb\xbf':
                error_msg = "CSV file contains UTF-8 BOM, which is not allowed"
                logger.error(error_msg)
                return False, error_msg

        # Check CSV format and headers
        with open(csv_file, 'r', encoding='utf-8') as f:
            # Try to read as CSV
            try:
                reader = csv.reader(f)
                first_row = next(reader, None)
            except csv.Error as e:
                error_msg = f"Invalid CSV format: {e}"
                logger.error(error_msg)
                return False, error_msg

            # Check headers
            if first_row is None:
                # Empty file is valid
                return True, ""

            expected_headers = ['timestamp', 'temperature']
            if first_row != expected_headers:
                error_msg = (
                    f"Invalid CSV headers. Expected {expected_headers}, "
                    f"got {first_row}"
                )
                logger.error(error_msg)
                return False, error_msg

        logger.debug(f"CSV file format validation passed: {csv_file}")
        return True, ""

    except UnicodeDecodeError as e:
        error_msg = f"File is not valid UTF-8: {e}"
        logger.error(error_msg)
        return False, error_msg
    except Exception as e:
        error_msg = f"Error validating CSV file: {e}"
        logger.error(error_msg)
        return False, error_msg


def save_temperature(
    timestamp: str,
    temperature: float,
    csv_file: str = "data/temperature.csv"
) -> None:
    """
    Save temperature data to CSV file.

    Creates the file with headers if it doesn't exist, otherwise appends
    the data to the existing file. Temperature is formatted to 1 decimal
    place. Uses a temporary file for safe writing with rollback on failure.
    Validates CSV format before writing.

    Args:
        timestamp: ISO 8601 formatted timestamp
        temperature: Temperature value in Celsius
        csv_file: Path to the CSV file (default: data/temperature.csv)

    Raises:
        IOError: If file writing fails
        ValueError: If timestamp or temperature validation fails or CSV
                    format is invalid
    """
    import csv
    import shutil

    # Validate CSV format before proceeding
    is_valid_csv, csv_error = validate_csv_format(csv_file)
    if not is_valid_csv:
        raise ValueError(f"Invalid CSV format: {csv_error}")

    # Validate timestamp
    is_valid_ts, ts_error = validate_timestamp(timestamp)
    if not is_valid_ts:
        raise ValueError(f"Invalid timestamp: {ts_error}")

    # Validate temperature
    is_valid_temp, temp_error = validate_temperature(temperature)
    if not is_valid_temp:
        raise ValueError(f"Invalid temperature: {temp_error}")

    # Check for duplicate timestamp
    if check_duplicate_timestamp(timestamp, csv_file):
        error_msg = f"Duplicate timestamp: {timestamp}"
        logger.error(error_msg)
        raise ValueError(error_msg)

    # Format temperature to 1 decimal place
    formatted_temp = f"{temperature:.1f}"

    # Ensure directory exists
    csv_dir = os.path.dirname(csv_file)
    if csv_dir and not os.path.exists(csv_dir):
        try:
            os.makedirs(csv_dir, exist_ok=True)
            logger.debug(f"Created directory: {csv_dir}")
        except OSError as e:
            error_msg = f"Failed to create directory {csv_dir}: {e}"
            logger.error(error_msg)
            raise IOError(error_msg)

    # Check if file exists to determine if we need to write headers
    file_exists = os.path.exists(csv_file)
    needs_header = not file_exists or os.path.getsize(csv_file) == 0

    # Use temporary file for safe writing
    temp_file = f"{csv_file}.tmp"

    try:
        # If file exists, copy it to temp file first
        if file_exists:
            shutil.copy2(csv_file, temp_file)
            logger.debug(
                f"Copied existing file to temporary file: {temp_file}"
            )

        # Open temp file in append mode with UTF-8 encoding (no BOM)
        with open(temp_file, 'a', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)

            # Write header if file is new
            if needs_header:
                writer.writerow(['timestamp', 'temperature'])
                logger.debug("Created CSV file with headers")

            # Write data row
            writer.writerow([timestamp, formatted_temp])
            logger.debug(
                f"Wrote data to temporary file: "
                f"{timestamp}, {formatted_temp}°C"
            )

        # If write was successful, replace original file with temp file
        shutil.move(temp_file, csv_file)
        logger.info(
            f"Saved temperature data: {timestamp}, {formatted_temp}°C"
        )

    except Exception as e:
        # Clean up temporary file on error
        if os.path.exists(temp_file):
            try:
                os.remove(temp_file)
                logger.debug(
                    f"Removed temporary file after error: {temp_file}"
                )
            except OSError:
                pass  # Ignore cleanup errors

        error_msg = f"Failed to write to CSV file {csv_file}: {e}"
        logger.error(error_msg)
        raise IOError(error_msg)


def main() -> None:
    """
    Main entry point for the temperature logger.

    Orchestrates the entire temperature logging process:
    1. Loads configuration
    2. Retrieves API token from environment
    3. Fetches temperature data from Nature Remo API
    4. Validates the data
    5. Saves to CSV file
    6. Handles errors appropriately

    Exits with status code 0 on success, 1 on failure.
    """
    import sys

    try:
        # Load configuration
        logger.info("Starting temperature logger")
        config = load_config()
        logger.debug(f"Configuration loaded: {config}")

        # Get API token
        logger.info("Retrieving API token from environment")
        token = get_api_token()
        logger.debug(f"API token retrieved: {mask_token(token)}")

        # Fetch temperature data with retry logic
        logger.info("Fetching temperature data from Nature Remo API")
        temperature = get_temperature_with_retry(
            token=token,
            timeout=config['timeout'],
            max_retries=config['max_retries']
        )
        logger.info(f"Temperature retrieved: {temperature}°C")

        # Generate timestamp
        timestamp = format_timestamp()
        logger.debug(f"Generated timestamp: {timestamp}")

        # Validate data
        logger.info("Validating temperature data")
        is_valid_temp, temp_error = validate_temperature(temperature)
        if not is_valid_temp:
            logger.error(f"Temperature validation failed: {temp_error}")
            sys.exit(1)

        is_valid_ts, ts_error = validate_timestamp(timestamp)
        if not is_valid_ts:
            logger.error(f"Timestamp validation failed: {ts_error}")
            sys.exit(1)

        logger.info("Data validation passed")

        # Save to CSV
        csv_file = config['csv_file']
        logger.info(f"Saving temperature data to {csv_file}")
        save_temperature(timestamp, temperature, csv_file)
        logger.info("Temperature data saved successfully")

        # Success
        logger.info("Temperature logging completed successfully")
        sys.exit(0)

    except AuthenticationError as e:
        logger.error(f"Authentication error: {e}")
        logger.error("Please check your NATURE_REMO_TOKEN environment variable")
        sys.exit(1)

    except TimeoutError as e:
        logger.error(f"Timeout error: {e}")
        logger.error("API request timed out. Please check your network connection")
        sys.exit(1)

    except APIError as e:
        logger.error(f"API error: {e}")
        logger.error("Failed to retrieve temperature data from Nature Remo API")
        sys.exit(1)

    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        logger.error("Temperature data failed validation")
        sys.exit(1)

    except IOError as e:
        logger.error(f"File I/O error: {e}")
        logger.error("Failed to save temperature data to file")
        sys.exit(1)

    except Exception as e:
        logger.error(f"Unexpected error: {type(e).__name__} - {e}")
        logger.error("An unexpected error occurred during temperature logging")
        sys.exit(1)


if __name__ == "__main__":
    main()
