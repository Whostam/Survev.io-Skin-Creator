import unittest

from skin_creator.preview import PreviewLayout, body_frame_from_layout


class BodyFrameFromLayoutTests(unittest.TestCase):
    def test_uses_defaults_when_overrides_missing(self) -> None:
        layout = PreviewLayout()
        frame = body_frame_from_layout(layout)

        expected_left = (layout.stage_width - layout.body_size) // 2 + layout.body_left_offset

        self.assertEqual(frame.width, layout.body_size)
        self.assertEqual(frame.height, layout.body_size)
        self.assertEqual(frame.left, expected_left)
        self.assertEqual(frame.top, layout.body_top)
        self.assertEqual(frame.rotation, layout.body_rotation)

    def test_honors_explicit_body_dimensions(self) -> None:
        layout = PreviewLayout(
            stage_width=360,
            body_width=200,
            body_height=180,
            body_left=50,
            body_top=120,
            body_rotation=15,
        )
        frame = body_frame_from_layout(layout)

        self.assertEqual(frame.width, 200)
        self.assertEqual(frame.height, 180)
        self.assertEqual(frame.left, 50)
        self.assertEqual(frame.top, 120)
        self.assertEqual(frame.rotation, 15.0)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
