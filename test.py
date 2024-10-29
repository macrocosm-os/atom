from atom.logging.github import GithubHandler

handler = GithubHandler(repo_url="https://github.com/macrocosm-os/folding")
handler.pull()
