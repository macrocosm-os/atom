<picture>
    <source srcset="./assets/macrocosmos-white.png"  media="(prefers-color-scheme: dark)">
    <source srcset="./assets/macrocosmos-black.png"  media="(prefers-color-scheme: light)">
    <img src="macrocosmos-black.png">
</picture>

<div align="center">

# **Atom** <!-- omit in toc -->
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) 
</div>

<div align="center">
    <img src="./assets/atom.png" alt="atom">
</div>

Just as the atom forms the basis of all matter, this repository will serve as the core structure for every project that follows. Scalable, efficient, and adaptable, `atom` provides a framework that enables rapid development while ensuring stability and clarity for bittensor subnetworks. 

The current vision of this sdk is to provide us with a backbone that all of us can benefit from, such as:
1. Generic miner backbone 
2. Generic validator backbone 
3. Chain-related tools (writing, reading)
4. Organic Scoring tools

## Working with Atom
If you want to use it for your subnet development, you can install using: 
```
pip install git+https://github.com/macrocosm-os/atom.git@main
```

If you want to work in developer mode where changes to the codebase will become reflected in your subnet, without needing to re-pip install, use the following: 
```bash
git clone ... 
pip install -e PATH_TO_ATOM
```
The -e allows you to be in "edit" mode. 

## Poetry Installation
We use poetry to handle dependancies that are within `atom`. 

### MacOS 
```bash 
brew install python@3.11
bash install.sh
```

## Generating the S3_CONFIG Dictionary

The `S3_CONFIG` dictionary is used to configure access to an S3-compatible object storage service. It relies on environment variables for secure and flexible configuration. Below are the steps to set up and use the `S3_CONFIG` dictionary:

### 1. Required Environment Variables
The following environment variables need to be set in your system or application environment:
- `S3_REGION`: The AWS region or S3-compatible region where your bucket is located.
- `S3_ENDPOINT`: The endpoint URL for your S3-compatible service (e.g., `https://s3.amazonaws.com` for AWS S3).
- `S3_KEY`: Your S3 access key ID.
- `S3_SECRET`: Your S3 secret access key.


