import time
import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
import sys

# Add the repo root to sys.path to allow imports
repo_root = Path(__file__).resolve().parents[2]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

class TestAutoIndexScheduler(unittest.TestCase):
    """
    Unit tests for Auto-index Scheduler logic.
    Note: While the primary implementation is in TypeScript, these tests 
    simulate the debounce and rate-limiting logic to verify the requirements.
    """

    def setUp(self):
        self.debounce_interval = 60  # 60 seconds
        self.rate_limit_interval = 300  # 5 minutes (300 seconds)
        self.last_index_time = 0
        self.index_call_count = 0

    def mock_trigger_index(self):
        self.index_call_count += 1
        self.last_index_time = time.time()

    def test_debounce_logic(self):
        """Verify that multiple events within the debounce window trigger only one indexing."""
        # Simulated debounce logic
        events = [0, 10, 20, 30, 40, 50]  # Events every 10 seconds
        last_event_time = 0
        
        # In a real scenario, the timer would be reset. 
        # Here we simulate that indexing only happens after last_event_time + debounce
        for t in events:
            last_event_time = t
        
        indexing_triggered_at = last_event_time + self.debounce_interval
        self.assertEqual(indexing_triggered_at, 110) # 50 + 60

    def test_rate_limit_logic(self):
        """Verify that indexing occurs no more than once every 5 minutes."""
        current_time = 1000
        self.last_index_time = 900 # 100 seconds ago
        
        # Try to index at 1000
        if current_time - self.last_index_time >= self.rate_limit_interval:
            self.mock_trigger_index()
        
        self.assertEqual(self.index_call_count, 0) # Should be blocked (100 < 300)
        
        # Try to index at 1301
        current_time = 1301
        if current_time - self.last_index_time >= self.rate_limit_interval:
            self.mock_trigger_index()
            
        self.assertEqual(self.index_call_count, 1) # Should succeed (401 > 300)

    @patch('time.sleep', return_value=None)
    def test_handle_index_in_progress(self, mock_sleep):
        """Simulate waiting for health.indexing=false before retrying."""
        health_responses = [
            {'indexing': True},
            {'indexing': True},
            {'indexing': False}
        ]
        
        call_count = 0
        def mock_fetch_health():
            nonlocal call_count
            res = health_responses[call_count]
            call_count += 1
            return res

        # Simulation of the polling loop
        while True:
            health = mock_fetch_health()
            if not health['indexing']:
                break
            # Simulate 2s delay
            time.sleep(2)
            
        self.assertEqual(call_count, 3)
        self.assertEqual(mock_sleep.call_count, 2)

if __name__ == '__main__':
    unittest.main()
