## Add or create your package
Clone your custom repository or generate a clean starter package:

```bash
ros2 package create --build-type ament_cmake my_custom_package
cd ..
```

## Build the workspace

```bash
# If using Pixi tasks
pixi run build

# Or manually within the environment
colcon build --symlink-install
```

## Source your package

```bash
source install/setup.bash
```