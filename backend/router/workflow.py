import aiofiles
import io
import logging
import os
from typing import Optional

from fastapi import APIRouter, HTTPException, status, Query
from fastapi.responses import StreamingResponse, Response

from middleware import CurrentUserDep
from schemas import ErrorResponse
from rag_system import RAGWorkflow 

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Workflow"])


@router.get(
    "/workflow/visualize",
    response_class=Response,
    responses={
        200: {
            "content": {"image/png": {}},
            "description": "Workflow visualization PNG image",
        },
        400: {"model": ErrorResponse, "description": "Visualization failed"},
        401: {"model": ErrorResponse, "description": "Not authenticated"},
    },
    summary="Visualize workflow graph",
    description="Generate and download a PNG visualization of the RAG workflow graph.",
)
async def visualize_workflow(
    current_user: CurrentUserDep,
    format: str = Query(default="png", pattern="^(png|mermaid)$",
                        description="Output format: png or mermaid"),
) -> Response:
    """
    Generate a visualization of the RAG workflow graph.

    - **format**: Output format (png or mermaid)

    Returns a PNG image or Mermaid diagram of the workflow structure.
    """
    try:
        graph = RAGWorkflow(
            session_id="visualization",
            collection_name="visualization",
        )

        from langgraph.checkpoint.memory import MemorySaver
        checkpointer = MemorySaver()
        compiled_graph = graph.graph.compile(checkpointer=checkpointer)

        if format == "mermaid":
            try:
                mermaid_diagram = compiled_graph.get_graph().draw_mermaid()
                return Response(
                    content=mermaid_diagram,
                    media_type="text/plain",
                    headers={
                        "Content-Disposition": "attachment; filename=workflow.mmd"
                    }
                )
            except Exception as e:
                logger.error(f"Failed to generate Mermaid diagram: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to generate Mermaid diagram: {str(e)}"
                )

        else:  
            try:
                mermaid_diagram = compiled_graph.get_graph().draw_mermaid()

                try:
                    from PIL import Image, ImageDraw, ImageFont
                    import subprocess
                    import tempfile

                    with tempfile.NamedTemporaryFile(mode='w', suffix='.mmd', delete=False) as f:
                        f.write(mermaid_diagram)
                        mmd_file = f.name

                    png_file = mmd_file.replace('.mmd', '.png')
                    try:
                        result = subprocess.run(
                            ['mmdc', '-i', mmd_file, '-o',
                                png_file, '-b', 'transparent'],
                            capture_output=True,
                            timeout=10
                        )

                        if result.returncode == 0 and os.path.exists(png_file):
                            async with aiofiles.open(png_file, 'rb') as f:
                                png_data = await f.read()

                            os.unlink(mmd_file)
                            os.unlink(png_file)

                            return Response(
                                content=png_data,
                                media_type="image/png",
                                headers={
                                    "Content-Disposition": "attachment; filename=workflow.png"
                                }
                            )
                    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.CalledProcessError):
                        pass

                    try:
                        png_bytes = compiled_graph.get_graph().draw_mermaid_png()
                        return Response(
                            content=png_bytes,
                            media_type="image/png",
                            headers={
                                "Content-Disposition": "attachment; filename=workflow.png"
                            }
                        )
                    except Exception:
                        pass

                    img = Image.new('RGB', (1200, 1600), color='white')
                    draw = ImageDraw.Draw(img)

                    try:
                        font = ImageFont.truetype("arial.ttf", 12)
                    except:
                        font = ImageFont.load_default()

                    y_position = 20
                    for line in mermaid_diagram.split('\n'):
                        draw.text((20, y_position), line,
                                  fill='black', font=font)
                        y_position += 20

                    draw.text((20, y_position + 20),
                              "Note: Install mermaid-cli (npm install -g @mermaid-js/mermaid-cli) for better visualization",
                              fill='red', font=font)

                    img_byte_arr = io.BytesIO()
                    img.save(img_byte_arr, format='PNG')
                    img_byte_arr.seek(0)

                    try:
                        os.unlink(mmd_file)
                    except:
                        pass

                    return Response(
                        content=img_byte_arr.getvalue(),
                        media_type="image/png",
                        headers={
                            "Content-Disposition": "attachment; filename=workflow.png"
                        }
                    )

                except ImportError:
                    logger.warning(
                        "PIL not available for PNG generation, returning Mermaid diagram")
                    return Response(
                        content=mermaid_diagram,
                        media_type="text/plain",
                        headers={
                            "Content-Disposition": "attachment; filename=workflow.mmd",
                            "X-Fallback": "true"
                        }
                    )

            except Exception as e:
                logger.error(f"Failed to generate PNG: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to generate visualization: {str(e)}. Try format=mermaid instead."
                )

    except Exception as e:
        logger.error(f"Workflow visualization error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to visualize workflow: {str(e)}"
        )


@router.get(
    "/workflow/structure",
    responses={
        200: {"description": "Workflow structure information"},
        401: {"model": ErrorResponse, "description": "Not authenticated"},
    },
    summary="Get workflow structure",
    description="Get the workflow structure as JSON.",
)
async def get_workflow_structure(
    current_user: CurrentUserDep,
):
    """
    Get the RAG workflow structure information.

    Returns metadata about nodes, edges, and the overall graph structure.
    """
    try:
        graph = RAGWorkflow(
            session_id="structure",
            collection_name="structure",
        )

        from langgraph.checkpoint.memory import MemorySaver
        checkpointer = MemorySaver()
        compiled_graph = graph.graph.compile(checkpointer=checkpointer)

        graph_structure = compiled_graph.get_graph()

        nodes = list(graph_structure.nodes.keys())
        edges = [
            {
                "source": edge.source,
                "target": edge.target,
            }
            for edge in graph_structure.edges
        ]

        return {
            "nodes": nodes,
            "edges": edges,
            "entry_point": graph_structure.entry_point if hasattr(graph_structure, 'entry_point') else None,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "description": "Production-ready LangGraph-based agentic RAG workflow",
        }

    except Exception as e:
        logger.error(
            f"Failed to get workflow structure: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get workflow structure: {str(e)}"
        )
