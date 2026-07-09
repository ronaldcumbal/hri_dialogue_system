# Interactive System

This repo contains basic interactive components to use in human-robot interactions. 

The system is desingned to work within the ROS 2 (Humble) framework. The installation tutorial can be found [here](https://docs.ros.org/en/humble/Installation.html).

## Robostack
The system can also work within a virtual environment using Robostack. Follow this [link](https://robostack.github.io/GettingStarted.html) for instruction. 

## Using Pip to install packages.
Always prefer Conda Packages when available ([Repository](https://anaconda.org/)). If **pip** is required, follow this steps:

### Method 1: Using an environment.yml File (Cleanest)

Declare pip dependencies directly in your `environment.yml` configuration file. *Micromamba will resolve its own packages first, then automatically invoke pip for the remaining libraries.*

```yaml
yamlname: my_env
channels:
  - conda-forge
dependencies:
  - python=3.11
  - numpy
  - pip
  - pip:
    - name-of-pip-only-package
```

Run the creation command:

```bash
micromamba create -f environment.yml
```

### Method 2: Command Line (Manual)

If you need to quickly add a pip package to an existing active environment, install pip via micromamba first:
```bash
# 1. Install pip using micromamba
micromamba install pip

# 2. Install your PyPI package
pip install name-of-pip-only-package
```

### Export manually-installed packages:
```bash
micromamba env export --from-history > environment.yml
```

## Getting USB camera feed

Follow the installation tutorial [here](https://github.com/ros-drivers/usb_cam)

```bash
sudo apt-get install ros-humble-usb-cam
```

## hri_msg and hri_face_detection

In addition to the packages in requirements.txt, you might need the following:

```bash
pip install transforms3d
pip install scipy
sudo apt-get install ros-humble-tf-transformations
```

## Audio Input Package

The **pkg_audio_input** package integrates the components to read and process audio input signals.

## Visual Input Package

The **pkg_visual_input** package integrates the components to read and process visual input signals

## Sensor Input Package

The **pkg_sensor_input** package integrates the components to read and process input signals from buttons/keys and sensors in general.

## Reasoning Package

The **pkg_reasoning** package integrates different models to preform computations from input signals and generate robot actions. These are mostly large models.

## Embodiment Package

The **pgk_embodiment** package integrates different component to connect a robot.

## Output Package

The **pkg_output** package integrates different component that make the robot perform different actions.

## Interface Package

The **pkg_interfaces** package integrates component outside of the robot embodiment, for example, GIUs, tablets, lights, etc.

## Additional modules

The following are packages that can be used as already built funtionalities:

- hri_face_detect
- hri_msgs
- usb_cam