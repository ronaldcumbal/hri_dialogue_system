# Interactive System

This repo contains basic interactive components to use in human-robot interactions. 

### Requirements

The system is desingned to work within the ROS 2 (Humble) framework. The installation tutorial can be found in this [link](https://docs.ros.org/en/humble/Installation.html).

## Wizard-of-Oz Package

The **woz_reception** package is design to allow a person to control the robot's speech and head gestures. Currently this is limited to a predetermined set of utterances. A simple interface indicates which keys should be pressed to send individual utterances to be spoken by the robot. 

### Compile

`colcon build --packages-select woz_reception`

### Run

`ros2 run woz_reception wizard_interface`

## Perception Package

The **robot_perception** package integrates different components to read and process input signals, including vision, audio (speech), buttons/keys and sensors in general.

## Reasoning Package

The **robot_reasoning** package integrates different models to preform computations and generate robot actions. These are mostly large models.

## Reaction Package

The **robot_react** package integrates different component that make the robot perform different actions.
