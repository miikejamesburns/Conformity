# OCIO Configurations

This directory contains example OpenColorIO (OCIO) configuration files for use with Conformity.

## Included Configs

### simple_config.ocio

A basic OCIO configuration for testing and demonstration purposes.

**Features:**
- Scene-linear working space
- Common camera color spaces (RED, ARRI, Blackmagic)
- Standard display transforms (sRGB, Rec.709)
- Log encoding support (LogC)
- ACES color spaces (ACEScg, ACES2065-1)

**Color Spaces:**

| Name | Family | Description | Use Case |
|------|--------|-------------|----------|
| Linear | Linear | Scene-linear working space | Compositing, VFX work |
| ACEScg | ACES | ACES working space | ACES workflows |
| ACES2065-1 | ACES | ACES interchange | Archive, delivery |
| RedWideGamutRGB | Input/RED | RED camera native | RED footage |
| ARRI_LogC4 | Input/ARRI | ARRI LogC4 | ARRI footage |
| BMDFilm_Gen5 | Input/Blackmagic | Blackmagic Film | BRAW footage |
| CameraRec709 | Input/Generic | Generic Rec.709 | Standard video |
| sRGB | Display | sRGB display | Web, monitors |
| Rec709 | Display | Rec.709 video | Broadcast |
| LogC | Log | ARRI LogC | Grading, DI |
| Raw | Utility | No transform | Data, mattes |

## Usage in Conformity

### Loading a Config

1. **Via UI:**
   - Open Conformity
   - Go to "Color Management" tab or Color Space widget
   - Click "Load Config..."
   - Select `simple_config.ocio`

2. **Via Environment Variable:**
   ```bash
   export OCIO=/path/to/Conformity/config/ocio/simple_config.ocio
   python run.py
   ```

3. **Via Configuration File:**
   Edit `config/default_config.yaml`:
   ```yaml
   ocio_config_path: "config/ocio/simple_config.ocio"
   ```

### Setting Pipeline Defaults

After loading a config, set your pipeline defaults:

1. **Working Color Space:** `Linear` or `ACEScg`
2. **Default Input:** `CameraRec709` or camera-specific
3. **Display:** `sRGB`
4. **View:** `Standard`

### Auto-Detection Rules

Conformity can automatically assign color spaces based on file extensions:

| Extension | Suggested Color Space |
|-----------|----------------------|
| `.r3d` | RedWideGamutRGB |
| `.ari` | ARRI_LogC4 |
| `.braw` | BMDFilm_Gen5 |
| `.dng` | CameraRec709 |
| `.mov`, `.mp4` | CameraRec709 |

## Production Configs

For production use, we recommend:

1. **ACES Config:**
   Download from: https://github.com/AcademySoftwareFoundation/OpenColorIO-Config-ACES

2. **Studio Config:**
   Use your studio's standardized OCIO config

3. **Custom Config:**
   Create a custom config based on your specific camera and display requirements

## Creating Custom Configs

To create a custom OCIO config:

1. **Start with a template:**
   - Copy `simple_config.ocio`
   - Or use ACES config as base

2. **Add your camera color spaces:**
   ```yaml
   - !<ColorSpace>
     name: MyCamera_LogProfile
     family: Input/MyCamera
     description: My camera's log profile
     # ... transform definitions
   ```

3. **Define your display transforms:**
   ```yaml
   displays:
     MyDisplay:
       - !<View> {name: Standard, colorspace: sRGB}
       - !<View> {name: HDR, colorspace: ST2084}
   ```

4. **Test thoroughly:**
   - Validate in Conformity
   - Test with representative footage
   - Verify color accuracy

## Resources

- [OCIO Documentation](https://opencolorio.readthedocs.io/)
- [ACES Configs](https://github.com/AcademySoftwareFoundation/OpenColorIO-Config-ACES)
- [OCIO Config Examples](https://github.com/AcademySoftwareFoundation/OpenColorIO-Configs)

## Troubleshooting

### Config Won't Load

- Check YAML syntax
- Verify all referenced files exist
- Check OCIO version compatibility
- Use Conformity's "Validate" button

### Color Spaces Not Available

- Ensure color space names match exactly (case-sensitive)
- Check family assignments
- Verify transforms are defined

### Incorrect Colors

- Verify source color space is correct for your media
- Check display/view transform
- Confirm OCIO version matches config version

## Notes

- The simple config is intentionally simplified for demonstration
- Production workflows should use proper LUTs and transforms
- Always test color accuracy with known reference images
- Keep configs in version control
- Document any custom color spaces added
