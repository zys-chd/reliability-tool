"""
FT 文件缓存系统。

三层缓存：
1. 内存 LRU — 同一会话内重复打开同一文件
2. SQLite 索引 — 记录文件路径、大小、修改时间、列信息
3. Pickle 文件 — 存储解析后的 DataFrame 和元数据

用法：
    from core.ft_cache import ft_cache
    ft_cache.get(file_path)       # 返回 FTData 或 None
    ft_cache.put(file_path, ft)   # 存储
"""
import logging
import os
import pickle
import platform
import sqlite3
import sys
import time
from collections import OrderedDict
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


def _resolve_program_dir() -> Path:
    """返回程序运行目录。

    打包后（PyInstaller）→ exe 所在目录
    普通 Python 运行 → 项目根目录（core/..）
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    # 本项目根目录：ft_cache.py 在 core/ 下
    return Path(__file__).parent.parent


def _resolve_cache_path(path_str: str) -> Path:
    """解析缓存路径，支持 %PROGRAM_DIR% 宏。

    >>> _resolve_cache_path("%PROGRAM_DIR%/cache")
    PosixPath('/path/to/project/cache')
    """
    resolved = path_str.replace("%PROGRAM_DIR%", str(_resolve_program_dir()))
    return Path(resolved)


CACHE_DIR_DEFAULT = _resolve_cache_path("%PROGRAM_DIR%/cache")
MEMORY_CACHE_MAX = 100  # LRU max entries


class FTCache:
    """三层缓存：内存 LRU → SQLite → Pickle 文件。"""

    def __init__(self, cache_dir: str | Path | None = None):
        self._cache_dir = Path(cache_dir) if cache_dir else CACHE_DIR_DEFAULT
        self._pickle_dir = self._cache_dir / "data"
        self._db_path = self._cache_dir / "index.db"

        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._pickle_dir.mkdir(parents=True, exist_ok=True)

        self._memory: OrderedDict[str, dict] = OrderedDict()
        self._max_memory = MEMORY_CACHE_MAX

        self._init_db()

    # ── SQLite ──────────────────────────────────────────────────

    def _init_db(self):
        with self._connect() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS file_cache (
                    file_path       TEXT PRIMARY KEY,
                    file_size       INTEGER NOT NULL,
                    file_mtime      REAL NOT NULL,
                    signature_id    TEXT,
                    test_columns    TEXT,
                    meta_columns    TEXT,
                    row_count       INTEGER,
                    col_count       INTEGER,
                    pickle_path     TEXT,
                    cached_at       REAL NOT NULL,
                    access_count    INTEGER DEFAULT 0
                );
                CREATE INDEX IF NOT EXISTS idx_file_cache_path
                    ON file_cache(file_path);
            """)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self._db_path))
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=OFF")
        return conn

    # ── 文件 hash / 状态 ───────────────────────────────────────

    @staticmethod
    def _file_stat(path: str) -> tuple[int, float]:
        """返回 (file_size, file_mtime)。"""
        st = os.stat(path)
        return st.st_size, st.st_mtime

    # ── 公共 API ────────────────────────────────────────────────

    def get(self, file_path: str) -> Optional[dict]:
        """从缓存获取 FTData 的内部状态 dict。

        返回包含 '_df', '_units', '_lower_limits', '_higher_limits',
        '_meta_header', '_test_header', '_fmt' 的 dict，
        或 None。
        """
        path = str(Path(file_path).resolve())

        # 1. 内存缓存
        entry = self._memory.get(path)
        if entry is not None:
            # 验证文件是否变化
            try:
                cur_size, cur_mtime = self._file_stat(path)
                if cur_size == entry.get("_file_size") and cur_mtime == entry.get("_file_mtime"):
                    self._memory.move_to_end(path)
                    logger.debug(f"内存缓存命中: {path}")
                    return entry["state"]
            except OSError:
                pass

        # 2. SQLite 缓存
        try:
            cur_size, cur_mtime = self._file_stat(path)
        except OSError:
            return None

        row = None
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM file_cache WHERE file_path = ?",
                (path,)
            ).fetchone()

        if row and row[1] == cur_size and abs(row[2] - cur_mtime) < 0.001:
            pickle_path = row[8]
            if pickle_path and Path(pickle_path).exists():
                try:
                    with open(pickle_path, "rb") as f:
                        state = pickle.load(f)
                    # 更新内存缓存
                    self._put_memory(path, state, cur_size, cur_mtime)
                    # 更新访问计数
                    with self._connect() as conn:
                        conn.execute(
                            "UPDATE file_cache SET access_count = access_count + 1 WHERE file_path = ?",
                            (path,)
                        )
                    logger.debug(f"SQLite 缓存命中: {path}")
                    return state
                except Exception as e:
                    logger.warning(f"读取缓存文件失败: {pickle_path} - {e}")

        return None

    def put(self, file_path: str, state: dict):
        """将 FTData 内部状态存入缓存。"""
        path = str(Path(file_path).resolve())

        try:
            cur_size, cur_mtime = self._file_stat(path)
        except OSError:
            return

        # Pickle 文件名 = 路径 hash
        pickle_name = f"{abs(hash(path)):016x}.pkl"
        pickle_path = self._pickle_dir / pickle_name

        # 存 pickle
        try:
            with open(pickle_path, "wb") as f:
                pickle.dump(state, f, protocol=pickle.HIGHEST_PROTOCOL)
        except Exception as e:
            logger.warning(f"写入缓存文件失败: {pickle_path} - {e}")
            return

        # 提取元数据
        sig_id = ""
        test_cols = ""
        meta_cols = ""
        row_count = 0
        col_count = 0
        if "_fmt" in state and state["_fmt"]:
            sig = state["_fmt"].get("sig", {})
            sig_id = sig.get("format_id", "")
        if "_test_header" in state:
            test_cols = ",".join(state["_test_header"])
            col_count = len(state["_test_header"])
        if "_meta_header" in state:
            meta_cols = ",".join(state["_meta_header"])
        if "_df" in state and state["_df"] is not None:
            # 如果 DF 包含 3 行 meta，减掉；否则直接用 len
            df_len = len(state["_df"])
            row_count = df_len - 3 if df_len > 3 else df_len
            if row_count < 0:
                row_count = 0

        # 写 SQLite
        with self._connect() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO file_cache
                    (file_path, file_size, file_mtime, signature_id,
                     test_columns, meta_columns, row_count, col_count,
                     pickle_path, cached_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                path, cur_size, cur_mtime, sig_id,
                test_cols, meta_cols, row_count, col_count,
                str(pickle_path), time.time(),
            ))

        # 内存缓存
        self._put_memory(path, state, cur_size, cur_mtime)

        logger.debug(f"已缓存: {path} ({row_count} rows, {col_count} cols)")

    def invalidate(self, file_path: str):
        """删除指定文件的缓存条目。"""
        path = str(Path(file_path).resolve())

        # 从内存删除
        self._memory.pop(path, None)

        # 从 SQLite 读取 pickle 路径再删除
        with self._connect() as conn:
            row = conn.execute(
                "SELECT pickle_path FROM file_cache WHERE file_path = ?",
                (path,)
            ).fetchone()
            conn.execute("DELETE FROM file_cache WHERE file_path = ?", (path,))

        if row and row[0]:
            try:
                Path(row[0]).unlink(missing_ok=True)
            except Exception:
                pass

        logger.debug(f"已清除缓存: {path}")

    def get_meta(self, file_path: str) -> Optional[dict]:
        """快速获取文件元数据（不加载 DataFrame）。"""
        path = str(Path(file_path).resolve())

        # 先看内存
        entry = self._memory.get(path)
        if entry is not None:
            try:
                cur_size, cur_mtime = self._file_stat(path)
                if cur_size == entry.get("_file_size") and cur_mtime == entry.get("_file_mtime"):
                    return self._entry_to_meta(entry)
            except OSError:
                pass

        # 再看 SQLite
        try:
            cur_size, cur_mtime = self._file_stat(path)
        except OSError:
            return None

        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM file_cache WHERE file_path = ?",
                (path,)
            ).fetchone()

        if row and row[1] == cur_size and abs(row[2] - cur_mtime) < 0.001:
            return {
                "file_path": row[0],
                "file_size": row[1],
                "file_mtime": row[2],
                "signature_id": row[3] or "",
                "test_columns": (row[4] or "").split(",") if row[4] else [],
                "meta_columns": (row[5] or "").split(",") if row[5] else [],
                "row_count": row[6] or 0,
                "col_count": row[7] or 0,
                "cached_at": row[9],
                "access_count": row[10] or 0,
            }
        return None

    def search_by_columns(self, column_keyword: str) -> list[dict]:
        """查找包含某测试列的所有缓存文件。"""
        results = []
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT file_path, test_columns, row_count, col_count, signature_id "
                "FROM file_cache WHERE test_columns LIKE ?",
                (f"%{column_keyword}%",)
            ).fetchall()
        for r in rows:
            results.append({
                "file_path": r[0],
                "test_columns": (r[1] or "").split(",") if r[1] else [],
                "row_count": r[2] or 0,
                "col_count": r[3] or 0,
                "signature_id": r[4] or "",
            })
        return results

    def clear_all(self):
        """清除全部缓存（内存 + SQLite + pickle 文件）。"""
        self._memory.clear()
        # 删 pickle 文件
        for f in self._pickle_dir.glob("*.pkl"):
            try:
                f.unlink()
            except Exception:
                pass
        # 清 SQLite
        with self._connect() as conn:
            conn.execute("DELETE FROM file_cache")
        # VACUUM 需要在事务外单独执行
        with sqlite3.connect(str(self._db_path)) as conn:
            conn.execute("VACUUM")
        logger.info("缓存已全部清除")

    # ── 缓存目录管理 ──────────────────────────────────────────

    def set_cache_dir(self, path: str | Path):
        """运行时切换缓存目录。内部的 DB 和 pickle 会自动重建。"""
        self._cache_dir = Path(path)
        self._pickle_dir = self._cache_dir / "data"
        self._db_path = self._cache_dir / "index.db"
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._pickle_dir.mkdir(parents=True, exist_ok=True)
        self._init_db()
        logger.info(f"缓存目录已切换: {self._cache_dir}")

    @property
    def cache_dir(self) -> Path:
        return self._cache_dir

    # ── 内部方法 ──────────────────────────────────────────────

    def _put_memory(self, path: str, state: dict,
                    file_size: int, file_mtime: float):
        """写入内存 LRU 缓存。"""
        if path in self._memory:
            self._memory.move_to_end(path)
        else:
            if len(self._memory) >= self._max_memory:
                self._memory.popitem(last=False)
        self._memory[path] = {
            "state": state,
            "_file_size": file_size,
            "_file_mtime": file_mtime,
        }

    @staticmethod
    def _entry_to_meta(entry: dict) -> dict:
        """从内存条目提取元数据。"""
        state = entry["state"]
        test_cols = state.get("_test_header", [])
        meta_cols = state.get("_meta_header", [])
        df = state.get("_df")
        row_count = 0
        if df is not None:
            df_len = len(df)
            row_count = df_len - 3 if df_len > 3 else df_len
            if row_count < 0:
                row_count = 0
        fmt = state.get("_fmt", {})
        sig = fmt.get("sig", {}) if fmt else {}
        return {
            "file_size": entry.get("_file_size", 0),
            "file_mtime": entry.get("_file_mtime", 0),
            "signature_id": sig.get("format_id", ""),
            "test_columns": list(test_cols),
            "meta_columns": list(meta_cols),
            "row_count": row_count,
            "col_count": len(test_cols),
        }


# 模块级单例
ft_cache = FTCache()
