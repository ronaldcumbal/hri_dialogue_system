from setuptools import find_packages, setup

package_name = 'woz_reception'

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
    maintainer='Ronald Cumbal',
    maintainer_email='ronald.cumbal.g@gmail.com',
    description='TODO: Package description',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'wizard_interface = woz_reception.wizard_interface:main',
            'furhat_bridge = woz_reception.furhat_bridge:main',
        ],
    },
)
