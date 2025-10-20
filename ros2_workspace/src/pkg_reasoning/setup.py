from setuptools import find_packages, setup

package_name = 'pkg_reasoning'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools', 'pkg_commons'],
    zip_safe=True,
    maintainer='Ronald Cumbal',
    maintainer_email='ronald.cumbal.g@gmail.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'dialogue_manager = pkg_reasoning.dialogue_manager:main',
            'llm_prompter = pkg_reasoning.llm_prompter:main'
        ],
    },
)
