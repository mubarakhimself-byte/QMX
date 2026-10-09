from pathlib import Path

from macro_bias import create_server

if __name__ == "__main__":
    create_server(Path.cwd()).run(transport="stdio", show_banner=False)
