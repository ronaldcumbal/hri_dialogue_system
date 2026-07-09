from setuptools import find_packages, setup

package_name = 'pkg_audio_input'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='ronald',
    maintainer_email='ronald.cumbal.g@gmail.com',
    description='TODO: Package description',
    license='TODO: License declaration',
#    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'stt_whisper_server = pkg_audio_input.stt_whisper_server:main',
            'stt_whisper_client = pkg_audio_input.stt_whisper_client:main',
            'stt_speechmatics = pkg_audio_input.stt_speechmatics:main',
        ],
    },
)
