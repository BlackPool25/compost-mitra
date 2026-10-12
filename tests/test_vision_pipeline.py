"""Unit tests for the Lightweight Vision Ingestion & Bulk Density Estimator.

Verifies:
1. Image loading from PIL Image, bytes, and file paths.
2. Literature bulk density lookup and mass conversion accuracy.
3. Volumetric scaling with container capacity.
4. Colorimetric segmentation for green scraps, citrus peels, and coffee grounds.
5. End-to-end chaining from vision mass estimation to convex recipe optimization.
"""

from __future__ import annotations

import io
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from scripts.convex_optimizer import balance_available_wastes
from scripts.vision_pipeline import (
    LITERATURE_BULK_DENSITIES,
    estimate_waste_from_image,
)


@pytest.fixture
def green_vegetable_image() -> Image.Image:
    # Pure green image simulating vegetable peelings
    arr = np.zeros((120, 120, 3), dtype=np.uint8)
    arr[:, :, 1] = 220
    return Image.fromarray(arr)


@pytest.fixture
def orange_citrus_image() -> Image.Image:
    # Bright orange image simulating citrus peels
    arr = np.zeros((120, 120, 3), dtype=np.uint8)
    arr[:, :, 0] = 255  # Red
    arr[:, :, 1] = 140  # Green -> Orange in RGB
    return Image.fromarray(arr)


@pytest.fixture
def dark_coffee_image() -> Image.Image:
    # Dark brown image simulating spent coffee grounds
    arr = np.zeros((120, 120, 3), dtype=np.uint8)
    arr[:, :, 0] = 45
    arr[:, :, 1] = 25
    arr[:, :, 2] = 15
    return Image.fromarray(arr)


class TestVisionPipeline:
    """Test suite for estimate_waste_from_image and bulk density conversions."""

    def test_literature_density_table_validity(self):
        assert len(LITERATURE_BULK_DENSITIES) >= 15
        for ing_id, rho in LITERATURE_BULK_DENSITIES.items():
            assert 40.0 <= rho <= 1000.0, f"Density for {ing_id} outside realistic envelope"

    def test_green_vegetable_detection(self, green_vegetable_image):
        res = estimate_waste_from_image(green_vegetable_image, container_volume_liters=5.0)

        assert res.total_estimated_mass_kg > 0.5
        assert res.total_volume_liters > 1.0
        assert "vegetable_scraps" in res.masses_by_ingredient
        assert res.items[0].confidence > 0.60
        assert res.items[0].bulk_density_kg_m3 == 550.0

    def test_orange_citrus_detection(self, orange_citrus_image):
        res = estimate_waste_from_image(orange_citrus_image, container_volume_liters=10.0)

        assert res.total_estimated_mass_kg > 0.5
        assert "citrus_peels" in res.masses_by_ingredient
        assert res.items[0].bulk_density_kg_m3 == 480.0

    def test_coffee_detection(self, dark_coffee_image):
        res = estimate_waste_from_image(dark_coffee_image, container_volume_liters=4.0)

        assert res.total_estimated_mass_kg > 0.2
        assert "coffee_grounds" in res.masses_by_ingredient
        assert res.items[0].bulk_density_kg_m3 == 350.0

    def test_bytes_input_handling(self, green_vegetable_image):
        buf = io.BytesIO()
        green_vegetable_image.save(buf, format="PNG")
        raw_bytes = buf.getvalue()

        res = estimate_waste_from_image(raw_bytes, container_volume_liters=5.0)
        assert res.total_estimated_mass_kg > 0.5

    def test_volume_scaling_proportionality(self, green_vegetable_image):
        res_5l = estimate_waste_from_image(green_vegetable_image, container_volume_liters=5.0)
        res_10l = estimate_waste_from_image(green_vegetable_image, container_volume_liters=10.0)

        assert res_10l.total_estimated_mass_kg == pytest.approx(
            res_5l.total_estimated_mass_kg * 2.0, rel=1e-3
        )

    def test_nonexistent_file_raises_not_found(self):
        with pytest.raises(FileNotFoundError):
            estimate_waste_from_image("/nonexistent/path/to/waste.jpg")

    def test_invalid_type_raises_value_error(self):
        with pytest.raises(ValueError, match="Unsupported image input type"):
            estimate_waste_from_image(12345)

    def test_end_to_end_vision_to_optimizer(self, green_vegetable_image):
        # Image -> Estimated Masses -> Convex Optimizer
        vision_res = estimate_waste_from_image(green_vegetable_image, container_volume_liters=6.0)
        opt_res = balance_available_wastes(vision_res.masses_by_ingredient)

        assert opt_res.success is True
        assert opt_res.blend_properties["heuristic_grade"] in ("GRADE_A", "GRADE_B")
        assert 25.0 <= opt_res.blend_properties["cn"] <= 35.0
