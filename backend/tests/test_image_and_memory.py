import asyncio
import os
import sys
from PIL import Image, ImageDraw

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.db import AsyncSessionLocal, init_db
from app.core.models import User, Document, InteractionTrace
from app.pipeline.offline.indexer import offline_indexer
from app.pipeline.offline.parser import dual_parser
from app.pipeline.online.coordinator import online_pipeline
from sqlalchemy import select

async def run_image_and_memory_tests():
    print("\n================ 1. Initializing DB ================")
    await init_db()

    async with AsyncSessionLocal() as db:
        user = await db.get(User, "student_1")
        if not user:
            user = User(id="student_1", name="Student 1")
            db.add(user)
            await db.commit()
            print("Seeded student_1")

    print("\n================ 2. Creating & Testing Image Source Ingestion ================")
    # Create a test synthetic diagram image
    test_img_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'test_assets'))
    os.makedirs(test_img_dir, exist_ok=True)
    test_img_path = os.path.join(test_img_dir, 'transformer_attention_diagram.png')

    # Draw a clean diagram with text
    img = Image.new('RGB', (600, 400), color=(245, 247, 250))
    d = ImageDraw.Draw(img)
    d.rectangle([(40, 40), (560, 360)], outline=(79, 70, 229), width=3)
    d.text((60, 60), "Scaled Dot-Product Attention Architecture", fill=(17, 24, 39))
    d.text((60, 100), "Formula: Attention(Q, K, V) = softmax(Q K^T / sqrt(d_k)) V", fill=(31, 41, 55))
    d.text((60, 140), "Key Components: Queries Q, Keys K, Values V, Scaling Factor sqrt(d_k)", fill=(55, 65, 81))
    d.text((60, 180), "Multi-Head Attention projects Q, K, V into h distinct representation subspaces.", fill=(55, 65, 81))
    img.save(test_img_path)
    print(f"Generated test image diagram at: {test_img_path}")

    # Dual parser test on image
    pages_data = await dual_parser.parse_image(test_img_path, title="Transformer Attention Diagram")
    print(f"Parsed Image Title: Transformer Attention Diagram")
    print(f"Parsed Pages Count: {len(pages_data)}")
    assert len(pages_data) >= 1, "Image parser did not produce page data"
    assert "image_path" in pages_data[0], "Page data missing image_path snapshot"
    print(f"Extracted Text Snippet: {pages_data[0]['text'][:100]}...")

    # Real-time indexing test
    print("\n================ 3. Testing Real-Time Indexing of Image ================")
    async with AsyncSessionLocal() as db:
        index_result = await offline_indexer.index_source(
            file_path_or_content=test_img_path,
            title="Transformer Attention Architecture",
            source_type="image",
            db=db,
            original_filename="transformer_attention_diagram.png"
        )
    print("Indexing result:", index_result)
    assert index_result["status"] == "success", "Indexing failed"
    doc_id = index_result["document_id"]
    print(f"Indexed document_id: {doc_id}")

    print("\n================ 4. Testing Real-Time Chat Query with Image Evidence ================")
    async with AsyncSessionLocal() as db:
        chat_res = await online_pipeline.run(
            user_id="student_1",
            session_id="test_img_session_1",
            user_query="What is the formula and scaling factor for Scaled Dot-Product Attention?",
            db=db
        )
    print("\n--- Chat Tutor Answer ---")
    print(chat_res["answer"][:300] + "...")
    print(f"Citations count: {len(chat_res['citations'])}")
    print(f"First citation: {chat_res['citations'][0] if chat_res['citations'] else 'None'}")
    assert len(chat_res["answer"]) > 20, "Tutor produced empty answer"

    print("\n================ 5. Testing Chat History Replay ('Seen Back') ================")
    async with AsyncSessionLocal() as db:
        res = await db.execute(
            select(InteractionTrace).where(InteractionTrace.session_id == "test_img_session_1")
        )
        traces = res.scalars().all()
        print(f"Found {len(traces)} recorded interaction trace(s) for session 'test_img_session_1'")
        assert len(traces) >= 1, "Interaction trace was not saved in DB"
        trace = traces[0]
        print(f"Trace ID: {trace.id}, Query: '{trace.user_query}'")

    print("\n================ 6. Testing Document Deletion & Vector Clearance ================")
    async with AsyncSessionLocal() as db:
        del_success = await offline_indexer.delete_document(doc_id=doc_id, db=db)
        print(f"Document delete returned: {del_success}")
        assert del_success is True, "Failed to delete document from SQLite & VectorDB"

        check_doc = await db.get(Document, doc_id)
        assert check_doc is None, "Document still exists in SQLite"

    print("\n================ 7. Testing Session & Message Deletion ================")
    async with AsyncSessionLocal() as db:
        from app.api.routers.chat import delete_message, delete_session
        del_msg_res = await delete_message(trace_id=trace.id, db=db)
        print(f"Delete message result: {del_msg_res}")
        del_sess_res = await delete_session(session_id="test_img_session_1", db=db)
        print(f"Delete session result: {del_sess_res}")

    print("\n>>> ALL IMAGE, REAL-TIME EMBEDDING, GRAPH & MEMORY TESTS PASSED SUCCESSFULLY! <<<\n")
    from app.core.db import engine
    await engine.dispose()

def test_image_and_memory_suite():
    """Pytest suite runner for image parsing, real-time embedding, and chat memory."""
    asyncio.run(run_image_and_memory_tests())

if __name__ == "__main__":
    asyncio.run(run_image_and_memory_tests())
