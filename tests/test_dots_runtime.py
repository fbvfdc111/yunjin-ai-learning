from __future__ import annotations

import sys
import threading
import time
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from yunjin_ai.dots_runtime import dots_request_slot


class DotsRuntimeTests(unittest.TestCase):
    def test_two_sessions_are_serialized_before_using_shared_api_key(self):
        first_entered = threading.Event()
        release_first = threading.Event()
        order: list[str] = []

        def first_request() -> None:
            with dots_request_slot():
                order.append("first-enter")
                first_entered.set()
                release_first.wait(timeout=2)
                order.append("first-leave")

        def second_request() -> None:
            with dots_request_slot():
                order.append("second-enter")

        first = threading.Thread(target=first_request)
        second = threading.Thread(target=second_request)
        first.start()
        self.assertTrue(first_entered.wait(timeout=1))
        second.start()
        time.sleep(0.05)
        self.assertEqual(order, ["first-enter"])
        release_first.set()
        first.join(timeout=2)
        second.join(timeout=2)

        self.assertFalse(first.is_alive())
        self.assertFalse(second.is_alive())
        self.assertEqual(order, ["first-enter", "first-leave", "second-enter"])


if __name__ == "__main__":
    unittest.main()
