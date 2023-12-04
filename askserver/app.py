from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import argparse
import uvicorn

from askserver import knowledge_base, qa_collection


def create_app():
    app = FastAPI(
        title="AskServer",
        description="AskServer: A Knowledge Base Management System",
        version="0.1.0",
        docs_url="/",
        redoc_url=None,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(knowledge_base.router, prefix="/kb")
    app.include_router(qa_collection.router, prefix="/qa")
    return app


app = create_app()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="AskServer", description="External API for asksjtu project"
    )
    parser.add_argument("--host", type=str, default="0.0.0.0")
    parser.add_argument("--port", type=int, default=11621)
    args = parser.parse_args()
    # create and run app
    uvicorn.run(app, host=args.host, port=args.port)
