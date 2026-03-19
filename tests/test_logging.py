from __future__ import annotations

import io
import json
import unittest

from polytest.engine.json_logging import JsonLogger


class JsonLoggerTests(unittest.TestCase):
    def test_stream_filter_only_prints_selected_events(self) -> None:
        stream = io.StringIO()
        logger = JsonLogger(stream=stream, stream_include_events={"opportunity"})

        logger.emit("feed_connecting", asset_count=10)
        logger.emit("opportunity", market_id="m1")

        lines = stream.getvalue().splitlines()
        self.assertEqual(len(lines), 1)
        self.assertEqual(json.loads(lines[0])["event"], "opportunity")


if __name__ == "__main__":
    unittest.main()
