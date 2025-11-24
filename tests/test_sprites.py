from skin_creator.sprites import build_part_svg, svg_backpack


def base_cfg():
    return dict(
        style="Solid",
        primary="#111111",
        secondary="#111111",
        extra="#111111",
        angle=0,
        gap=10,
        opacity=1.0,
        size=10,
    )


def test_glow_outline_supports_custom_color_and_thickness():
    svg = build_part_svg(
        base_cfg(),
        svg_backpack,
        "#5522aa",
        10,
        "Glow",
        glow_color="#ff2200",
        glow_size=18,
    )
    assert "backpack-glow" in svg
    assert "flood-color=\"#ff2200\"" in svg
    assert "filter=\"url(#backpack-glow)\"" in svg


def test_gradient_outline_uses_linear_gradient():
    svg = build_part_svg(base_cfg(), svg_backpack, "#5522aa", 10, "Gradient")
    assert "backpack-stroke-grad" in svg
    assert "stroke=\"url(#backpack-stroke-grad)\"" in svg


def test_dashed_outline_sets_dasharray():
    svg = build_part_svg(base_cfg(), svg_backpack, "#5522aa", 10, "Dashed")
    assert "stroke-dasharray" in svg


def test_double_outline_renders_two_strokes():
    svg = build_part_svg(base_cfg(), svg_backpack, "#5522aa", 10, "Double Stroke")
    assert svg.count("stroke=\"") >= 2
