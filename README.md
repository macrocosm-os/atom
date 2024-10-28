# Atom
`Atom` is the foundation upon which we will build the future.

Just as the atom forms the basis of all matter, this repository will serve as the core structure for every project that follows. Scalable, efficient, and adaptable, `Atom` provides a framework that enables rapid development while ensuring stability and clarity for bittensor subnetworks.

The current vision of this sdk is to provide us with a backbone that all of us can benefit from, such as:
1. Generic miner backbone 
2. Generic validator backbone 
3. Chain-related tools (writing, reading)
4. ect... 

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
