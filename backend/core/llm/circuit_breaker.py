"""
Circuit Breaker Pattern for LLM Fault Tolerance

Prevents cascading failures when LLM service is down.
"""
import time
from enum import Enum
from typing import Callable, Any


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
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0.0
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection.
        
        Args:
            func: Async function to call
            *args, **kwargs: Function arguments
            
        Returns:
            Function result OR fallback message if circuit is open
        """
        # Check if circuit should transition from OPEN -> HALF_OPEN
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time >= self.recovery_timeout:
                print(f"🔄 Circuit breaker transitioning to HALF_OPEN (testing recovery)")
                self.state = CircuitState.HALF_OPEN
            else:
                # Circuit still open, return fallback
                print(f"⚠️ Circuit breaker OPEN - rejecting LLM call")
                return self.fallback_message
        
        # Attempt the call
        try:
            result = await func(*args, **kwargs)
            
            # Success! Reset circuit
            if self.state == CircuitState.HALF_OPEN:
                print(f"✅ Circuit breaker recovered - transitioning to CLOSED")
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            
            return result
            
        except Exception as e:
            print(f"❌ Circuit breaker caught error: {str(e)}")
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            # Should we open the circuit?
            if self.failure_count >= self.failure_threshold:
                print(f"🚨 Circuit breaker OPENING after {self.failure_count} failures")
                self.state = CircuitState.OPEN
            
            # Return fallback for now
            return self.fallback_message
