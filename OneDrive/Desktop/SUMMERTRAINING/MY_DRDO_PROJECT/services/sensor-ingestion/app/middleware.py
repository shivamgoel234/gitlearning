"""
Custom middleware for request handling.

Implements request ID tracking, logging, and timing.
"""

import time
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import logging

logger = logging.getLogger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add unique request ID to each request.
    
    Adds X-Request-ID header for request tracking and distributed tracing.
    """
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Process request and add request ID.
        
        Args:
            request: Incoming request
            call_next: Next middleware/route handler
            
        Returns:
            Response with request ID header
        """
        # Get or generate request ID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        
        # Store in request state for access in route handlers
        request.state.request_id = request_id
        
        # Process request
        response = await call_next(request)
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all incoming requests and responses.
    
    Logs request method, path, status code, and duration.
    """
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Log request and response information.
        
        Args:
            request: Incoming request
            call_next: Next middleware/route handler
            
        Returns:
            Response from route handler
        """
        # Start timer
        start_time = time.time()
        
        # Get request info
        method = request.method
        path = request.url.path
        request_id = getattr(request.state, "request_id", "unknown")
        
        # Log incoming request
        logger.info(
            f"Incoming request: {method} {path}",
            extra={"request_id": request_id}
        )
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Log response
            logger.info(
                f"Request completed: {method} {path} - "
                f"Status: {response.status_code} - "
                f"Duration: {duration_ms:.2f}ms",
                extra={
                    "request_id": request_id,
                    "duration_ms": duration_ms
                }
            )
            
            return response
            
        except Exception as e:
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Log error
            logger.error(
                f"Request failed: {method} {path} - "
                f"Error: {str(e)} - "
                f"Duration: {duration_ms:.2f}ms",
                extra={
                    "request_id": request_id,
                    "duration_ms": duration_ms
                },
                exc_info=True
            )
            
            raise
