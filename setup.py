from setuptools import find_packages, setup

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    name="atom",
    version="0.1.0",
    packages=find_packages(),
    install_requires=requirements,
    author="macrocosmos",
    author_email="brian@macrocosmos.ai",
    description="Basic building blocks for all bittensor subnets",
    url="https://github.com/macrocosm-os/atom",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.9",
)
