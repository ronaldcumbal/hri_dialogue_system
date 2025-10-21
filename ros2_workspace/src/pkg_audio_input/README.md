## Installing Vosk

Download models from ([here](https://alphacephei.com/vosk/models)):

Place unzipped model in `../ros2_workspace/src/pkg_audio_input/models'`

## Working with Google STT

### Set Credentials
First, Authenticate to Speech-to-Text with this [tutorial](https://cloud.google.com/speech-to-text/docs/authentication#client-libs).

Then Set up ADC for a local development environment with this [tutorial](https://cloud.google.com/docs/authentication/set-up-adc-local-dev-environment):


## Installing sounddevice

Recommended steps to install sounddevice with portAudio ([source](https://github.com/Upsonic/Upsonic/issues/22)):

### Ubuntu/Debian:

- Update the package list: 
`sudo apt update`
- Install the PortAudio library and development files: 
`sudo apt install portaudio19-dev`
- Install sounddevice Python package:
`pip install sounddevice`

### macOS

- Install PortAudio using Homebrew:
`brew install portaudio`
- Install sounddevice Python package:
`pip install sounddevice`

## Using Google Cloud Services

### Install the gcloud CLI locally
Follow this [tutorial](https://cloud.google.com/sdk/docs/install#deb)

### Set Aplication Default Credentials
Follow this [tutorial](https://cloud.google.com/docs/authentication/set-up-adc-local-dev-environment)

## Getting USB camera feed

Follow the installation tutorial [here](https://github.com/ros-drivers/usb_cam)

`sudo apt-get install ros-humble-usb-cam`