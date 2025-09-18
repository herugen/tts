"""
文件级注释：
本模块实现 UploadRepository 和 VoiceRepository，负责 Upload 与 Voice 领域对象的持久化操作，属于基础设施层（Infrastructure Layer）。
采用 sqlite3 作为底层数据库，字段设计严格对齐 app.models.oc8r.Upload 与 app.models.oc8r.Voice。
每个仓库均提供基础的增删查改（CRUD）接口，便于应用层调用。

架构说明：
- 每个 Repository 只负责单一领域对象的持久化，保持高内聚低耦合。
- 通过依赖注入方式传递数据库连接，便于测试与扩展。
- 所有 SQL 语句均采用参数化，防止 SQL 注入。
- 不直接暴露 sqlite3 细节，接口以领域模型为主。

依赖说明：
- 依赖 app.models.oc8r.Upload, app.models.oc8r.Voice 作为数据模型。
- 依赖 sqlite3 作为数据库驱动。

注意事项：
- 领域层与基础设施层解耦，Repository 只做数据持久化，不包含业务逻辑。
- 字段类型、命名与 oc8r.Upload/Voice 保持一致。
"""

import sqlite3
import json
from typing import Optional, List
from app.models.oc8r import Upload, Voice
from app.models import oc8r

class UploadRepository:
    """
    UploadRepository
    ----------------
    负责 Upload 领域对象的持久化操作，提供增删查改接口。
    字段对齐 oc8r.Upload: id, fileName, contentType, sizeBytes, durationSeconds, createdAt
    """

    def __init__(self, conn: sqlite3.Connection):
        """
        初始化仓库，传入 sqlite3.Connection
        """
        self.conn = conn
        self._ensure_table()

    def _ensure_table(self):
        """
        确保 upload 表存在，若不存在则创建
        """
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS uploads (
            id TEXT PRIMARY KEY,
            fileName TEXT NOT NULL,
            contentType TEXT NOT NULL,
            sizeBytes INTEGER NOT NULL,
            durationSeconds REAL,
            createdAt TEXT NOT NULL
        )
        """)
        self.conn.commit()

    def add(self, upload: Upload):
        """
        新增 Upload 记录
        """
        self.conn.execute(
            "INSERT INTO uploads (id, fileName, contentType, sizeBytes, durationSeconds, createdAt) VALUES (?, ?, ?, ?, ?, ?)",
            (upload.id, upload.fileName, upload.contentType, upload.sizeBytes, upload.durationSeconds, upload.createdAt)
        )
        self.conn.commit()

    def get(self, upload_id: str) -> Optional[Upload]:
        """
        根据 id 查询 Upload
        """
        cur = self.conn.execute(
            "SELECT id, fileName, contentType, sizeBytes, durationSeconds, createdAt FROM uploads WHERE id = ?",
            (upload_id,)
        )
        row = cur.fetchone()
        if row:
            return Upload(
                id=row[0],
                fileName=row[1],
                contentType=row[2],
                sizeBytes=row[3],
                durationSeconds=row[4],
                createdAt=row[5]
            )
        return None

    def list(self, limit: int = 100, offset: int = 0) -> List[Upload]:
        """
        列表查询 Upload，支持分页
        """
        cur = self.conn.execute(
            "SELECT id, fileName, contentType, sizeBytes, durationSeconds, createdAt FROM uploads ORDER BY createdAt DESC LIMIT ? OFFSET ?",
            (limit, offset)
        )
        return [
            Upload(
                id=row[0],
                fileName=row[1],
                contentType=row[2],
                sizeBytes=row[3],
                durationSeconds=row[4],
                createdAt=row[5]
            )
            for row in cur.fetchall()
        ]

    def delete(self, upload_id: str):
        """
        删除指定 id 的 Upload
        """
        self.conn.execute(
            "DELETE FROM uploads WHERE id = ?",
            (upload_id,)
        )
        self.conn.commit()


class VoiceRepository:
    """
    VoiceRepository
    ---------------
    负责 Voice 领域对象的持久化操作，提供增删查改接口。
    字段对齐 oc8r.Voice: id, name, description, uploadId, createdAt, updatedAt
    """

    def __init__(self, conn: sqlite3.Connection):
        """
        初始化仓库，传入 sqlite3.Connection
        """
        self.conn = conn
        self._ensure_table()

    def _ensure_table(self):
        """
        确保 voice 表存在，若不存在则创建
        """
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS voices (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            uploadId TEXT NOT NULL,
            createdAt TEXT NOT NULL,
            updatedAt TEXT NOT NULL
        )
        """)
        self.conn.commit()

    def add(self, voice: Voice):
        """
        新增 Voice 记录
        """
        self.conn.execute(
            "INSERT INTO voices (id, name, description, uploadId, createdAt, updatedAt) VALUES (?, ?, ?, ?, ?, ?)",
            (voice.id, voice.name, voice.description, voice.uploadId, voice.createdAt, voice.updatedAt)
        )
        self.conn.commit()

    def get(self, voice_id: str) -> Optional[Voice]:
        """
        根据 id 查询 Voice
        """
        cur = self.conn.execute(
            "SELECT id, name, description, uploadId, createdAt, updatedAt FROM voices WHERE id = ?",
            (voice_id,)
        )
        row = cur.fetchone()
        if row:
            return Voice(
                id=row[0],
                name=row[1],
                description=row[2],
                uploadId=row[3],
                createdAt=row[4],
                updatedAt=row[5]
            )
        return None

    def list(self, limit: int = 100, offset: int = 0) -> List[Voice]:
        """
        列表查询 Voice，支持分页
        """
        cur = self.conn.execute(
            "SELECT id, name, description, uploadId, createdAt, updatedAt FROM voices ORDER BY createdAt DESC LIMIT ? OFFSET ?",
            (limit, offset)
        )
        return [
            Voice(
                id=row[0],
                name=row[1],
                description=row[2],
                uploadId=row[3],
                createdAt=row[4],
                updatedAt=row[5]
            )
            for row in cur.fetchall()
        ]

    def delete(self, voice_id: str):
        """
        删除指定 id 的 Voice
        """
        self.conn.execute(
            "DELETE FROM voices WHERE id = ?",
            (voice_id,)
        )
        self.conn.commit()


