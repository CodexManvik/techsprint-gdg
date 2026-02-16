"""
Circuit Breaker Pattern for LLM Fault Tolerance

Prevents cascading failures when LLM service is down.
"""
import time
import asyncio
import logging
from enum import Enum
from typing import Callable, Any

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    CLOSED = "closed"  # Normal operation
    OPEN = "open"      # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing recovery


class CircuitBreaker:
    """
    Circuit Breaker for LLM calls.
    
    Opens after {failure_threshold} consecutive failures.
    Auto-recovers after {recovery_timeout} seconds.
    """
    
    def __init__(
        self, 
        failure_threshold: int = 3,
        recovery_timeout: float = 30.0,
        fallback_message: str = "🤖 AI is temporarily unavailable. Reconnecting..."
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.fallback_message = fallback_message
        
        # Protected state (requires lock for concurrent access)
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0.0
        self.state_lock = asyncio.Lock()  # Protect concurrent state access
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection.
        
        Args:
            func: Async function to call
            *args, **kwargs: Function arguments
            
        Returns:
            Function result OR fallback message if circuit is open
        """
        # Check if circuit should transition from OPEN -> HALF_OPEN (with lock)
        async with self.state_lock:
            if self.state == CircuitState.OPEN:
                if time.time() - self.last_failure_time >= self.recovery_timeout:
                    logger.info("Circuit breaker transitioning to HALF_OPEN (testing recovery)")
                    self.state = CircuitState.HALF_OPEN
                else:
                    # Circuit still open, return fallback
                    logger.warning("Circuit breaker OPEN - rejecting LLM call")
                    return self.fallback_message
        
        # Attempt the call
        try:
            result = await func(*args, **kwargs)
            
            # Success! Reset circuit (with lock)
            async with self.state_lock:
                # Only transition to CLOSED if we're in HALF_OPEN
                # Avoid closing a circuit that was just opened by a concurrent failure
                if self.state == CircuitState.HALF_OPEN:
                    logger.info("Circuit breaker recovered - transitioning to CLOSED")
                    self.state = CircuitState.CLOSED
                    self.failure_count = 0
                elif self.state == CircuitState.CLOSED:
                    # Already closed, just reset count
                    self.failure_count = 0
                else:
                    # Circuit was opened by concurrent failure, skip closing
                    logger.debug(f"Circuit state is {self.state}, skipping transition to CLOSED")
            
            return result
            
        except Exception as e:
            logger.error(f"Circuit breaker caught error: {str(e)}")
            
            # Update failure state (with lock)
            async with self.state_lock:
                self.failure_count += 1
                self.last_failure_time = time.time()
                
                # Should we open the circuit?
                if self.failure_count >= self.failure_threshold:
                    logger.warning(f"Circuit breaker OPENING after {self.failure_count} failures")
                    self.state = CircuitState.OPEN
            
            # Return fallback for now
            return self.fallback_message
