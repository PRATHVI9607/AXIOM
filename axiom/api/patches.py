"""Patch endpoints (PRD §8.3) — generate, list, accept, reject patches."""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from axiom.core.database import get_db
from axiom.core.security import CurrentUser, get_current_user
from axiom.models.api_models import PatchOut
from axiom.models.db_models import Patch
from axiom.services.patch_service import get_patch_generator

router = APIRouter(prefix="/patches", tags=["patches"])


@router.post("/{project_id}/generate", response_model=list[PatchOut])
async def generate_patches(
    project_id: str,
    file_path: str,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[PatchOut]:
    """Detect risk patterns in a file and persist verified patch candidates."""
    try:
        code = Path(file_path).read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Cannot read file: {exc}") from exc

    candidates = get_patch_generator().generate(code)
    out: list[PatchOut] = []
    for c in candidates:
        patch = Patch(
            project_id=project_id,
            pattern=c.pattern,
            original_code=c.original,
            patched_code=c.patched,
            confidence=c.confidence,
            verified=c.verified,
            test_results=c.test_results,
        )
        db.add(patch)
        await db.flush()
        out.append(
            PatchOut(
                patch_id=patch.id,
                function_id=patch.function_id,
                pattern=c.pattern,
                confidence=c.confidence,
                original=c.original,
                patched=c.patched,
                verified=c.verified,
                test_results=c.test_results or {},
            )
        )
    return out


@router.get("/{project_id}", response_model=list[PatchOut])
async def list_patches(
    project_id: str,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[PatchOut]:
    result = await db.execute(select(Patch).where(Patch.project_id == project_id))
    return [_to_out(p) for p in result.scalars().all()]


@router.get("/{project_id}/{patch_id}", response_model=PatchOut)
async def get_patch(
    project_id: str,
    patch_id: str,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PatchOut:
    patch = await db.get(Patch, patch_id)
    if patch is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Patch not found")
    return _to_out(patch)


@router.post("/{project_id}/{patch_id}/accept", response_model=PatchOut)
async def accept_patch(
    project_id: str,
    patch_id: str,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PatchOut:
    patch = await db.get(Patch, patch_id)
    if patch is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Patch not found")
    patch.status = "accepted"
    await db.flush()
    return _to_out(patch)


@router.post("/{project_id}/{patch_id}/reject", response_model=PatchOut)
async def reject_patch(
    project_id: str,
    patch_id: str,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PatchOut:
    patch = await db.get(Patch, patch_id)
    if patch is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Patch not found")
    patch.status = "rejected"
    await db.flush()
    return _to_out(patch)


def _to_out(patch: Patch) -> PatchOut:
    return PatchOut(
        patch_id=patch.id,
        function_id=patch.function_id,
        pattern=patch.pattern,
        confidence=patch.confidence,
        original=patch.original_code,
        patched=patch.patched_code,
        verified=patch.verified,
        test_results=patch.test_results or {},
    )