class TtsJobRepository:
    """
    TtsJobRepository
    ---------------
    负责 TtsJob 领域对象的持久化操作，提供增删查改接口。
    字段对齐 oc8r.TtsJob: id, type, status, createdAt, updatedAt, request, result, error
    """

    def __init__(self, conn: sqlite3.Connection):
        """
        初始化仓库，传入 sqlite3.Connection
        """
        self.conn = conn
        self._ensure_table()

    def _ensure_table(self):
        """
        确保 tts_job 表存在，若不存在则创建
        """
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS tts_jobs (
            id TEXT PRIMARY KEY,
            type TEXT NOT NULL,
            status TEXT NOT NULL,
            createdAt TEXT NOT NULL,
            updatedAt TEXT NOT NULL,
            request TEXT NOT NULL,
            result TEXT,
            error TEXT
        )
        """)
        self.conn.commit()

    def add(self, tts_job: oc8r.TtsJob):
        """
        新增 TtsJob 记录
        """
        # 序列化复杂对象为JSON字符串，处理枚举类型和AnyUrl类型
        request_data = None
        if tts_job.request:
            request_data = tts_job.request.model_dump(mode='json')
        request_json = json.dumps(request_data)
        
        result_data = None
        if tts_job.result:
            result_data = tts_job.result.model_dump(mode='json')
        result_json = json.dumps(result_data)
        
        error_json = json.dumps(tts_job.error.model_dump(mode='json') if tts_job.error else None)
        
        # 处理枚举类型
        type_str = tts_job.type.value if hasattr(tts_job.type, 'value') else str(tts_job.type)
        status_str = tts_job.status.value if hasattr(tts_job.status, 'value') else str(tts_job.status)
        
        self.conn.execute(
            "INSERT INTO tts_jobs (id, type, status, createdAt, updatedAt, request, result, error) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (tts_job.id, type_str, status_str, tts_job.createdAt, tts_job.updatedAt, request_json, result_json, error_json)
        )
        self.conn.commit()

    def get(self, tts_job_id: str) -> Optional[oc8r.TtsJob]:
        """
        根据 id 查询 TtsJob
        """
        cur = self.conn.execute(
            "SELECT id, type, status, createdAt, updatedAt, request, result, error FROM tts_jobs WHERE id = ?",
            (tts_job_id,)
        )
        row = cur.fetchone()
        if row:
            # 反序列化JSON字段
            request = None
            if row[5]:
                req_data = json.loads(row[5])
                if req_data:  # 确保不是None
                    request = oc8r.CreateTtsJobRequest(**req_data)
            
            result = None
            if row[6]:
                res_data = json.loads(row[6])
                if res_data:  # 确保不是None
                    result = oc8r.Result(**res_data)
            
            error = None
            if row[7]:
                err_data = json.loads(row[7])
                if err_data:  # 确保不是None
                    error = oc8r.ErrorResponse(**err_data)
            
            return oc8r.TtsJob(
                id=row[0],
                type=oc8r.Type(row[1]),
                status=oc8r.JobStatus(row[2]),
                createdAt=row[3],
                updatedAt=row[4],
                request=request,
                result=result,
                error=error
            )
        return None

    def list(self, status: Optional[str] = None, limit: int = 100, offset: int = 0) -> List[oc8r.TtsJob]:
        """
        列表查询 TtsJob，支持分页和状态过滤
        """
        if status:
            cur = self.conn.execute(
                "SELECT id, type, status, createdAt, updatedAt, request, result, error FROM tts_jobs WHERE status = ? ORDER BY createdAt DESC LIMIT ? OFFSET ?",
                (status, limit, offset)
            )
        else:
            cur = self.conn.execute(
                "SELECT id, type, status, createdAt, updatedAt, request, result, error FROM tts_jobs ORDER BY createdAt DESC LIMIT ? OFFSET ?",
                (limit, offset)
            )
        items: List[oc8r.TtsJob] = []
        for row in cur.fetchall():
            # 反序列化JSON字段
            request = None
            if row[5]:
                req_data = json.loads(row[5])
                if req_data:  # 确保不是None
                    request = oc8r.CreateTtsJobRequest(**req_data)
            
            result = None
            if row[6]:
                res_data = json.loads(row[6])
                if res_data:  # 确保不是None
                    result = oc8r.Result(**res_data)
            
            error = None
            if row[7]:
                err_data = json.loads(row[7])
                if err_data:  # 确保不是None
                    error = oc8r.ErrorResponse(**err_data)
            
            items.append(
                oc8r.TtsJob(
                    id=row[0],
                    type=oc8r.Type(row[1]),
                    status=oc8r.JobStatus(row[2]),
                    createdAt=row[3],
                    updatedAt=row[4],
                    request=request,
                    result=result,
                    error=error
                )
            )
        return items

    def delete(self, tts_job_id: str):
        """
        删除指定 id 的 TtsJob
        """
        self.conn.execute(
            "DELETE FROM tts_jobs WHERE id = ?",
            (tts_job_id,)
        )
        self.conn.commit()

    def update(self,
               tts_job_id: str,
               *,
               status: Optional[oc8r.JobStatus] = None,
               result: Optional[oc8r.Result] = None,
               error: Optional[oc8r.ErrorResponse] = None,
               updatedAt: Optional[str] = None) -> None:
        """
        部分更新 TtsJob 的字段（status/result/error/updatedAt）。
        未提供的字段保持不变。
        """
        # 先读取当前记录
        current = self.get(tts_job_id)
        if current is None:
            return
        new_status = status or current.status
        new_result = result if result is not None else current.result
        new_error = error if error is not None else current.error
        new_updated_at = updatedAt or current.updatedAt

        status_str = new_status.value if hasattr(new_status, 'value') else str(new_status)
        result_json = json.dumps(new_result.model_dump(mode='json') if new_result is not None else None)
        error_json = json.dumps(new_error.model_dump(mode='json') if new_error is not None else None)

        self.conn.execute(
            "UPDATE tts_jobs SET status = ?, result = ?, error = ?, updatedAt = ? WHERE id = ?",
            (status_str, result_json, error_json, new_updated_at, tts_job_id)
        )
        self.conn.commit()

