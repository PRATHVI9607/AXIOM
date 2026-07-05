# axiom.spec — PyInstaller build for a standalone AXIOM backend binary.
# Build:  pyinstaller packaging/axiom.spec   (from repo root)
# Output: dist/axiom(.exe) — the extension can spawn it via `axiom.backendCommand`.
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

hidden = (
    collect_submodules("uvicorn")
    + collect_submodules("axiom")
    + ["asyncpg", "aiosqlite", "sqlalchemy.dialects.sqlite", "sqlalchemy.dialects.postgresql"]
)

# Ship migration scripts, the GNN weights, and the eBPF program alongside the binary.
datas = [
    ("../alembic", "alembic"),
    ("../alembic.ini", "."),
    ("../axiom/models/gnn_v1.npz", "axiom/models"),
    ("../ebpf/syscall_tracer.bpf.c", "ebpf"),
] + collect_data_files("chromadb", include_py_files=False)

a = Analysis(
    ["axiom_entry.py"],
    pathex=[".."],
    binaries=[],
    datas=datas,
    hiddenimports=hidden,
    hookspath=[],
    runtime_hooks=[],
    excludes=["torch", "torch_geometric"],  # optional, huge; omit from the binary
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="axiom",
    console=True,
    upx=True,
    disable_windowed_traceback=False,
)
