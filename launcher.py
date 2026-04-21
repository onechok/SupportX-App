import multiprocessing
from supportx_app.app import run

if __name__ == "__main__":
    multiprocessing.set_start_method("spawn", force=True)
    raise SystemExit(run())
