# Test LUT Files

This directory contains sample LUT files for testing the Conformity LUT management system.

## Files

### Identity LUTs

**identity_33.cube**
- Format: 3D CUBE
- Size: 33x33x33
- Description: Standard identity LUT that passes through all colors unchanged
- Use: Testing basic LUT loading and application

**identity_17.cube**
- Format: 3D CUBE
- Size: 17x17x17
- Description: Smaller identity LUT for faster testing
- Use: Testing with different LUT sizes

**identity_1d_1024.cube**
- Format: 1D CUBE
- Size: 1024 points
- Description: 1D identity LUT
- Use: Testing 1D LUT functionality

**identity_1d_256.cube**
- Format: 1D CUBE
- Size: 256 points
- Description: Smaller 1D identity LUT
- Use: Testing 1D LUT with different sizes

### Effect LUTs

**invert_17.cube**
- Format: 3D CUBE
- Size: 17x17x17
- Description: Inverts all colors (output = 1 - input)
- Use: Testing color transformation

**sepia_17.cube**
- Format: 3D CUBE
- Size: 17x17x17
- Description: Applies sepia tone effect
- Use: Testing creative color grading

**contrast_1.2_256.cube**
- Format: 1D CUBE
- Size: 256 points
- Description: Increases contrast by 20%
- Use: Testing 1D contrast adjustments

**contrast_0.8_256.cube**
- Format: 1D CUBE
- Size: 256 points
- Description: Decreases contrast by 20%
- Use: Testing 1D contrast reduction

## Usage

These LUT files are used by `test_lut_loader.py` and `test_lut_manager.py` to verify:
- LUT parsing accuracy (CUBE format)
- 1D and 3D LUT support
- Data integrity and interpolation
- LUT application to RGB values
- Library management
- Metadata handling

## Generation

All LUT files are generated programmatically by `tests/generate_test_luts.py`. To regenerate:

```bash
python tests/generate_test_luts.py
```

## Format Reference

### CUBE Format

```
TITLE "LUT Name"
DOMAIN_MIN 0.0 0.0 0.0
DOMAIN_MAX 1.0 1.0 1.0
LUT_3D_SIZE 33

# Comments start with #

# RGB data (one line per point)
0.000000 0.000000 0.000000
0.031250 0.000000 0.000000
...
```

For 1D LUTs, use `LUT_1D_SIZE` instead of `LUT_3D_SIZE`.

## Testing

To test with these LUTs:

```python
from conformity.lut_manager import LUTLoader

loader = LUTLoader()
lut = loader.load("tests/test_data/luts/identity_33.cube")

# Apply to RGB values
import numpy as np
rgb = np.array([[0.5, 0.3, 0.8]])
result = lut.apply(rgb)
```
