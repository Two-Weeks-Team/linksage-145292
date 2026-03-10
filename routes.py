from fastapi import APIRouter, HTTPException, Depends, Body
from pydantic import BaseModel, Field
from typing import List, Optional
from sqlalchemy.orm import Session
from models import SessionLocal, Bookmark, Tag, User, Favorite, Base
from ai_service import call_inference
import datetime

router = APIRouter()

# Dependency to get a DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------- Pydantic Schemas ----------
class SummarizeRequest(BaseModel):
    url: str = Field(..., description="URL to summarize")

class SummarizeResponse(BaseModel):
    summary: str

class TagsRequest(BaseModel):
    url: str = Field(..., description="URL to generate tags for")

class TagsResponse(BaseModel):
    tags: List[str]

class BookmarkCreate(BaseModel):
    url: str = Field(..., description="Link to save")
    title: Optional[str] = None
    summary: Optional[str] = None
    tags: Optional[List[str]] = None
    favorite: bool = False

class BookmarkResponse(BaseModel):
    id: int
    url: str
    title: Optional[str]
    summary: Optional[str]
    tags: List[str]
    favorite: bool
    saved_at: datetime.datetime

# ---------- Helper Functions ----------
def _ensure_tags(db: Session, tag_names: List[str]):
    tag_objs = []
    for name in tag_names:
        name = name.strip().lower()
        if not name:
            continue
        tag = db.query(Tag).filter(Tag.name == name).first()
        if not tag:
            tag = Tag(name=name)
            db.add(tag)
            db.flush()  # assign id
        tag_objs.append(tag)
    return tag_objs

# ---------- AI Endpoints ----------
@router.post("/summarize", response_model=SummarizeResponse)
async def summarize(req: SummarizeRequest):
    messages = [{"role": "user", "content": f"Summarize the main points of the web page at {req.url} in less than 150 words."}]
    result = await call_inference(messages)
    summary = result.get("summary") or result.get("note") or "Summary not available."
    return SummarizeResponse(summary=summary)

@router.post("/generate-tags", response_model=TagsResponse)
async def generate_tags(req: TagsRequest):
    messages = [{"role": "user", "content": f"Provide a short, comma‑separated list of relevant tags for the content at {req.url}. Return only a JSON array of strings."}]
    result = await call_inference(messages)
    tags = result.get("tags")
    if isinstance(tags, str):
        # try to split if a plain string was returned
        tags = [t.strip() for t in tags.split(',') if t.strip()]
    elif not isinstance(tags, list):
        tags = []
    return TagsResponse(tags=tags)

# ---------- Bookmark CRUD ----------
@router.post("/bookmarks", response_model=BookmarkResponse)
async def create_bookmark(payload: BookmarkCreate, db: Session = Depends(get_db)):
    # For demo purposes we assume a single default user (id=1). In real app, use auth.
    user = db.query(User).filter(User.id == 1).first()
    if not user:
        # create a placeholder user
        user = User(email="demo@example.com", password_hash="not_used")
        db.add(user)
        db.flush()

    summary = payload.summary
    tags = payload.tags or []

    # Call AI services if missing
    if not summary:
        summarize_msg = [{"role": "user", "content": f"Summarize the page at {payload.url} in 150 words or less."}]
        ai_res = await call_inference(summarize_msg)
        summary = ai_res.get("summary") or ""
    if not tags:
        tag_msg = [{"role": "user", "content": f"Return a JSON array of 3‑5 short tags for the page at {payload.url}."}]
        ai_res = await call_inference(tag_msg)
        tags = ai_res.get("tags") or []
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(',') if t.strip()]

    bookmark = Bookmark(
        user_id=user.id,
        url=payload.url,
        title=payload.title,
        summary=summary,
        favorite=payload.favorite,
    )
    db.add(bookmark)
    db.flush()  # assign bookmark.id
    # Attach tags
    tag_objs = _ensure_tags(db, tags)
    bookmark.tags = tag_objs
    db.commit()
    db.refresh(bookmark)
    return BookmarkResponse(
        id=bookmark.id,
        url=bookmark.url,
        title=bookmark.title,
        summary=bookmark.summary,
        tags=[t.name for t in bookmark.tags],
        favorite=bookmark.favorite,
        saved_at=bookmark.saved_at,
    )

@router.get("/bookmarks", response_model=List[BookmarkResponse])
def list_bookmarks(db: Session = Depends(get_db)):
    # Demo: return all bookmarks for the placeholder user id=1
    bookmarks = db.query(Bookmark).filter(Bookmark.user_id == 1, Bookmark.deleted_at.is_(None)).all()
    return [
        BookmarkResponse(
            id=b.id,
            url=b.url,
            title=b.title,
            summary=b.summary,
            tags=[t.name for t in b.tags],
            favorite=b.favorite,
            saved_at=b.saved_at,
        )
        for b in bookmarks
    ]

@router.get("/bookmarks/{bookmark_id}", response_model=BookmarkResponse)
def get_bookmark(bookmark_id: int, db: Session = Depends(get_db)):
    bm = db.query(Bookmark).filter(Bookmark.id == bookmark_id, Bookmark.deleted_at.is_(None)).first()
    if not bm:
        raise HTTPException(status_code=404, detail="Bookmark not found")
    return BookmarkResponse(
        id=bm.id,
        url=bm.url,
        title=bm.title,
        summary=bm.summary,
        tags=[t.name for t in bm.tags],
        favorite=bm.favorite,
        saved_at=bm.saved_at,
    )

@router.post("/favorites")
def add_favorite(link_id: int = Body(..., embed=True), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == 1).first()
    bookmark = db.query(Bookmark).filter(Bookmark.id == link_id).first()
    if not bookmark:
        raise HTTPException(status_code=404, detail="Bookmark not found")
    fav = db.query(Favorite).filter(Favorite.user_id == user.id, Favorite.bookmark_id == link_id).first()
    if fav:
        return {"status": "already_favorite"}
    fav = Favorite(user_id=user.id, bookmark_id=link_id)
    db.add(fav)
    bookmark.favorite = True
    db.commit()
    return {"status": "success"}

@router.delete("/favorites/{link_id}")
def remove_favorite(link_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == 1).first()
    fav = db.query(Favorite).filter(Favorite.user_id == user.id, Favorite.bookmark_id == link_id).first()
    if not fav:
        raise HTTPException(status_code=404, detail="Favorite not found")
    db.delete(fav)
    bookmark = db.query(Bookmark).filter(Bookmark.id == link_id).first()
    if bookmark:
        bookmark.favorite = False
    db.commit()
    return {"status": "success"}
