from pathlib import Path
import shutil
def clear_tmp():
    tmp_dir = Path("tmp")
    if not tmp_dir.exists():
        return  # Nada para limpar

    for item in tmp_dir.iterdir():
        if item.name == ".keep":
            continue  # Pula o .keep
        if item.is_dir():
            shutil.rmtree(item)
        else:
            item.unlink()

    print("[DEBUG] Pasta tmp/ limpa (mantido .keep).", flush=True)