"""Generate sample LUT files for testing."""

import numpy as np
from pathlib import Path

# Create test data directory
lut_dir = Path(__file__).parent / "test_data" / "luts"
lut_dir.mkdir(parents=True, exist_ok=True)


def generate_identity_3d_cube(size=33):
    """Generate a 3D identity LUT in CUBE format."""
    output_path = lut_dir / f"identity_{size}.cube"

    with open(output_path, 'w') as f:
        f.write(f'TITLE "Identity {size}x{size}x{size}"\n')
        f.write("DOMAIN_MIN 0.0 0.0 0.0\n")
        f.write("DOMAIN_MAX 1.0 1.0 1.0\n")
        f.write(f"LUT_3D_SIZE {size}\n")
        f.write("\n")
        f.write("# Identity LUT - passes through all colors unchanged\n")
        f.write("# Generated for Conformity testing\n")
        f.write("\n")

        for b in range(size):
            for g in range(size):
                for r in range(size):
                    r_val = r / (size - 1)
                    g_val = g / (size - 1)
                    b_val = b / (size - 1)
                    f.write(f"{r_val:.6f} {g_val:.6f} {b_val:.6f}\n")

    print(f"Generated: {output_path}")


def generate_identity_1d_cube(size=1024):
    """Generate a 1D identity LUT in CUBE format."""
    output_path = lut_dir / f"identity_1d_{size}.cube"

    with open(output_path, 'w') as f:
        f.write(f'TITLE "Identity 1D {size}"\n')
        f.write("DOMAIN_MIN 0.0 0.0 0.0\n")
        f.write("DOMAIN_MAX 1.0 1.0 1.0\n")
        f.write(f"LUT_1D_SIZE {size}\n")
        f.write("\n")
        f.write("# 1D Identity LUT\n")
        f.write("\n")

        for i in range(size):
            val = i / (size - 1)
            f.write(f"{val:.6f} {val:.6f} {val:.6f}\n")

    print(f"Generated: {output_path}")


def generate_invert_3d_cube(size=17):
    """Generate a simple invert LUT."""
    output_path = lut_dir / f"invert_{size}.cube"

    with open(output_path, 'w') as f:
        f.write(f'TITLE "Invert {size}x{size}x{size}"\n')
        f.write("DOMAIN_MIN 0.0 0.0 0.0\n")
        f.write("DOMAIN_MAX 1.0 1.0 1.0\n")
        f.write(f"LUT_3D_SIZE {size}\n")
        f.write("\n")
        f.write("# Inverts all colors (1 - value)\n")
        f.write("\n")

        for b in range(size):
            for g in range(size):
                for r in range(size):
                    r_val = 1.0 - (r / (size - 1))
                    g_val = 1.0 - (g / (size - 1))
                    b_val = 1.0 - (b / (size - 1))
                    f.write(f"{r_val:.6f} {g_val:.6f} {b_val:.6f}\n")

    print(f"Generated: {output_path}")


def generate_sepia_3d_cube(size=17):
    """Generate a sepia tone LUT."""
    output_path = lut_dir / f"sepia_{size}.cube"

    with open(output_path, 'w') as f:
        f.write(f'TITLE "Sepia {size}x{size}x{size}"\n')
        f.write("DOMAIN_MIN 0.0 0.0 0.0\n")
        f.write("DOMAIN_MAX 1.0 1.0 1.0\n")
        f.write(f"LUT_3D_SIZE {size}\n")
        f.write("\n")
        f.write("# Sepia tone effect\n")
        f.write("\n")

        for b in range(size):
            for g in range(size):
                for r in range(size):
                    # Original RGB
                    r_in = r / (size - 1)
                    g_in = g / (size - 1)
                    b_in = b / (size - 1)

                    # Sepia formula
                    r_out = min(1.0, 0.393 * r_in + 0.769 * g_in + 0.189 * b_in)
                    g_out = min(1.0, 0.349 * r_in + 0.686 * g_in + 0.168 * b_in)
                    b_out = min(1.0, 0.272 * r_in + 0.534 * g_in + 0.131 * b_in)

                    f.write(f"{r_out:.6f} {g_out:.6f} {b_out:.6f}\n")

    print(f"Generated: {output_path}")


def generate_contrast_1d_cube(contrast=1.2, size=256):
    """Generate a contrast adjustment 1D LUT."""
    output_path = lut_dir / f"contrast_{contrast}_{size}.cube"

    with open(output_path, 'w') as f:
        f.write(f'TITLE "Contrast {contrast} 1D"\n')
        f.write("DOMAIN_MIN 0.0 0.0 0.0\n")
        f.write("DOMAIN_MAX 1.0 1.0 1.0\n")
        f.write(f"LUT_1D_SIZE {size}\n")
        f.write("\n")
        f.write(f"# Contrast adjustment: {contrast}\n")
        f.write("\n")

        for i in range(size):
            val = i / (size - 1)
            # Contrast formula: (val - 0.5) * contrast + 0.5
            adjusted = np.clip((val - 0.5) * contrast + 0.5, 0.0, 1.0)
            f.write(f"{adjusted:.6f} {adjusted:.6f} {adjusted:.6f}\n")

    print(f"Generated: {output_path}")


if __name__ == "__main__":
    print("Generating test LUT files...")

    # Generate various test LUTs
    generate_identity_3d_cube(33)  # Standard 33x33x33 identity
    generate_identity_3d_cube(17)  # Smaller 17x17x17 identity
    generate_identity_1d_cube(1024)  # 1D identity
    generate_identity_1d_cube(256)  # Smaller 1D identity
    generate_invert_3d_cube(17)  # Color inversion
    generate_sepia_3d_cube(17)  # Sepia tone
    generate_contrast_1d_cube(1.2, 256)  # Contrast boost
    generate_contrast_1d_cube(0.8, 256)  # Contrast reduce

    print("\nDone! Generated test LUTs in:", lut_dir)
