# From https://github.com/ros-drivers/usb_cam/blob/main/launch/camera_config.py

from pathlib import Path
from typing import List, Optional

from ament_index_python.packages import get_package_share_directory
from pydantic import BaseModel, model_validator, field_validator

CAM_CONFIG_DIR = get_package_share_directory('pkg_launch')

class CameraConfig(BaseModel):
    name: str = 'camera1'
    param_path: Path = None
    remappings: Optional[List] = None
    namespace: Optional[str] = None

    def __init__(self, filename: str = 'params_1.yaml', **data):
        if 'param_path' not in data:
            # Set default param_path if not provided
            data['param_path'] = Path(CAM_CONFIG_DIR, 'config', filename)
        super().__init__(**data)


    @field_validator('param_path')
    @classmethod
    def validate_param_path(cls, value: Path) -> Path:
        if value and not value.exists():
            raise FileNotFoundError(f'Could not find parameter file: {value}')
        return value

    @model_validator(mode='after')
    def validate_model(self) -> 'CameraConfig':
        if self.name and not self.remappings:
            # Automatically set remappings if name is set
            self.remappings = [
                ('image_raw', f'{self.name}/image_raw'),
                ('image_raw/compressed', f'{self.name}/image_compressed'),
                ('image_raw/compressedDepth', f'{self.name}/compressedDepth'),
                ('image_raw/theora', f'{self.name}/image_raw/theora'),
                ('camera_info', f'{self.name}/camera_info'),
            ]
        return self