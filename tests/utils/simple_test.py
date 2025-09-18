#!/usr/bin/env python3
"""
简化测试脚本
不依赖pytest，直接测试核心功能
"""

import sys
import os
import asyncio
import tempfile
import sqlite3
from datetime import datetime
import uuid

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

async def test_basic_imports():
    """测试基本导入"""
    print("🔍 测试基本导入...")
    try:
        from app.models import oc8r
        from app.infra.repositories import TtsJobRepository, VoiceRepository, UploadRepository
        from app.infra.queue import get_queue_manager
        from app.domain.strategies.tts_strategy import TtsStrategyFactory
        print("✅ 基本导入成功")
        return True
    except Exception as e:
        print(f"❌ 导入失败: {str(e)}")
        return False

async def test_database_operations():
    """测试数据库操作"""
    print("🗄️ 测试数据库操作...")
    try:
        from app.infra.repositories import UploadRepository, VoiceRepository, TtsJobRepository
        from app.models import oc8r
        
        # 创建临时数据库
        temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_db.close()
        
        conn = sqlite3.connect(temp_db.name, check_same_thread=False)
        
        # 测试Repository
        upload_repo = UploadRepository(conn)
        voice_repo = VoiceRepository(conn)
        job_repo = TtsJobRepository(conn)
        
        # 创建测试数据
        upload = oc8r.Upload(
            id=str(uuid.uuid4()),
            fileName="test.wav",
            contentType="audio/wav",
            sizeBytes=1024,
            durationSeconds=1.5,
            createdAt=datetime.now().isoformat()
        )
        upload_repo.add(upload)
        
        voice = oc8r.Voice(
            id=str(uuid.uuid4()),
            name="Test Voice",
            description="Test voice",
            uploadId=upload.id,
            createdAt=datetime.now().isoformat(),
            updatedAt=datetime.now().isoformat()
        )
        voice_repo.add(voice)
        
        job = oc8r.TtsJob(
            id=str(uuid.uuid4()),
            type=oc8r.Type.tts,
            status=oc8r.JobStatus.queued,
            createdAt=datetime.now().isoformat(),
            updatedAt=datetime.now().isoformat(),
            request=oc8r.CreateTtsJobRequest(
                text="Hello world",
                mode=oc8r.TtsMode.speaker,
                voiceId=voice.id
            ),
            result=None,
            error=None
        )
        job_repo.add(job)
        
        # 验证数据
        retrieved_upload = upload_repo.get(upload.id)
        retrieved_voice = voice_repo.get(voice.id)
        retrieved_job = job_repo.get(job.id)
        
        assert retrieved_upload is not None
        assert retrieved_voice is not None
        assert retrieved_job is not None
        
        conn.close()
        os.unlink(temp_db.name)
        
        print("✅ 数据库操作成功")
        return True
    except Exception as e:
        print(f"❌ 数据库操作失败: {str(e)}")
        return False

async def test_queue_operations():
    """测试队列操作"""
    print("🔄 测试队列操作...")
    try:
        from app.infra.queue import get_queue_manager
        
        qm = get_queue_manager()
        
        # 测试入队
        task_id = await qm.enqueue({"test": "data"})
        assert task_id is not None
        
        # 测试状态查询
        status = qm.status(task_id)
        assert status is not None
        
        print("✅ 队列操作成功")
        return True
    except Exception as e:
        print(f"❌ 队列操作失败: {str(e)}")
        return False

async def test_strategy_creation():
    """测试策略创建"""
    print("🎯 测试策略创建...")
    try:
        from app.domain.strategies.tts_strategy import TtsStrategyFactory
        from app.infra.indextts_client import IndexTtsClient
        from app.models import oc8r
        
        client = IndexTtsClient()
        
        # 测试创建策略
        strategy = TtsStrategyFactory.create_strategy(oc8r.TtsMode.speaker, client)
        assert strategy is not None
        
        await client.close()
        
        print("✅ 策略创建成功")
        return True
    except Exception as e:
        print(f"❌ 策略创建失败: {str(e)}")
        return False

async def test_model_creation():
    """测试模型创建"""
    print("📦 测试模型创建...")
    try:
        from app.models import oc8r
        
        # 测试创建各种模型
        upload = oc8r.Upload(
            id=str(uuid.uuid4()),
            fileName="test.wav",
            contentType="audio/wav",
            sizeBytes=1024,
            durationSeconds=1.5,
            createdAt=datetime.now().isoformat()
        )
        
        voice = oc8r.Voice(
            id=str(uuid.uuid4()),
            name="Test Voice",
            description="Test voice",
            uploadId=upload.id,
            createdAt=datetime.now().isoformat(),
            updatedAt=datetime.now().isoformat()
        )
        
        job_request = oc8r.CreateTtsJobRequest(
            text="Hello world",
            mode=oc8r.TtsMode.speaker,
            voiceId=voice.id
        )
        
        job = oc8r.TtsJob(
            id=str(uuid.uuid4()),
            type=oc8r.Type.tts,
            status=oc8r.JobStatus.queued,
            createdAt=datetime.now().isoformat(),
            updatedAt=datetime.now().isoformat(),
            request=job_request,
            result=None,
            error=None
        )
        
        # 验证模型
        assert upload.id is not None
        assert voice.id is not None
        assert job.id is not None
        
        print("✅ 模型创建成功")
        return True
    except Exception as e:
        print(f"❌ 模型创建失败: {str(e)}")
        return False

async def run_all_tests():
    """运行所有测试"""
    print("🧪 开始运行简化测试套件...\n")
    
    tests = [
        ("基本导入", test_basic_imports),
        ("数据库操作", test_database_operations),
        ("队列操作", test_queue_operations),
        ("策略创建", test_strategy_creation),
        ("模型创建", test_model_creation),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"🔍 运行测试: {test_name}")
        try:
            success = await test_func()
            if success:
                passed += 1
                print(f"✅ {test_name} 通过\n")
            else:
                print(f"❌ {test_name} 失败\n")
        except Exception as e:
            print(f"❌ {test_name} 异常: {str(e)}\n")
    
    print(f"📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！")
        return True
    else:
        print(f"❌ 有 {total - passed} 个测试失败")
        return False

if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
